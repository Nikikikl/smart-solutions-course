#include <Arduino.h>
#include <WiFi.h>
#include <esp_camera.h>
#include <esp_http_server.h>

#include "camera_pins.h"
#include "camera_settings.h"
#include "tool_camera_core.h"

#if __has_include("wifi_private.h")
#include "wifi_private.h"
#else
#include "wifi_private.example.h"
#endif

#ifndef TOOL_CAMERA_WIFI_SSID
#error "Wi-Fi config must define TOOL_CAMERA_WIFI_SSID"
#endif
#ifndef TOOL_CAMERA_WIFI_PASSWORD
#error "Wi-Fi config must define TOOL_CAMERA_WIFI_PASSWORD"
#endif
#ifndef TOOL_CAMERA_HOSTNAME
#define TOOL_CAMERA_HOSTNAME ""
#endif

namespace {

SemaphoreHandle_t g_camera_mutex = nullptr;
httpd_handle_t g_http_server = nullptr;
bool g_camera_available = false;
const char* g_sensor_name = "unknown";
volatile uint32_t g_frames_served = 0;

bool g_wifi_was_connected = false;
bool g_wifi_config_valid = false;
uint32_t g_wifi_failed_attempts = 0;
uint32_t g_last_wifi_attempt_ms = 0;
uint32_t g_wifi_retry_delay_ms = 0;

esp_err_t sendJsonError(httpd_req_t* request, const char* status,
                        const char* code) {
  char body[96];
  snprintf(body, sizeof(body), "{\"error\":\"%s\"}", code);
  httpd_resp_set_status(request, status);
  httpd_resp_set_type(request, "application/json");
  httpd_resp_set_hdr(request, "Cache-Control", "no-store");
  return httpd_resp_sendstr(request, body);
}

esp_err_t statusHandler(httpd_req_t* request) {
  const bool wifi_connected = WiFi.status() == WL_CONNECTED;
  const IPAddress address = wifi_connected ? WiFi.localIP() : IPAddress();
  char body[384];
  snprintf(body, sizeof(body),
           "{\"device\":\"tool-camera\",\"camera\":\"%s\","
           "\"wifi\":\"%s\",\"ip\":\"%u.%u.%u.%u\","
           "\"sensor\":\"%s\",\"frames\":%lu,\"uptime_ms\":%lu}",
           g_camera_available ? "available" : "unavailable",
           wifi_connected ? "connected" : "disconnected", address[0],
           address[1], address[2], address[3], g_sensor_name,
           static_cast<unsigned long>(g_frames_served),
           static_cast<unsigned long>(millis()));
  httpd_resp_set_type(request, "application/json");
  httpd_resp_set_hdr(request, "Cache-Control", "no-store");
  return httpd_resp_sendstr(request, body);
}

esp_err_t snapshotHandler(httpd_req_t* request) {
  if (!g_camera_available || g_camera_mutex == nullptr) {
    return sendJsonError(request, "503 Service Unavailable",
                         "camera_unavailable");
  }
  if (xSemaphoreTake(g_camera_mutex,
                     pdMS_TO_TICKS(tool_camera::kCaptureMutexTimeoutMs)) !=
      pdTRUE) {
    return sendJsonError(request, "503 Service Unavailable", "camera_busy");
  }

  camera_fb_t* frame = esp_camera_fb_get();
  if (frame == nullptr) {
    xSemaphoreGive(g_camera_mutex);
    Serial.println("Snapshot error: camera returned no frame");
    return sendJsonError(request, "500 Internal Server Error",
                         "capture_failed");
  }

  const bool complete_jpeg = frame->len >= 4 && frame->buf[0] == 0xff &&
                             frame->buf[1] == 0xd8 &&
                             frame->buf[frame->len - 2] == 0xff &&
                             frame->buf[frame->len - 1] == 0xd9;
  esp_err_t result = ESP_FAIL;
  if (complete_jpeg) {
    httpd_resp_set_type(request, tool_camera::snapshotContentType());
    httpd_resp_set_hdr(request, "Cache-Control", "no-store, max-age=0");
    result = httpd_resp_send(request, reinterpret_cast<const char*>(frame->buf),
                             frame->len);
    if (result == ESP_OK) {
      ++g_frames_served;
    }
  } else {
    Serial.println("Snapshot error: incomplete JPEG frame");
    result = sendJsonError(request, "500 Internal Server Error",
                           "incomplete_jpeg");
  }

  esp_camera_fb_return(frame);
  xSemaphoreGive(g_camera_mutex);
  return result;
}

bool initializeCamera() {
  if (!psramFound()) {
    Serial.println("Camera unavailable: PSRAM was not detected");
    return false;
  }

  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = kCameraPinD0;
  config.pin_d1 = kCameraPinD1;
  config.pin_d2 = kCameraPinD2;
  config.pin_d3 = kCameraPinD3;
  config.pin_d4 = kCameraPinD4;
  config.pin_d5 = kCameraPinD5;
  config.pin_d6 = kCameraPinD6;
  config.pin_d7 = kCameraPinD7;
  config.pin_xclk = kCameraPinXclk;
  config.pin_pclk = kCameraPinPclk;
  config.pin_vsync = kCameraPinVsync;
  config.pin_href = kCameraPinHref;
  config.pin_sccb_sda = kCameraPinSiod;
  config.pin_sccb_scl = kCameraPinSioc;
  config.pin_pwdn = kCameraPinPwdn;
  config.pin_reset = kCameraPinReset;
  config.xclk_freq_hz = tool_camera::kXclkHz;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = tool_camera::kFrameSize;
  config.jpeg_quality = tool_camera::kJpegQuality;
  config.fb_count = tool_camera::kFrameBufferCount;
  config.grab_mode = CAMERA_GRAB_LATEST;
  config.fb_location = CAMERA_FB_IN_PSRAM;

  const esp_err_t error = esp_camera_init(&config);
  if (error != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", error);
    return false;
  }

  sensor_t* sensor = esp_camera_sensor_get();
  if (sensor != nullptr) {
    const camera_sensor_info_t* info = esp_camera_sensor_get_info(&sensor->id);
    g_sensor_name = info != nullptr ? info->name
                                    : tool_camera::sensorModelName(sensor->id.PID);
    if (sensor->id.PID == OV3660_PID) {
      // Colour correction from the official Arduino camera example. Its vflip
      // is left out, as in the 3D Printing USB firmware: the picture must keep
      // the orientation the hub and the 3D Lab 2 evidence frames use until the
      // orientation on the J4 mount is checked.
      sensor->set_brightness(sensor, 1);
      sensor->set_saturation(sensor, -2);
    }
  }
  Serial.printf("Camera initialized; detected sensor: %s\n", g_sensor_name);
  return true;
}

bool startHttpServer() {
  if (g_http_server != nullptr) {
    return true;
  }
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.lru_purge_enable = true;
  config.stack_size = 8192;
  if (httpd_start(&g_http_server, &config) != ESP_OK) {
    g_http_server = nullptr;
    Serial.println("HTTP server start failed");
    return false;
  }

  const httpd_uri_t status_uri = {
      .uri = "/status",
      .method = HTTP_GET,
      .handler = statusHandler,
      .user_ctx = nullptr,
  };
  const httpd_uri_t snapshot_uri = {
      .uri = "/snapshot.jpg",
      .method = HTTP_GET,
      .handler = snapshotHandler,
      .user_ctx = nullptr,
  };
  if (httpd_register_uri_handler(g_http_server, &status_uri) != ESP_OK ||
      httpd_register_uri_handler(g_http_server, &snapshot_uri) != ESP_OK) {
    Serial.println("HTTP route registration failed");
    httpd_stop(g_http_server);
    g_http_server = nullptr;
    return false;
  }
  Serial.println("HTTP server started: /status and /snapshot.jpg");
  return true;
}

void serviceWifi() {
  const bool connected = WiFi.status() == WL_CONNECTED;
  if (connected) {
    if (!g_wifi_was_connected) {
      g_wifi_was_connected = true;
      g_wifi_failed_attempts = 0;
      Serial.print("Wi-Fi connected; local IP: ");
      Serial.println(WiFi.localIP());
      startHttpServer();
    }
    return;
  }

  if (g_wifi_was_connected) {
    g_wifi_was_connected = false;
    Serial.println("Wi-Fi disconnected; waiting before reconnect");
  }
  if (!g_wifi_config_valid) {
    return;
  }

  const uint32_t now = millis();
  if (!tool_camera::intervalElapsed(now, g_last_wifi_attempt_ms,
                                    g_wifi_retry_delay_ms)) {
    return;
  }
  g_last_wifi_attempt_ms = now;
  g_wifi_retry_delay_ms =
      tool_camera::reconnectBackoffMs(g_wifi_failed_attempts++);
  Serial.printf("Wi-Fi connection attempt; next retry in %lu ms\n",
                static_cast<unsigned long>(g_wifi_retry_delay_ms));
  WiFi.begin(TOOL_CAMERA_WIFI_SSID, TOOL_CAMERA_WIFI_PASSWORD);
}

// USB Serial protocol of the 3D Printing Lab 2 tool-camera firmware
// (3d-print/lab2/tool-camera/capture.py, hub ToolCamera): 'c' answers
// "JPG <len>\n" + JPEG bytes, 'i' answers one INFO line. Keeping it here lets
// one firmware serve both the Wi-Fi /snapshot.jpg path and the USB hub path.
void serviceSerialCommands() {
  while (Serial.available() > 0) {
    const int command = Serial.read();
    if (command == 'i') {
      Serial.printf("INFO camera=%s sensor=%s psram=%u wifi=%s frames=%lu\n",
                    g_camera_available ? "ok" : "fail", g_sensor_name,
                    static_cast<unsigned>(ESP.getPsramSize()),
                    WiFi.status() == WL_CONNECTED ? "connected" : "disconnected",
                    static_cast<unsigned long>(g_frames_served));
      continue;
    }
    if (command != 'c') {
      continue;
    }
    if (!g_camera_available || g_camera_mutex == nullptr) {
      Serial.println("ERR camera not ready");
      continue;
    }
    if (xSemaphoreTake(g_camera_mutex,
                       pdMS_TO_TICKS(tool_camera::kCaptureMutexTimeoutMs)) !=
        pdTRUE) {
      Serial.println("ERR camera busy");
      continue;
    }
    camera_fb_t* frame = esp_camera_fb_get();
    if (frame == nullptr) {
      xSemaphoreGive(g_camera_mutex);
      Serial.println("ERR capture failed");
      continue;
    }
    Serial.printf("JPG %u\n", static_cast<unsigned>(frame->len));
    Serial.write(frame->buf, frame->len);
    Serial.flush();
    ++g_frames_served;
    esp_camera_fb_return(frame);
    xSemaphoreGive(g_camera_mutex);
  }
}

}  // namespace

void setup() {
  // Native USB CDC (HWCDC): the default 256-byte TX ring and 100 ms host wait
  // drop parts of a 30-40 kB JPEG whenever the PC reads a little late
  // (arduino-esp32 #10836). Buffer more and wait longer instead of dropping.
  Serial.setTxBufferSize(16384);
  Serial.setTxTimeoutMs(2000);
  Serial.begin(115200);
  delay(250);
  Serial.println("Lab 2 tool camera boot");

  g_camera_mutex = xSemaphoreCreateMutex();
  if (g_camera_mutex == nullptr) {
    Serial.println("Camera unavailable: mutex allocation failed");
  } else {
    g_camera_available = initializeCamera();
  }

  const tool_camera::WifiConfigError config_error =
      tool_camera::validateWifiConfig(TOOL_CAMERA_WIFI_SSID,
                                      TOOL_CAMERA_WIFI_PASSWORD,
                                      TOOL_CAMERA_HOSTNAME);
  g_wifi_config_valid = config_error == tool_camera::WifiConfigError::kOk;
  if (!g_wifi_config_valid) {
    Serial.printf("Wi-Fi disabled: %s; create ignored wifi_private.h\n",
                  tool_camera::wifiConfigErrorName(config_error));
    return;
  }

  WiFi.mode(WIFI_STA);
  // Modem sleep (default WIFI_PS_MIN_MODEM) holds incoming packets until the
  // next DTIM beacon, ~100-300 ms per request; the official CameraWebServer
  // example disables it as well. Costs power, the XIAO is USB-powered.
  WiFi.setSleep(false);
  if (TOOL_CAMERA_HOSTNAME[0] != '\0') {
    WiFi.setHostname(TOOL_CAMERA_HOSTNAME);
  }
  g_wifi_retry_delay_ms = 0;
  serviceWifi();
}

void loop() {
  serviceSerialCommands();
  serviceWifi();
  delay(5);
}
