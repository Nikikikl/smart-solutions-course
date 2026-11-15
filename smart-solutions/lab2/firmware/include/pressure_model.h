#pragma once

#include <stdint.h>

namespace pressure {

constexpr int kAdcMinCount = 0;
constexpr int kAdcMaxCount = 4095;

struct Calibration {
  bool calibrated = false;
  float voltsPerCount = 0.0f;
  float voltageOffsetV = 0.0f;
  float kpaPerVolt = 0.0f;
  float pressureOffsetKpa = 0.0f;
};

enum class CalibrationCode : uint8_t {
  Ok,
  InvalidVoltsPerCount,
  InvalidVoltageOffset,
  InvalidKpaPerVolt,
  InvalidPressureOffset,
  ConvertedVoltageOutOfRange,
  ConvertedPressureOutOfRange,
  MalformedValue,
};

struct CalibrationResult {
  CalibrationCode code;
  const char* reason;
  bool ok() const { return code == CalibrationCode::Ok; }
};

CalibrationResult validateCalibration(const Calibration& calibration);

// Default conversion from the documented Data Acquisition Lab 2 chain:
// G5 ADC 3.70 V / 4095, LM358N stage Vout = A * Vin - (A - 1) * Vref with
// A = 1 + 10k / 54k and Vref = 0.69 V, and the MPX5700AP datasheet transfer
// Vin = 5.0 V * (0.0012858 * P + 0.04). Pressure is absolute kPa. These are
// editable defaults, not a reference-pressure calibration.
Calibration dataAcquisitionLab2Calibration();

// Parses all four fields as one unit and changes output only after complete
// validation. Values from Data Acquisition Lab 2 can therefore replace the
// uncalibrated defaults without changing firmware code.
CalibrationResult parseCalibration(const char* voltsPerCount,
                                   const char* voltageOffsetV,
                                   const char* kpaPerVolt,
                                   const char* pressureOffsetKpa,
                                   Calibration* output);

enum class ReadingCode : uint8_t {
  Ok,
  NotCalibrated,
  InvalidRawAdc,
  ConvertedVoltageOutOfRange,
  ConvertedPressureOutOfRange,
  SensorUnconfirmed,
};

struct Reading {
  ReadingCode code = ReadingCode::NotCalibrated;
  const char* status = "not_calibrated";
  int rawAdc = 0;
  bool voltageAvailable = false;
  float voltageV = 0.0f;
  bool pressureAvailable = false;
  float pressureKpa = 0.0f;
  bool ok() const { return code == ReadingCode::Ok; }
};

Reading convertReading(int rawAdc, const Calibration& calibration);
Reading convertSensorReading(int rawAdc, const Calibration& calibration, bool sensorConfirmed);

}  // namespace pressure
