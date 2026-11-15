#pragma once

#include <Preferences.h>

#include "pressure_model.h"

namespace pressure {

class SettingsStore {
 public:
  bool begin();
  // Until the page saves pressure settings once, load() returns the
  // Data Acquisition Lab 2 defaults. A saved "disabled" state stays disabled.
  Calibration load() const;
  bool hasStoredCalibration() const;
  bool save(const Calibration& calibration);

 private:
  mutable Preferences preferences_;
};

}  // namespace pressure
