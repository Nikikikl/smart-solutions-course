#include "build_mode.h"
#if !BENCH_MODE
#include <Arduino.h>
#include <ArduinoJson.h>
#include <DNSServer.h>
#include <M5Unified.h>
#include <Preferences.h>
#include <WebServer.h>
#include <WiFi.h>
#include <esp_system.h>
#include <time.h>

#include "persistent_state.h"
#include "display_image_job.h"
#include "display_image_renderer.h"
#include "post_office_ca.h"
#include "post_office_client.h"
#include "post_office_model.h"
#include "post_office_settings.h"
#include "pressure_model.h"
#include "pressure_settings.h"
#include "station_bridge.h"
#include "web_page.h"

namespace {

constexpr uint16_t kDnsPort = 53;
constexpr char kSetupSsid[] = "Lab2AtomSetup";
constexpr int kPressureAdcPin = 5;  // AtomS3(R) G5; verify DA2 wiring in lab.
constexpr int kPressureSampleCount = 8;

WebServer webServer(80);
DNSServer dnsServer;
Preferences wifiPreferences;
postoffice::SettingsStore settingsStore;
postoffice::PersistentState persistentState;
postoffice::StationBridge stationBridge;
postoffice::PostOfficeClient postOfficeClient;
postoffice::DisplayImageJob displayImageJob;
postoffice::Settings settings;
pressure::SettingsStore pressureSettingsStore;
pressure::Calibration pressureCalibration;
bool pressureSensorConfirmed = false;  // RAM only; local confirmation expires at reboot.
String serialLine;
bool accessPointActive = false;
bool wifiRecoveryActive = false;
bool stationAttemptActive = false;
uint32_t stationAttemptStartedMs = 0;
uint32_t nextStationRetryAtMs = 0;

void logLine(const String& message) {
  // Never pass Wi-Fi passwords or the Atom API key to this function.
  Serial.println("# " + message);
}

void handleWifiEvent(arduino_event_id_t event, arduino_event_info_t info) {
  switch (event) {
    case ARDUINO_EVENT_WIFI_STA_START:
      logLine("Wi-Fi event: STA start");
      break;
    case ARDUINO_EVENT_WIFI_STA_CONNECTED:
      logLine("Wi-Fi event: STA associated");
      break;
    case ARDUINO_EVENT_WIFI_STA_GOT_IP:
      logLine("Wi-Fi event: STA got IP " + WiFi.localIP().toString());
      break;
    case ARDUINO_EVENT_WIFI_STA_DISCONNECTED: {
      const uint8_t reason = info.wifi_sta_disconnected.reason;
      const char* reasonName =
          WiFi.disconnectReasonName(static_cast<wifi_err_reason_t>(reason));
      logLine("Wi-Fi event: STA disconnected; reason=" + String(reason) +
              (reasonName[0] == '\0' ? "" : " (" + String(reasonName) + ")"));
      break;
    }
    default:
      break;
  }
}

String jsonString(const String& value) {
  JsonDocument document;
  document.set(value);
  String output;
  serializeJson(document, output);
  return output;
}

String deviceId() {
  const uint64_t mac = ESP.getEfuseMac();
  char value[32];
  snprintf(value, sizeof(value), "atom-%04lx%08lx", (unsigned long)(mac >> 32),
           (unsigned long)mac);
  return String(value);
}

void showStatus(const String& heading, const String& detail) {
  localdisplay::showStatus(heading.c_str(), detail.c_str());
}

void startSetupAccessPoint(bool enableRecovery) {
  WiFi.disconnect(false, false);  // keep saved credentials for the next reboot
  WiFi.mode(enableRecovery ? WIFI_AP_STA : WIFI_AP);
  WiFi.softAP(kSetupSsid);  // local setup AP; no production credential in source
  dnsServer.start(kDnsPort, "*", WiFi.softAPIP());
  accessPointActive = true;
  wifiRecoveryActive = enableRecovery;
  stationAttemptActive = false;
  nextStationRetryAtMs = millis() + postoffice::kWifiStaRetryIntervalMs;
  logLine("Wi-Fi setup AP active");
  showStatus("Setup AP", WiFi.softAPIP().toString());
}

void startStoredStationAttempt(bool keepSetupAccessPoint) {
  const String ssid = wifiPreferences.getString("ssid", "");
  if (ssid.isEmpty()) {
    startSetupAccessPoint(false);
    return;
  }
  WiFi.mode(keepSetupAccessPoint ? WIFI_AP_STA : WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(ssid.c_str(), wifiPreferences.getString("pass", "").c_str());
  stationAttemptActive = true;
  stationAttemptStartedMs = millis();
  logLine(keepSetupAccessPoint ? "Wi-Fi recovery: STA retry started"
                               : "Wi-Fi STA connecting to configured SSID");
  if (!keepSetupAccessPoint) showStatus("Wi-Fi connecting", ssid);
}

bool timerReached(uint32_t nowMs, uint32_t deadlineMs) {
  return static_cast<int32_t>(nowMs - deadlineMs) >= 0;
}

void finishWifiRecovery() {
  dnsServer.stop();
  WiFi.softAPdisconnect(true);
  WiFi.mode(WIFI_STA);
  accessPointActive = false;
  wifiRecoveryActive = false;
  stationAttemptActive = false;
  logLine("Wi-Fi recovery: STA connected; setup AP stopped");
}

void startNetwork() {
  const String ssid = wifiPreferences.getString("ssid", "");
  if (postoffice::wifiStartupMode(!ssid.isEmpty()) ==
      postoffice::WifiStartupMode::StationAttempt) {
    accessPointActive = false;
    wifiRecoveryActive = false;
    startStoredStationAttempt(false);
    return;
  }

  startSetupAccessPoint(false);
}

String wifiModeName() {
  if (accessPointActive) return "ap";
  if (WiFi.status() == WL_CONNECTED) return "sta_connected";
  return "sta_connecting";
}

void handleRoot() {
  webServer.send_P(200, "text/html", LAB2_INDEX_HTML);
}

void handleSettingsGet() {
  settings = settingsStore.load();
  JsonDocument document;
  document["ssid"] = wifiPreferences.getString("ssid", "");
  document["server_url"] = settings.serverUrl;
  document["poll_interval_ms"] = settings.pollIntervalMs;
  document["dev_http"] = settings.allowDevHttp;
  document["atom_key_configured"] = !settings.atomKey.isEmpty();
  document["wifi_mode"] = wifiModeName();
  document["post_office_status"] = postOfficeClient.statusText();
  // Wi-Fi password and Atom key are intentionally never returned.
  String response;
  serializeJson(document, response);
  webServer.send(200, "application/json", response);
}

void handleSettingsPost() {
  postoffice::Settings candidate = settingsStore.load();
  candidate.serverUrl = webServer.arg("server_url");
  candidate.serverUrl.trim();
  candidate.allowDevHttp = webServer.arg("dev_http") == "1";
  const String key = webServer.arg("atom_key");
  if (!key.isEmpty()) candidate.atomKey = key;

  const String interval = webServer.arg("poll_interval_ms");
  if (interval.isEmpty()) {
    webServer.send(400, "application/json", "{\"error\":\"poll_interval_required\"}");
    return;
  }
  candidate.pollIntervalMs = interval.toInt();
  const postoffice::ConfigInput input{candidate.serverUrl.c_str(), candidate.atomKey.c_str(),
                                      candidate.pollIntervalMs, candidate.allowDevHttp};
  const postoffice::ConfigResult validation = postoffice::validateConfig(input);
  if (!validation.ok()) {
    webServer.send(400, "application/json",
                   "{\"error\":" + jsonString(validation.reason) + "}");
    return;
  }
  if (!settingsStore.save(candidate)) {
    webServer.send(500, "application/json", "{\"error\":\"settings_store_failed\"}");
    return;
  }

  const String ssid = webServer.arg("ssid");
  const String wifiPassword = webServer.arg("wifi_pass");
  if (!ssid.isEmpty()) {
    wifiPreferences.putString("ssid", ssid);
    if (!wifiPassword.isEmpty()) wifiPreferences.putString("pass", wifiPassword);
  }
  settings = candidate;
  postOfficeClient.configure(settings);
  logLine("post-office settings saved; secrets not logged");
  webServer.send(200, "application/json", "{\"saved\":true,\"wifi_restart_required\":true}");
}

void handlePostOfficeTest() {
  // Deliberately calls only /health; it cannot claim or execute a job.
  const String result = postOfficeClient.testConnection();
  const bool ok = result == "health_ok";
  webServer.send(ok ? 200 : 503, "application/json",
                 "{\"result\":" + jsonString(result) + "}");
}

void handlePressureSettingsGet() {
  pressureCalibration = pressureSettingsStore.load();
  JsonDocument document;
  document["calibrated"] = pressureCalibration.calibrated;
  document["sensor_confirmed"] = pressureSensorConfirmed;
  document["adc_pin"] = "G5";
  if (pressureCalibration.calibrated) {
    document["volts_per_count"] = pressureCalibration.voltsPerCount;
    document["voltage_offset_v"] = pressureCalibration.voltageOffsetV;
    document["kpa_per_volt"] = pressureCalibration.kpaPerVolt;
    document["pressure_offset_kpa"] = pressureCalibration.pressureOffsetKpa;
  } else {
    document["volts_per_count"] = nullptr;
    document["voltage_offset_v"] = nullptr;
    document["kpa_per_volt"] = nullptr;
    document["pressure_offset_kpa"] = nullptr;
  }
  String response;
  serializeJson(document, response);
  webServer.send(200, "application/json", response);
}

void handlePressureSettingsPost() {
  const String sensorConfirmedValue = webServer.arg("sensor_confirmed");
  if (!sensorConfirmedValue.isEmpty() && sensorConfirmedValue!="0" && sensorConfirmedValue!="1") {
    webServer.send(400,"application/json","{\"error\":\"invalid_sensor_confirmation\"}");
    return;
  }
  const String calibratedValue = webServer.arg("pressure_calibrated");
  if (calibratedValue != "0" && calibratedValue != "1") {
    webServer.send(400, "application/json",
                   "{\"error\":\"malformed_pressure_settings\"}");
    return;
  }
  pressure::Calibration candidate;
  candidate.calibrated = calibratedValue == "1";
  if (candidate.calibrated) {
    const pressure::CalibrationResult parsed = pressure::parseCalibration(
        webServer.arg("volts_per_count").c_str(),
        webServer.arg("voltage_offset_v").c_str(),
        webServer.arg("kpa_per_volt").c_str(),
        webServer.arg("pressure_offset_kpa").c_str(), &candidate);
    if (!parsed.ok()) {
      webServer.send(400, "application/json",
                     "{\"error\":" + jsonString(parsed.reason) + "}");
      return;
    }
  }
  if (!pressureSettingsStore.save(candidate)) {
    webServer.send(500, "application/json",
                   "{\"error\":\"pressure_settings_store_failed\"}");
    return;
  }
  pressureCalibration = candidate;
  pressureSensorConfirmed = sensorConfirmedValue == "1";
  logLine(candidate.calibrated ? "pressure calibration saved"
                               : "pressure calibration disabled");
  webServer.send(200, "application/json",
                 candidate.calibrated
                     ? "{\"saved\":true,\"calibrated\":true}"
                     : "{\"saved\":true,\"calibrated\":false}");
}

int readPressureRawAdc() {
  uint32_t total = 0;
  for (int sample = 0; sample < kPressureSampleCount; ++sample) {
    total += static_cast<uint32_t>(analogRead(kPressureAdcPin));
  }
  return static_cast<int>(total / kPressureSampleCount);
}

void handlePressureTest() {
  pressureCalibration = pressureSettingsStore.load();
  const pressure::Reading reading =
      pressure::convertSensorReading(readPressureRawAdc(), pressureCalibration, pressureSensorConfirmed);
  JsonDocument document;
  document["status"] = reading.status;
  document["sample_count"] = kPressureSampleCount;
  document["raw_adc"] = reading.rawAdc;
  document["calibrated"] = pressureCalibration.calibrated;
  document["sensor_confirmed"] = pressureSensorConfirmed;
  if (reading.voltageAvailable) {
    document["voltage_v"] = reading.voltageV;
  } else {
    document["voltage_v"] = nullptr;
  }
  if (reading.pressureAvailable) {
    document["pressure_kpa"] = reading.pressureKpa;
  } else {
    document["pressure_kpa"] = nullptr;
  }
  String response;
  serializeJson(document, response);
  const bool safeResponse = reading.ok() ||
                            reading.code == pressure::ReadingCode::NotCalibrated ||
                            reading.code == pressure::ReadingCode::SensorUnconfirmed;
  webServer.send(safeResponse ? 200 : 503, "application/json", response);
}

void handleState() {
  const postoffice::PendingResult pending = persistentState.pendingResult();
  JsonDocument document;
  document["device_id"] = deviceId();
  document["wifi"] = wifiModeName();
  document["post_office"] = postOfficeClient.statusText();
  document["active_job_id"] = persistentState.activeJobId();
  document["pending_result_id"] = pending.present ? pending.jobId : "";
  document["pressure_available"] = false;
  document["pressure_calibrated"] = pressureCalibration.calibrated;
  document["pressure_sensor_confirmed"] = pressureSensorConfirmed;
  document["pressure"] = nullptr;
  String response;
  serializeJson(document, response);
  webServer.send(200, "application/json", response);
}

void networkTask(void*) {
  bool lastConnected = false;
  for (;;) {
    webServer.handleClient();
    if (accessPointActive) dnsServer.processNextRequest();
    const uint32_t nowMs = millis();
    const bool connected = WiFi.status() == WL_CONNECTED;
    if (connected != lastConnected) {
      logLine(connected ? "Wi-Fi connected" : "Wi-Fi disconnected");
      if (connected) {
        stationAttemptActive = false;
      } else if (lastConnected && !wifiRecoveryActive) {
        stationAttemptActive = true;
        stationAttemptStartedMs = nowMs;
      }
      lastConnected = connected;
    }

    const postoffice::WifiRecoveryAction action = postoffice::wifiRecoveryAction(
        wifiRecoveryActive, stationAttemptActive, connected,
        nowMs - stationAttemptStartedMs, timerReached(nowMs, nextStationRetryAtMs));
    if (action == postoffice::WifiRecoveryAction::EnterFallback) {
      logLine("Wi-Fi STA timeout; final status=" +
              String(static_cast<int>(WiFi.status())));
      logLine("Wi-Fi STA timeout; starting setup AP with periodic STA recovery");
      startSetupAccessPoint(true);
      lastConnected = false;
    } else if (action == postoffice::WifiRecoveryAction::StartRetry) {
      startStoredStationAttempt(true);
    } else if (action == postoffice::WifiRecoveryAction::RetryTimedOut) {
      logLine("Wi-Fi recovery: STA retry timed out; final status=" +
              String(static_cast<int>(WiFi.status())));
      WiFi.disconnect(false, false);
      stationAttemptActive = false;
      nextStationRetryAtMs = nowMs + postoffice::kWifiStaRetryIntervalMs;
    } else if (action == postoffice::WifiRecoveryAction::RetrySucceeded) {
      finishWifiRecovery();
    }

    postOfficeClient.tick(nowMs);
    vTaskDelay(1);
  }
}

void pollSerialStationBoundary() {
  while (Serial.available()) {
    const char character = static_cast<char>(Serial.read());
    if (character == '\n' || character == '\r') {
      if (!serialLine.isEmpty()) {
        const postoffice::PendingResult before = persistentState.pendingResult();
        if (displayImageJob.handleStationResult(persistentState, [&] {
              return stationBridge.handleResultLine(serialLine, persistentState);
            })) {
          const postoffice::PendingResult after = persistentState.pendingResult();
          if (!before.present && after.present) logLine("local station result queued");
        }
        // Non-post-office JSON can be handed to the Lab 1 pump parser when
        // the projects are merged. That hardware integration remains TODO.
        serialLine = "";
      }
    } else if (character >= 0x20 && serialLine.length() < 512) {
      serialLine += character;
    }
  }
}

}  // namespace

void setup() {
  auto config = M5.config();
  M5.begin(config);
  M5.Display.setRotation(0);
  // Default HWCDC TX ring is 256 bytes; logs plus a job line overflow it.
  Serial.setTxBufferSize(4096);
  Serial.begin(115200);

  wifiPreferences.begin("wifi", false);  // compatible with Lab 1 keys
  settingsStore.begin();
  pressureSettingsStore.begin();
  persistentState.begin();
  stationBridge.begin();
  settings = settingsStore.load();
  pressureCalibration = pressureSettingsStore.load();
  pinMode(kPressureAdcPin, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(kPressureAdcPin, ADC_11db);
  postOfficeClient.begin(deviceId(), persistentState, stationBridge, POST_OFFICE_ROOT_CA,
                        &displayImageJob);
  postOfficeClient.configure(settings);

  WiFi.onEvent(handleWifiEvent);
  startNetwork();
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");

  webServer.on("/", HTTP_GET, handleRoot);
  webServer.on("/settings", HTTP_GET, handleSettingsGet);
  webServer.on("/settings", HTTP_POST, handleSettingsPost);
  webServer.on("/state", HTTP_GET, handleState);
  webServer.on("/test/post-office", HTTP_POST, handlePostOfficeTest);
  webServer.on("/pressure/settings", HTTP_GET, handlePressureSettingsGet);
  webServer.on("/pressure/settings", HTTP_POST, handlePressureSettingsPost);
  webServer.on("/test/pressure", HTTP_POST, handlePressureTest);
  webServer.onNotFound([]() {
    if (accessPointActive) handleRoot();
    else webServer.send(404, "application/json", "{\"error\":\"not_found\"}");
  });
  webServer.begin();

  xTaskCreatePinnedToCore(networkTask, "lab2-net", 12288, nullptr, 1, nullptr, 0);
  logLine("Lab 2 foundation ready; real station/hardware validation TODO");
}

void loop() {
  M5.update();
  pollSerialStationBoundary();
  displayImageJob.processPending(persistentState, localdisplay::render);
  // Future Lab 1 display/button and pump work remains on core 1.
  delay(2);
}
#endif  // !BENCH_MODE
