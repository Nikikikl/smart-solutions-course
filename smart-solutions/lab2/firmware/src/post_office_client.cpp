#include "post_office_client.h"

#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <atomic>
#include <esp_sntp.h>
#include <mbedtls/x509_crt.h>
#include <time.h>
#include "normal_tls.h"

#ifndef MBEDTLS_SSL_KEEP_PEER_CERTIFICATE
#error "Normal TLS validity checking requires retained peer certificates"
#endif

namespace postoffice {
namespace {

constexpr uint32_t kResultRetryMs = 2000;
constexpr int64_t kClockPlausibleAfter = 1700000000LL;
std::atomic<bool> utcSynchronized{false};

void timeSynchronized(struct timeval* value) {
  utcSynchronized.store(value && normaltls::utcValid(true,value->tv_sec));
}

bool trustedClock() {
  return normaltls::utcValid(utcSynchronized.load(),static_cast<int64_t>(time(nullptr)));
}

class ValidityCheckedClient : public WiFiClientSecure {
 public:
  explicit ValidityCheckedClient(const char* ca): ca_(ca) { setCACert(ca); }
  int connect(const char* host,uint16_t port,int32_t timeout) override {
    return normaltls::connectVerified(trustedClock,
      [&] { return WiFiClientSecure::connect(host,port,timeout); },
      [&] {
        mbedtls_x509_crt roots;
        mbedtls_x509_crt_init(&roots);
        auto* peer=const_cast<mbedtls_x509_crt*>(getPeerCertificate());
        bool ok=false;
        if (ca_ && mbedtls_x509_crt_parse(&roots,
            reinterpret_cast<const unsigned char*>(ca_),strlen(ca_)+1)==0) {
          ok=normaltls::verifyChain(peer,&roots,host,static_cast<int64_t>(time(nullptr)),
            MBEDTLS_X509_BADCERT_OTHER,
            [](mbedtls_x509_crt* chain,mbedtls_x509_crt* ca,const char* name,
               uint32_t* flags,int (*cb)(void*,mbedtls_x509_crt*,int,uint32_t*),void* ctx) {
              return mbedtls_x509_crt_verify(chain,ca,nullptr,name,flags,cb,ctx);
            });
        }
        mbedtls_x509_crt_free(&roots);
        return ok;
      },[&] { stop(); });
  }
 private:
  const char* ca_;
};

void logLine(const String& message) {
  Serial.println("# POST " + message);
}

// Gregorian civil date to Unix days, adapted from Howard Hinnant's public
// domain civil calendar algorithm. This avoids locale/timezone ambiguity.
int64_t daysFromCivil(int year, unsigned month, unsigned day) {
  year -= month <= 2;
  const int era = (year >= 0 ? year : year - 399) / 400;
  const unsigned yearOfEra = static_cast<unsigned>(year - era * 400);
  const unsigned dayOfYear =
      (153 * (month + (month > 2 ? -3 : 9)) + 2) / 5 + day - 1;
  const unsigned dayOfEra = yearOfEra * 365 + yearOfEra / 4 - yearOfEra / 100 + dayOfYear;
  return static_cast<int64_t>(era) * 146097 + static_cast<int64_t>(dayOfEra) - 719468;
}

bool parseUtc(const char* value, int64_t& epoch) {
  if (value == nullptr) return false;
  int year = 0;
  unsigned month = 0, day = 0, hour = 0, minute = 0, second = 0;
  int consumed = 0;
  if (sscanf(value, "%d-%u-%uT%u:%u:%u%n", &year, &month, &day, &hour, &minute,
             &second, &consumed) != 6) {
    return false;
  }
  const char* tail = value + consumed;
  if (*tail == '.') {
    ++tail;
    const char* fractionStart = tail;
    while (*tail >= '0' && *tail <= '9') ++tail;
    if (tail == fractionStart) return false;
  }
  if (*tail != 'Z' || tail[1] != '\0') return false;
  if (month < 1 || month > 12 || day < 1 || day > 31 || hour > 23 || minute > 59 ||
      second > 60) {
    return false;
  }
  epoch = daysFromCivil(year, month, day) * 86400 + hour * 3600 + minute * 60 + second;
  return true;
}

bool hasDirectMotionField(JsonObjectConst object) {
  static const char* fields[] = {
      "x",          "y",       "z",       "r",       "speed",
      "pump",       "do",      "command", "coordinates", "trajectory",
      "motion",     "script",  "joints",  "joint",   "repetitions"};
  for (JsonPairConst pair : object) {
    for (const char* field : fields) {
      if (strcmp(pair.key().c_str(), field) == 0) return true;
    }
  }
  return false;
}

bool hasUnsupportedJobField(JsonObjectConst object) {
  static const char* allowed[] = {"id",         "job",       "arg",    "created_at",
                                  "expires_at", "status",    "claimed_at",
                                  "result",     "reason",    "updated_at"};
  for (JsonPairConst pair : object) {
    bool known = false;
    for (const char* field : allowed) {
      if (strcmp(pair.key().c_str(), field) == 0) {
        known = true;
        break;
      }
    }
    if (!known) return true;
  }
  return false;
}

}  // namespace

void PostOfficeClient::begin(const String& deviceId, PersistentState& state,
                             StationBridge& bridge, const char* rootCa, DisplayImageJob* display) {
  deviceId_ = deviceId;
  state_ = &state;
  bridge_ = &bridge;
  display_ = display;
  rootCa_ = rootCa;
  sntp_set_time_sync_notification_cb(timeSynchronized);
}

void PostOfficeClient::configure(const Settings& settings) {
  settings_ = settings;
  nextPollAtMs_ = 0;
  setStatus("configured");
}

void PostOfficeClient::setStatus(const String& value) {
  statusText_ = value;
}

String PostOfficeClient::endpoint(const String& path) const {
  String base = settings_.serverUrl;
  while (base.endsWith("/")) base.remove(base.length() - 1);
  return base + path;
}

bool PostOfficeClient::transportReady(String& reason) const {
  const ConfigInput input{settings_.serverUrl.c_str(), settings_.atomKey.c_str(),
                          settings_.pollIntervalMs, settings_.allowDevHttp};
  const ConfigResult validation = validateConfig(input);
  if (!validation.ok()) {
    reason = validation.reason;
    return false;
  }
  if (settings_.serverUrl.startsWith("https://") && rootCa_ == nullptr) {
    reason = "https_ca_not_configured";
    return false;
  }
  if (WiFi.status() != WL_CONNECTED) {
    reason = "wifi_disconnected";
    return false;
  }
  if (settings_.serverUrl.startsWith("https://") && !trustedClock()) {
    reason = "https_time_unavailable";
    return false;
  }
  return true;
}

int PostOfficeClient::postJson(const String& path, const String& payload, String& response) {
  String reason;
  if (!transportReady(reason)) {
    setStatus(reason);
    return -1;
  }

  HTTPClient http;
  http.setConnectTimeout(1500);
  http.setTimeout(2500);
  http.setFollowRedirects(HTTPC_DISABLE_FOLLOW_REDIRECTS);
  const String url = endpoint(path);
  int code = -1;
  if (url.startsWith("https://")) {
    ValidityCheckedClient client(rootCa_);
    if (!http.begin(client, url)) return -1;
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", "Bearer " + settings_.atomKey);
    code = http.POST(payload);
    if (code > 0) response = http.getString();
    http.end();
  } else {
    WiFiClient client;
    if (!http.begin(client, url)) return -1;
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", "Bearer " + settings_.atomKey);
    code = http.POST(payload);
    if (code > 0) response = http.getString();
    http.end();
  }
  return code;
}

int PostOfficeClient::get(const String& path, String& response) {
  String reason;
  if (!transportReady(reason)) {
    setStatus(reason);
    return -1;
  }

  HTTPClient http;
  http.setConnectTimeout(1500);
  http.setTimeout(2500);
  http.setFollowRedirects(HTTPC_DISABLE_FOLLOW_REDIRECTS);
  const String url = endpoint(path);
  int code = -1;
  if (url.startsWith("https://")) {
    ValidityCheckedClient client(rootCa_);
    if (!http.begin(client, url)) return -1;
    http.addHeader("Authorization", "Bearer " + settings_.atomKey);
    code = http.GET();
    if (code > 0) response = http.getString();
    http.end();
  } else {
    WiFiClient client;
    if (!http.begin(client, url)) return -1;
    http.addHeader("Authorization", "Bearer " + settings_.atomKey);
    code = http.GET();
    if (code > 0) response = http.getString();
    http.end();
  }
  return code;
}

bool PostOfficeClient::parseJobResponse(const String& response, Job& job, bool& hasJob,
                                        String& refusalReason) {
  JsonDocument document;
  if (deserializeJson(document, response) != DeserializationError::Ok) {
    refusalReason = "invalid_server_json";
    return false;
  }
  if (document["job"].isNull()) {
    hasJob = false;
    return true;
  }
  hasJob = true;
  JsonObjectConst object = document["job"].as<JsonObjectConst>();
  JsonObjectConst argument = object["arg"].as<JsonObjectConst>();
  strlcpy(job.id, object["id"] | "", sizeof(job.id));
  strlcpy(job.type, object["job"] | "", sizeof(job.type));

  const char* letter = argument["letter"] | "";
  job.letter = strlen(letter) == 1 ? letter[0] : 0;
  strlcpy(job.routine, argument["routine"] | "", sizeof(job.routine));
  const JsonString imageId = argument["image_id"].as<JsonString>();
  const bool validImageString = !imageId.isNull() && imageId.size() <= kMaxImageId &&
      imageId.size() == strlen(imageId.c_str());
  if (validImageString) strlcpy(job.imageId, imageId.c_str(), sizeof(job.imageId));
  const bool expectedArgument =
      (strcmp(job.type, "letter") == 0 && argument.size() == 1 &&
       argument["letter"].is<const char*>()) ||
      (strcmp(job.type, "pick_place") == 0 && argument.size() == 1 &&
       argument["routine"].is<const char*>()) ||
      (strcmp(job.type, "display_image") == 0 && argument.size() == 1 && validImageString);
  job.hasDirectMotionData = hasUnsupportedJobField(object) || hasDirectMotionField(object) ||
                            hasDirectMotionField(argument) || !expectedArgument;
  if (!parseUtc(object["expires_at"].as<const char*>(), job.expiresEpoch)) {
    refusalReason = "invalid_expiration";
    return false;
  }

  const int64_t nowEpoch = static_cast<int64_t>(time(nullptr));
  const bool clockAvailable = nowEpoch >= kClockPlausibleAfter;
  const ValidationResult validation = validateJob(job, nowEpoch, clockAvailable);
  if (!validation.ok()) {
    refusalReason = validation.reason;
    return false;
  }
  return true;
}

void PostOfficeClient::pollOnce(uint32_t nowMs) {
  JsonDocument request;
  request["device_id"] = deviceId_;
  request["poll_interval_ms"] = settings_.pollIntervalMs;
  request["atom_uptime_ms"] = nowMs;
  JsonObject station = request["station"].to<JsonObject>();
  // The serial adapter exists, but station reachability has not been measured.
  station["reachable"] = false;
  station["robot_state"] = "unknown";
  String payload;
  serializeJson(request, payload);

  String response;
  const int code = postJson("/api/atom/poll", payload, response);
  if (code != 200) {
    setStatus(code > 0 ? "poll_http_" + String(code) : "poll_failed");
    logLine(statusText_);
    return;
  }

  Job job;
  bool hasJob = false;
  String refusalReason;
  if (!parseJobResponse(response, job, hasJob, refusalReason)) {
    // The server has already claimed a response job. If an ID is available,
    // report a terminal refusal rather than silently dropping it.
    if (job.id[0] != '\0' && state_->startClaim(job.id))
      state_->queueRefused(job.id, refusalReason);
    setStatus("job_refused:" + refusalReason);
    logLine(statusText_);
    return;
  }
  if (!hasJob) {
    setStatus("poll_ok_no_job");
    return;
  }

  logLine("received id=" + String(job.id) + " type=" + String(job.type));
  if (state_->isDuplicate(job.id)) {
    state_->queueRefused(job.id, "duplicate_job");
    setStatus("duplicate_job");
    return;
  }
  if (strcmp(job.type, "display_image") == 0) {
    if (display_ && display_->accept(job, *state_)) {
      setStatus("awaiting_local_display");
    } else {
      if (!display_ && state_->startClaim(job.id))
        state_->queueRefused(job.id, "display_unavailable");
      setStatus("display_claim_failed");
    }
    return;  // Local LCD jobs never reach the USB station boundary.
  }
  if (!state_->startClaim(job.id)) {
    state_->queueRefused(job.id, "claim_state_conflict");
    setStatus("claim_state_conflict");
    return;
  }
  if (!bridge_->dispatchJob(job, nowMs)) {
    state_->queueRefused(job.id, "station_dispatch_failed");
    setStatus("station_dispatch_failed");
    return;
  }
  setStatus("awaiting_station_result");
  logLine("dispatched id=" + String(job.id) + " to local station boundary");
}

void PostOfficeClient::sendPendingResult(uint32_t nowMs) {
  const PendingResult pending = state_->pendingResult();
  if (!state_->healthy()) { setStatus("nvs_state_error"); return; }
  if (!pending.present) return;

  JsonDocument document;
  document["id"] = pending.jobId;
  document["status"] = pending.status;
  if (pending.status == "done") {
    document["result"]["source"] = pending.source;
  } else {
    document["reason"] = pending.reason;
  }
  String payload;
  serializeJson(document, payload);

  String response;
  const int code = postJson("/api/atom/result", payload, response);
  if (code == 200) {
    if (!state_->acknowledgeResult(pending.jobId)) {
      setStatus("nvs_state_error");
      return;
    }
    setStatus("result_sent");
    logLine("result sent id=" + pending.jobId);
  } else {
    nextResultAttemptAtMs_ = nowMs + kResultRetryMs;
    setStatus(code > 0 ? "result_http_" + String(code) : "result_retry_wait");
    logLine("result retained id=" + pending.jobId + " status=" + statusText_);
  }
}

void PostOfficeClient::tick(uint32_t nowMs) {
  if (state_ == nullptr || bridge_ == nullptr) return;
  if (!state_->healthy()) { setStatus("nvs_state_error"); return; }
  const PendingResult pending = state_->pendingResult();
  if (!state_->healthy()) { setStatus("nvs_state_error"); return; }
  if (pending.present) {
    if (static_cast<int32_t>(nowMs - nextResultAttemptAtMs_) >= 0) {
      sendPendingResult(nowMs);
    }
    return;
  }
  const String active = state_->activeJobId();
  if (!active.isEmpty()) {
    const char* giveUp = bridge_->service(nowMs, active);
    if (giveUp != nullptr) {
      // Never wait without a deadline: report the failure and become idle.
      state_->queueRefused(active, giveUp);
      setStatus(giveUp);
      logLine(String(giveUp) + " id=" + active);
      return;
    }
  }
  if (!state_->canPoll()) return;
  if (static_cast<int32_t>(nowMs - nextPollAtMs_) < 0) return;
  nextPollAtMs_ = nowMs + settings_.pollIntervalMs;
  pollOnce(nowMs);
}

String PostOfficeClient::testConnection() {
  String response;
  const int code = get("/health", response);
  if (code == 200) return "health_ok";
  return code > 0 ? "health_http_" + String(code) : statusText_;
}

}  // namespace postoffice
