#include "pressure_settings.h"

namespace pressure {

bool SettingsStore::begin() {
  return preferences_.begin("pressure", false);
}

bool SettingsStore::hasStoredCalibration() const {
  return preferences_.isKey("calibrated");
}

Calibration SettingsStore::load() const {
  if (!hasStoredCalibration()) return dataAcquisitionLab2Calibration();
  Calibration calibration;
  calibration.calibrated = preferences_.getBool("calibrated", false);
  if (!calibration.calibrated) return calibration;
  calibration.voltsPerCount = preferences_.getFloat("vPerCount", 0.0f);
  calibration.voltageOffsetV = preferences_.getFloat("vOffset", 0.0f);
  calibration.kpaPerVolt = preferences_.getFloat("kpaPerV", 0.0f);
  calibration.pressureOffsetKpa = preferences_.getFloat("kpaOffset", 0.0f);
  if (!validateCalibration(calibration).ok()) return Calibration{};
  return calibration;
}

bool SettingsStore::save(const Calibration& calibration) {
  if (!validateCalibration(calibration).ok()) return false;
  if (!calibration.calibrated) {
    return preferences_.putBool("calibrated", false) == sizeof(bool);
  }

  // The validity flag is written last so a partial write cannot expose a
  // mixture of old and new coefficients as a calibrated configuration.
  if (preferences_.putBool("calibrated", false) != sizeof(bool)) return false;
  bool ok = preferences_.putFloat("vPerCount", calibration.voltsPerCount) ==
            sizeof(float);
  ok = preferences_.putFloat("vOffset", calibration.voltageOffsetV) ==
           sizeof(float) &&
       ok;
  ok = preferences_.putFloat("kpaPerV", calibration.kpaPerVolt) ==
           sizeof(float) &&
       ok;
  ok = preferences_.putFloat("kpaOffset", calibration.pressureOffsetKpa) ==
           sizeof(float) &&
       ok;
  if (!ok) return false;
  return preferences_.putBool("calibrated", true) == sizeof(bool);
}

}  // namespace pressure
