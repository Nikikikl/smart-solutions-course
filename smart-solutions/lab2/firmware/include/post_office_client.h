#pragma once

#include <Arduino.h>

#include "persistent_state.h"
#include "post_office_settings.h"
#include "station_bridge.h"
#include "display_image_job.h"

namespace postoffice {

class PostOfficeClient {
 public:
  void begin(const String& deviceId, PersistentState& state, StationBridge& bridge,
             const char* rootCa, DisplayImageJob* display = nullptr);
  void configure(const Settings& settings);
  void tick(uint32_t nowMs);

  // GET /health only. It never polls or claims a job. Optional outputs return
  // the HTTP status (-1 without a response) and the server's response body.
  String testConnection(int* httpStatus = nullptr, String* responseBody = nullptr);
  String statusText() const { return statusText_; }

 private:
  int postJson(const String& path, const String& payload, String& response);
  int get(const String& path, String& response);
  void pollOnce(uint32_t nowMs);
  void sendPendingResult(uint32_t nowMs);
  bool parseJobResponse(const String& response, Job& job, bool& hasJob,
                        String& refusalReason);
  String endpoint(const String& path) const;
  bool transportReady(String& reason) const;
  void setStatus(const String& value);

  Settings settings_;
  String deviceId_;
  PersistentState* state_ = nullptr;
  StationBridge* bridge_ = nullptr;
  DisplayImageJob* display_ = nullptr;
  const char* rootCa_ = nullptr;
  uint32_t nextPollAtMs_ = 0;
  uint32_t nextResultAttemptAtMs_ = 0;
  String statusText_ = "not configured";
};

}  // namespace postoffice
