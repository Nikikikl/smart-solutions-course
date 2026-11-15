#include <unity.h>

#include <cstring>
#include <limits>
#include <initializer_list>

#include "post_office_model.h"
#include "pressure_model.h"
#include "bench_tests.h"
#include "display_images.h"

using namespace postoffice;

static Job validJob() {
  Job job;
  std::strcpy(job.id, "example-job-1");
  std::strcpy(job.type, "letter");
  job.letter = 'A';
  job.expiresEpoch = 2000;
  return job;
}

void test_valid_letter_job() {
  TEST_ASSERT_TRUE(validateJob(validJob(), 1000, true).ok());
}

void test_display_image_whitelist_and_resource_sizes() {
  for (const char* id : {"lab2_logo", "lab2_check"}) {
    Job job = validJob();
    std::strcpy(job.type, "display_image");
    std::strcpy(job.imageId, id);
    TEST_ASSERT_TRUE(validateJob(job, 1000, true).ok());
    const auto* image = localdisplay::findImage(id);
    TEST_ASSERT_NOT_NULL(image);
    TEST_ASSERT_EQUAL(256, image->count);
  }
  const auto* logo = localdisplay::findImage("lab2_logo");
  const auto* check = localdisplay::findImage("lab2_check");
  TEST_ASSERT_NOT_EQUAL(0, std::memcmp(logo->pixels, check->pixels, 512));
}

void test_display_image_rejects_unknown_ids() {
  for (const char* id : {"", "unknown", "https://x", "../lab2_logo", "LAB2_LOGO"}) {
    Job job = validJob();
    std::strcpy(job.type, "display_image");
    std::strcpy(job.imageId, id);
    TEST_ASSERT_EQUAL(static_cast<int>(ValidationCode::InvalidImage),
                      static_cast<int>(validateJob(job, 1000, true).code));
  }
  TEST_ASSERT_NULL(localdisplay::findImage(nullptr));
}

void test_display_image_preserves_motion_clock_and_ttl_guards() {
  Job job = validJob();
  std::strcpy(job.type, "display_image");
  std::strcpy(job.imageId, "lab2_logo");
  TEST_ASSERT_FALSE(validateJob(job, 2000, true).ok());
  TEST_ASSERT_FALSE(validateJob(job, 1000, false).ok());
  job.hasDirectMotionData = true;
  TEST_ASSERT_FALSE(validateJob(job, 1000, true).ok());
}

void test_invalid_letter_is_refused() {
  Job job = validJob();
  job.letter = '1';
  TEST_ASSERT_EQUAL(
      static_cast<int>(ValidationCode::InvalidLetter),
      static_cast<int>(validateJob(job, 1000, true).code));
}

void test_valid_pick_place_job() {
  Job job = validJob();
  std::strcpy(job.type, "pick_place");
  std::strcpy(job.routine, "source_to_finished");
  TEST_ASSERT_TRUE(validateJob(job, 1000, true).ok());
}

void test_invalid_pick_place_routine_is_refused() {
  Job job = validJob();
  std::strcpy(job.type, "pick_place");
  std::strcpy(job.routine, "other");
  TEST_ASSERT_EQUAL(
      static_cast<int>(ValidationCode::InvalidRoutine),
      static_cast<int>(validateJob(job, 1000, true).code));
}

void test_unknown_job_is_refused() {
  Job job = validJob();
  std::strcpy(job.type, "move_robot");
  TEST_ASSERT_EQUAL(
      static_cast<int>(ValidationCode::UnknownJob),
      static_cast<int>(validateJob(job, 1000, true).code));
}

void test_direct_motion_is_refused() {
  Job job = validJob();
  job.hasDirectMotionData = true;
  TEST_ASSERT_EQUAL(
      static_cast<int>(ValidationCode::DirectMotionNotAllowed),
      static_cast<int>(validateJob(job, 1000, true).code));
}

void test_expired_job_is_refused() {
  Job job = validJob();
  TEST_ASSERT_EQUAL(
      static_cast<int>(ValidationCode::Expired),
      static_cast<int>(validateJob(job, 2000, true).code));
}

void test_clock_is_required_for_expiration_check() {
  TEST_ASSERT_EQUAL(
      static_cast<int>(ValidationCode::ClockUnavailable),
      static_cast<int>(validateJob(validJob(), 0, false).code));
}

void test_config_requires_https_without_dev_flag() {
  ConfigInput config{"http://127.0.0.1:5001", "test-key", 1000, false};
  TEST_ASSERT_EQUAL(
      static_cast<int>(ConfigCode::HttpRequiresDevMode),
      static_cast<int>(validateConfig(config).code));
  config.allowDevHttp = true;
  TEST_ASSERT_TRUE(validateConfig(config).ok());
}

void test_config_requires_key_and_poll_range() {
  ConfigInput missingKey{"https://example.invalid", "", 1000, false};
  TEST_ASSERT_EQUAL(
      static_cast<int>(ConfigCode::MissingAtomKey),
      static_cast<int>(validateConfig(missingKey).code));
  ConfigInput badInterval{"https://example.invalid", "test-key", 1, false};
  TEST_ASSERT_EQUAL(
      static_cast<int>(ConfigCode::InvalidPollInterval),
      static_cast<int>(validateConfig(badInterval).code));
}

void test_config_rejects_missing_host_and_whitespace() {
  ConfigInput missingHost{"https://", "test-key", 1000, false};
  TEST_ASSERT_EQUAL(
      static_cast<int>(ConfigCode::InvalidServerUrl),
      static_cast<int>(validateConfig(missingHost).code));
  ConfigInput whitespace{"https://example.invalid/path\n", "test-key", 1000, false};
  TEST_ASSERT_EQUAL(
      static_cast<int>(ConfigCode::InvalidServerUrl),
      static_cast<int>(validateConfig(whitespace).code));
}

void test_claim_guard_blocks_second_job_and_duplicate() {
  ClaimGuard guard;
  TEST_ASSERT_TRUE(guard.start("job-1"));
  TEST_ASSERT_FALSE(guard.canPoll());
  TEST_ASSERT_FALSE(guard.start("job-2"));
  TEST_ASSERT_TRUE(guard.isDuplicate("job-1"));
}

void test_result_must_match_active_job_and_ack() {
  ClaimGuard guard;
  TEST_ASSERT_TRUE(guard.start("job-1"));
  TEST_ASSERT_FALSE(guard.queueResult("job-2"));
  TEST_ASSERT_TRUE(guard.queueResult("job-1"));
  TEST_ASSERT_FALSE(guard.canPoll());
  TEST_ASSERT_TRUE(guard.acknowledgeResult("job-1"));
  TEST_ASSERT_TRUE(guard.canPoll());
}

void test_restored_ambiguous_claim_is_not_pollable() {
  ClaimGuard guard;
  guard.restore("ambiguous-job", "");
  TEST_ASSERT_FALSE(guard.canPoll());
  TEST_ASSERT_TRUE(guard.isDuplicate("ambiguous-job"));
}

void test_missing_persisted_claim_restores_as_empty_state() {
  ClaimGuard guard;
  guard.restore("", "");
  TEST_ASSERT_TRUE(guard.canPoll());
  TEST_ASSERT_EQUAL_STRING("", guard.activeJobId());
  TEST_ASSERT_EQUAL_STRING("", guard.pendingResultId());
}

void test_missing_wifi_credentials_start_setup_ap() {
  TEST_ASSERT_EQUAL(
      static_cast<int>(WifiStartupMode::SetupAccessPoint),
      static_cast<int>(wifiStartupMode(false)));
}

void test_saved_wifi_credentials_attempt_station_connection() {
  TEST_ASSERT_EQUAL(
      static_cast<int>(WifiStartupMode::StationAttempt),
      static_cast<int>(wifiStartupMode(true)));
}

void test_station_attempt_waits_before_timeout() {
  TEST_ASSERT_FALSE(shouldFallbackToSetupAccessPoint(false, kWifiStaTimeoutMs - 1));
  TEST_ASSERT_FALSE(shouldFallbackToSetupAccessPoint(true, kWifiStaTimeoutMs));
}

void test_station_timeout_falls_back_to_setup_ap() {
  TEST_ASSERT_TRUE(shouldFallbackToSetupAccessPoint(false, kWifiStaTimeoutMs));
}

void test_wifi_recovery_enters_fallback_after_initial_timeout() {
  TEST_ASSERT_EQUAL(
      static_cast<int>(WifiRecoveryAction::EnterFallback),
      static_cast<int>(wifiRecoveryAction(false, true, false, kWifiStaTimeoutMs,
                                          false)));
}

void test_wifi_recovery_waits_for_retry_timer() {
  TEST_ASSERT_EQUAL(
      static_cast<int>(WifiRecoveryAction::None),
      static_cast<int>(wifiRecoveryAction(true, false, false, 0, false)));
  TEST_ASSERT_EQUAL(
      static_cast<int>(WifiRecoveryAction::StartRetry),
      static_cast<int>(wifiRecoveryAction(true, false, false, 0, true)));
}

void test_wifi_recovery_success_stops_retry() {
  TEST_ASSERT_EQUAL(
      static_cast<int>(WifiRecoveryAction::RetrySucceeded),
      static_cast<int>(wifiRecoveryAction(true, true, true, 1000, false)));
}

void test_failed_wifi_retry_returns_to_fallback_wait() {
  TEST_ASSERT_EQUAL(
      static_cast<int>(WifiRecoveryAction::RetryTimedOut),
      static_cast<int>(wifiRecoveryAction(true, true, false, kWifiStaTimeoutMs,
                                          false)));
}

static pressure::Calibration validPressureCalibration() {
  // Synthetic arithmetic fixture only; these are not lab calibration values.
  pressure::Calibration calibration;
  calibration.calibrated = true;
  calibration.voltsPerCount = 0.001f;
  calibration.voltageOffsetV = 0.0f;
  calibration.kpaPerVolt = 100.0f;
  calibration.pressureOffsetKpa = -10.0f;
  return calibration;
}

void test_pressure_uncalibrated_state_never_invents_converted_values() {
  const pressure::Reading reading =
      pressure::convertReading(1234, pressure::Calibration{});
  TEST_ASSERT_EQUAL(static_cast<int>(pressure::ReadingCode::NotCalibrated),
                    static_cast<int>(reading.code));
  TEST_ASSERT_EQUAL_INT(1234, reading.rawAdc);
  TEST_ASSERT_FALSE(reading.voltageAvailable);
  TEST_ASSERT_FALSE(reading.pressureAvailable);
  TEST_ASSERT_EQUAL_STRING("not_calibrated", reading.status);
}

void test_pressure_valid_calibration_converts_raw_voltage_and_kpa() {
  const pressure::Reading reading =
      pressure::convertReading(1000, validPressureCalibration());
  TEST_ASSERT_TRUE(reading.ok());
  TEST_ASSERT_TRUE(reading.voltageAvailable);
  TEST_ASSERT_TRUE(reading.pressureAvailable);
  TEST_ASSERT_FLOAT_WITHIN(0.0001f, 1.0f, reading.voltageV);
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 90.0f, reading.pressureKpa);
}

void test_pressure_data_acquisition_defaults_are_valid() {
  const pressure::Calibration defaults =
      pressure::dataAcquisitionLab2Calibration();
  TEST_ASSERT_TRUE(defaults.calibrated);
  TEST_ASSERT_TRUE(pressure::validateCalibration(defaults).ok());
  // 957 counts = 0.865 V, the G5 multimeter reading at atmosphere (15.11).
  const pressure::Reading reading = pressure::convertReading(957, defaults);
  TEST_ASSERT_TRUE(reading.ok());
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.8647f, reading.voltageV);
  TEST_ASSERT_FLOAT_WITHIN(0.1f, 99.14f, reading.pressureKpa);
}

void test_pressure_invalid_coefficients_fail_closed() {
  pressure::Calibration calibration = validPressureCalibration();
  calibration.voltsPerCount = 0.0f;
  TEST_ASSERT_FALSE(pressure::validateCalibration(calibration).ok());
  calibration = validPressureCalibration();
  calibration.kpaPerVolt = 0.0f;
  TEST_ASSERT_FALSE(pressure::validateCalibration(calibration).ok());
  calibration = validPressureCalibration();
  calibration.pressureOffsetKpa =
      std::numeric_limits<float>::quiet_NaN();
  TEST_ASSERT_FALSE(pressure::validateCalibration(calibration).ok());
}

void test_pressure_parser_accepts_complete_bounded_calibration() {
  pressure::Calibration calibration;
  const pressure::CalibrationResult result = pressure::parseCalibration(
      "0.001", "0", "100", "-10", &calibration);
  TEST_ASSERT_TRUE(result.ok());
  TEST_ASSERT_TRUE(calibration.calibrated);
  TEST_ASSERT_FLOAT_WITHIN(0.000001f, 0.001f, calibration.voltsPerCount);
  TEST_ASSERT_FLOAT_WITHIN(0.001f, -10.0f, calibration.pressureOffsetKpa);
}

void test_pressure_parser_rejects_malformed_input_without_changing_previous() {
  pressure::Calibration calibration = validPressureCalibration();
  const pressure::CalibrationResult result = pressure::parseCalibration(
      "0.001junk", "0", "100", "-10", &calibration);
  TEST_ASSERT_FALSE(result.ok());
  TEST_ASSERT_FLOAT_WITHIN(0.000001f, 0.001f, calibration.voltsPerCount);
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 100.0f, calibration.kpaPerVolt);
  TEST_ASSERT_FALSE(pressure::parseCalibration(
                        "0.000000000000000000000000000000001", "0", "100",
                        "-10", &calibration)
                        .ok());
}

void test_pressure_invalid_raw_adc_is_error_not_pressure() {
  const pressure::Reading reading =
      pressure::convertReading(4095, validPressureCalibration());
  TEST_ASSERT_EQUAL(static_cast<int>(pressure::ReadingCode::InvalidRawAdc),
                    static_cast<int>(reading.code));
  TEST_ASSERT_FALSE(reading.voltageAvailable);
  TEST_ASSERT_FALSE(reading.pressureAvailable);
  TEST_ASSERT_EQUAL(
      static_cast<int>(pressure::ReadingCode::InvalidRawAdc),
      static_cast<int>(
          pressure::convertReading(0, validPressureCalibration()).code));
}

int main(int argc, char** argv) {
  UNITY_BEGIN();
  RUN_TEST(test_bench_is_default_without_build_flag);
  RUN_TEST(test_bench_starts_only_local_services_with_stored_jobs);
  RUN_TEST(test_bench_ap_failure_has_no_unprotected_or_sta_fallback);
  RUN_TEST(test_bench_get_endpoints_are_read_only);
  RUN_TEST(test_bench_blocks_save_health_jobs_and_serial_routes);
  RUN_TEST(test_bench_unknown_and_non_post_methods_cannot_enable_execution);
  RUN_TEST(test_bench_only_pressure_post_can_sample_local_input);
  RUN_TEST(test_bench_password_valid_synthetic_bytes_and_entropy_order);
  RUN_TEST(test_bench_password_rejects_zero_and_all_constant_buffers);
  RUN_TEST(test_bench_password_rejects_repeating_and_counting_patterns);
  RUN_TEST(test_bench_password_rejects_malformed_buffers);
  RUN_TEST(test_bench_entropy_failure_disables_source_and_clears_output);
  RUN_TEST(test_bench_unwritten_rng_buffer_is_rejected);
  RUN_TEST(test_bench_bad_entropy_stops_before_ap_and_http_start);
  RUN_TEST(test_valid_letter_job);
  RUN_TEST(test_display_image_whitelist_and_resource_sizes);
  RUN_TEST(test_display_image_rejects_unknown_ids);
  RUN_TEST(test_display_image_preserves_motion_clock_and_ttl_guards);
  RUN_TEST(test_invalid_letter_is_refused);
  RUN_TEST(test_valid_pick_place_job);
  RUN_TEST(test_invalid_pick_place_routine_is_refused);
  RUN_TEST(test_unknown_job_is_refused);
  RUN_TEST(test_direct_motion_is_refused);
  RUN_TEST(test_expired_job_is_refused);
  RUN_TEST(test_clock_is_required_for_expiration_check);
  RUN_TEST(test_config_requires_https_without_dev_flag);
  RUN_TEST(test_config_requires_key_and_poll_range);
  RUN_TEST(test_config_rejects_missing_host_and_whitespace);
  RUN_TEST(test_claim_guard_blocks_second_job_and_duplicate);
  RUN_TEST(test_result_must_match_active_job_and_ack);
  RUN_TEST(test_restored_ambiguous_claim_is_not_pollable);
  RUN_TEST(test_missing_persisted_claim_restores_as_empty_state);
  RUN_TEST(test_missing_wifi_credentials_start_setup_ap);
  RUN_TEST(test_saved_wifi_credentials_attempt_station_connection);
  RUN_TEST(test_station_attempt_waits_before_timeout);
  RUN_TEST(test_station_timeout_falls_back_to_setup_ap);
  RUN_TEST(test_wifi_recovery_enters_fallback_after_initial_timeout);
  RUN_TEST(test_wifi_recovery_waits_for_retry_timer);
  RUN_TEST(test_wifi_recovery_success_stops_retry);
  RUN_TEST(test_failed_wifi_retry_returns_to_fallback_wait);
  RUN_TEST(test_pressure_uncalibrated_state_never_invents_converted_values);
  RUN_TEST(test_pressure_valid_calibration_converts_raw_voltage_and_kpa);
  RUN_TEST(test_pressure_data_acquisition_defaults_are_valid);
  RUN_TEST(test_pressure_invalid_coefficients_fail_closed);
  RUN_TEST(test_pressure_parser_accepts_complete_bounded_calibration);
  RUN_TEST(test_pressure_parser_rejects_malformed_input_without_changing_previous);
  RUN_TEST(test_pressure_invalid_raw_adc_is_error_not_pressure);
  return UNITY_END();
}
