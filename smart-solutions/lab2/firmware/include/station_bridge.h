#pragma once

#include <Arduino.h>
#include <Preferences.h>

#include "persistent_state.h"
#include "post_office_model.h"

namespace postoffice {

// USB link to the local station. The ESP32-S3 native USB CDC can drop bytes
// (arduino-esp32 #10836, #9580), so a job line is never trusted to arrive:
// it is resent until the station answers {"station_ack":{"id":...}}, and every
// wait has a deadline. The station deduplicates by job_id, so resends are safe
// (same pattern as the MAVLink command protocol: sender owns timeout + retry).
constexpr uint32_t kStationAckRetryMs = 1500;
constexpr uint8_t kStationMaxSendAttempts = 8;
constexpr uint32_t kStationResultTimeoutMs = 300000;

class StationBridge {
 public:
  bool begin();
  bool dispatchJob(const Job& job, uint32_t sentAtMs);
  bool handleResultLine(const String& line, PersistentState& state);
  // Resends an unacknowledged job and enforces deadlines. Returns a refusal
  // reason when the active job must be given up, otherwise nullptr.
  const char* service(uint32_t nowMs, const String& activeJobId);

 private:
  bool writeLine();
  void forget();

  Preferences preferences_;
  String jobId_;
  String line_;
  uint8_t attempts_ = 0;
  bool acknowledged_ = false;
  uint32_t nextSendAtMs_ = 0;
  uint32_t deadlineAtMs_ = 0;
};

}  // namespace postoffice
