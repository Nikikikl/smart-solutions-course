#include "pressure_model.h"

#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <cstring>

namespace pressure {
namespace {

constexpr float kMaxVoltsPerCount = 0.002f;
constexpr float kMaxAbsVoltageOffsetV = 0.5f;
constexpr float kMaxAbsKpaPerVolt = 10000.0f;
constexpr float kMaxAbsPressureOffsetKpa = 10000.0f;
constexpr float kMinConvertedVoltageV = -0.5f;
constexpr float kMaxConvertedVoltageV = 5.5f;
constexpr float kMaxAbsConvertedPressureKpa = 10000.0f;

// Data Acquisition Lab 2 values (see docs/atom_page.md for the sources).
constexpr float kDaAdcFullScaleV = 3.70f;
constexpr float kDaStageGain = 1.0f + 10.0f / 54.0f;
constexpr float kDaStageVrefV = 0.69f;
constexpr float kDaSensorSupplyV = 5.0f;
constexpr float kDaSensorSlopePerKpa = 0.0012858f;
constexpr float kDaSensorOffsetRatio = 0.04f;

bool finiteInRange(float value, float minimum, float maximum) {
  return std::isfinite(value) && value >= minimum && value <= maximum;
}

bool parseFiniteFloat(const char* text, float* output) {
  if (text == nullptr || text[0] == '\0' || output == nullptr) return false;
  size_t length = 0;
  for (const char* current = text; *current != '\0'; ++current) {
    if (++length > 32) return false;
    if (*current == ' ' || *current == '\t' || *current == '\r' ||
        *current == '\n') {
      return false;
    }
  }
  errno = 0;
  char* end = nullptr;
  const float parsed = std::strtof(text, &end);
  if (errno == ERANGE || end == text || *end != '\0' || !std::isfinite(parsed)) {
    return false;
  }
  *output = parsed;
  return true;
}

float voltageFor(int rawAdc, const Calibration& calibration) {
  return rawAdc * calibration.voltsPerCount + calibration.voltageOffsetV;
}

float pressureFor(float voltageV, const Calibration& calibration) {
  return voltageV * calibration.kpaPerVolt + calibration.pressureOffsetKpa;
}

}  // namespace

CalibrationResult validateCalibration(const Calibration& calibration) {
  if (!calibration.calibrated) return {CalibrationCode::Ok, "ok"};
  if (!finiteInRange(calibration.voltsPerCount, 0.0f,
                     kMaxVoltsPerCount) ||
      calibration.voltsPerCount == 0.0f) {
    return {CalibrationCode::InvalidVoltsPerCount,
            "invalid_pressure_volts_per_count"};
  }
  if (!finiteInRange(calibration.voltageOffsetV, -kMaxAbsVoltageOffsetV,
                     kMaxAbsVoltageOffsetV)) {
    return {CalibrationCode::InvalidVoltageOffset,
            "invalid_pressure_voltage_offset"};
  }
  if (!finiteInRange(calibration.kpaPerVolt, -kMaxAbsKpaPerVolt,
                     kMaxAbsKpaPerVolt) ||
      calibration.kpaPerVolt == 0.0f) {
    return {CalibrationCode::InvalidKpaPerVolt,
            "invalid_pressure_kpa_per_volt"};
  }
  if (!finiteInRange(calibration.pressureOffsetKpa,
                     -kMaxAbsPressureOffsetKpa,
                     kMaxAbsPressureOffsetKpa)) {
    return {CalibrationCode::InvalidPressureOffset,
            "invalid_pressure_offset"};
  }

  const float voltageAtMinimum = voltageFor(kAdcMinCount, calibration);
  const float voltageAtMaximum = voltageFor(kAdcMaxCount, calibration);
  if (!finiteInRange(voltageAtMinimum, kMinConvertedVoltageV,
                     kMaxConvertedVoltageV) ||
      !finiteInRange(voltageAtMaximum, kMinConvertedVoltageV,
                     kMaxConvertedVoltageV)) {
    return {CalibrationCode::ConvertedVoltageOutOfRange,
            "pressure_voltage_range_invalid"};
  }
  const float pressureAtMinimum = pressureFor(voltageAtMinimum, calibration);
  const float pressureAtMaximum = pressureFor(voltageAtMaximum, calibration);
  if (!finiteInRange(pressureAtMinimum, -kMaxAbsConvertedPressureKpa,
                     kMaxAbsConvertedPressureKpa) ||
      !finiteInRange(pressureAtMaximum, -kMaxAbsConvertedPressureKpa,
                     kMaxAbsConvertedPressureKpa)) {
    return {CalibrationCode::ConvertedPressureOutOfRange,
            "pressure_range_invalid"};
  }
  return {CalibrationCode::Ok, "ok"};
}

Calibration dataAcquisitionLab2Calibration() {
  const float sensorVoltsPerKpa = kDaSensorSupplyV * kDaSensorSlopePerKpa;
  const float sensorZeroV = kDaSensorSupplyV * kDaSensorOffsetRatio;
  Calibration calibration;
  calibration.calibrated = true;
  calibration.voltsPerCount = kDaAdcFullScaleV / kAdcMaxCount;
  calibration.voltageOffsetV = 0.0f;
  // Invert the stage and the sensor: P = (Vout / A + (A - 1) * Vref / A
  // - sensorZeroV) / sensorVoltsPerKpa.
  calibration.kpaPerVolt = 1.0f / (kDaStageGain * sensorVoltsPerKpa);
  calibration.pressureOffsetKpa =
      ((kDaStageGain - 1.0f) * kDaStageVrefV / kDaStageGain - sensorZeroV) /
      sensorVoltsPerKpa;
  return calibration;
}

CalibrationResult parseCalibration(const char* voltsPerCount,
                                   const char* voltageOffsetV,
                                   const char* kpaPerVolt,
                                   const char* pressureOffsetKpa,
                                   Calibration* output) {
  if (output == nullptr) {
    return {CalibrationCode::MalformedValue, "malformed_pressure_settings"};
  }
  Calibration candidate;
  candidate.calibrated = true;
  if (!parseFiniteFloat(voltsPerCount, &candidate.voltsPerCount) ||
      !parseFiniteFloat(voltageOffsetV, &candidate.voltageOffsetV) ||
      !parseFiniteFloat(kpaPerVolt, &candidate.kpaPerVolt) ||
      !parseFiniteFloat(pressureOffsetKpa, &candidate.pressureOffsetKpa)) {
    return {CalibrationCode::MalformedValue, "malformed_pressure_settings"};
  }
  const CalibrationResult validation = validateCalibration(candidate);
  if (!validation.ok()) return validation;
  *output = candidate;
  return validation;
}

Reading convertReading(int rawAdc, const Calibration& calibration) {
  Reading reading;
  reading.rawAdc = rawAdc;
  // A rail code is not accepted as pressure: it commonly means saturation,
  // a short, or an unusable sensor/op-amp operating point.
  if (rawAdc <= kAdcMinCount || rawAdc >= kAdcMaxCount) {
    reading.code = ReadingCode::InvalidRawAdc;
    reading.status = "invalid_raw_adc";
    return reading;
  }
  if (!calibration.calibrated || !validateCalibration(calibration).ok()) {
    reading.code = ReadingCode::NotCalibrated;
    reading.status = "not_calibrated";
    return reading;
  }

  reading.voltageV = voltageFor(rawAdc, calibration);
  if (!finiteInRange(reading.voltageV, kMinConvertedVoltageV,
                     kMaxConvertedVoltageV)) {
    reading.code = ReadingCode::ConvertedVoltageOutOfRange;
    reading.status = "converted_voltage_out_of_range";
    return reading;
  }
  reading.voltageAvailable = true;
  reading.pressureKpa = pressureFor(reading.voltageV, calibration);
  if (!finiteInRange(reading.pressureKpa, -kMaxAbsConvertedPressureKpa,
                     kMaxAbsConvertedPressureKpa)) {
    reading.code = ReadingCode::ConvertedPressureOutOfRange;
    reading.status = "converted_pressure_out_of_range";
    reading.voltageAvailable = false;
    return reading;
  }
  reading.pressureAvailable = true;
  reading.code = ReadingCode::Ok;
  reading.status = "ok";
  return reading;
}

Reading convertSensorReading(int rawAdc, const Calibration& calibration, bool sensorConfirmed) {
  if (sensorConfirmed) return convertReading(rawAdc,calibration);
  Reading reading;
  reading.rawAdc=rawAdc;
  reading.code=ReadingCode::SensorUnconfirmed;
  reading.status="sensor_not_confirmed";
  return reading;
}

}  // namespace pressure
