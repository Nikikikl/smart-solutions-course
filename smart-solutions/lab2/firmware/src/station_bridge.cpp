#include "station_bridge.h"

#include <ArduinoJson.h>

namespace postoffice {

namespace {
bool reached(uint32_t nowMs, uint32_t atMs) {
  return static_cast<int32_t>(nowMs - atMs) >= 0;
}
}  // namespace

bool StationBridge::begin() {
  return preferences_.begin("lab2bridge", false);
}

bool StationBridge::dispatchJob(const Job& job, uint32_t sentAtMs) {
  const uint32_t sequence = preferences_.getUInt("seq", 0) + 1;
  if (preferences_.putUInt("seq", sequence) != sizeof(uint32_t)) return false;

  // Letters retain the Lab 1 USB fields. Pick-place carries only a predefined
  // routine name; coordinates and actuator commands never cross this boundary.
  JsonDocument document;
  if (strcmp(job.type, "letter") == 0) {
    document["letter"] = String(job.letter);
  } else {
    document["job"] = "pick_place";
    document["routine"] = job.routine;
  }
  document["session"] = "post-office";
  document["seq"] = sequence;
  document["atom_sent_ms"] = sentAtMs;
  document["job_id"] = job.id;

  // Leading newline ends any partial line the host still holds, so a dropped
  // byte earlier on the link cannot corrupt this job line.
  line_ = "\n";
  serializeJson(document, line_);
  line_ += "\n";
  jobId_ = job.id;
  attempts_ = 1;
  acknowledged_ = false;
  nextSendAtMs_ = sentAtMs + kStationAckRetryMs;
  deadlineAtMs_ = sentAtMs + kStationResultTimeoutMs;
  writeLine();
  return true;
}

bool StationBridge::writeLine() {
  // One write call for the whole line; a short write is retried by service().
  const size_t written =
      Serial.write(reinterpret_cast<const uint8_t*>(line_.c_str()), line_.length());
  return written == line_.length();
}

void StationBridge::forget() {
  jobId_ = "";
  line_ = "";
  attempts_ = 0;
  acknowledged_ = false;
}

const char* StationBridge::service(uint32_t nowMs, const String& activeJobId) {
  if (jobId_.isEmpty()) return nullptr;
  if (activeJobId != jobId_) {  // finished, or replaced after a reboot
    forget();
    return nullptr;
  }
  if (!acknowledged_) {
    if (!reached(nowMs, nextSendAtMs_)) return nullptr;
    if (attempts_ >= kStationMaxSendAttempts) {
      forget();
      return "station_no_ack";
    }
    ++attempts_;
    nextSendAtMs_ = nowMs + kStationAckRetryMs;
    writeLine();
    return nullptr;
  }
  if (reached(nowMs, deadlineAtMs_)) {
    forget();
    return "station_result_timeout";
  }
  return nullptr;
}

bool StationBridge::handleResultLine(const String& line, PersistentState& state) {
  JsonDocument document;
  if (deserializeJson(document, line) != DeserializationError::Ok) return false;

  JsonObject ack = document["station_ack"].as<JsonObject>();
  if (!ack.isNull()) {
    const String ackId = ack["id"] | "";
    if (!jobId_.isEmpty() && ackId == jobId_) acknowledged_ = true;
    return true;
  }

  JsonObject result = document["post_office_result"].as<JsonObject>();
  if (result.isNull()) return false;

  const String jobId = result["id"] | "";
  const String status = result["status"] | "";
  if (jobId.isEmpty() || jobId != state.activeJobId()) return true;
  if (status == "done") {
    state.queueDone(jobId);
  } else if (status == "refused") {
    const String reason = result["reason"] | "station_refused";
    state.queueRefused(jobId, reason.substring(0, 160));
  }
  if (jobId == jobId_) forget();
  return true;
}

}  // namespace postoffice
