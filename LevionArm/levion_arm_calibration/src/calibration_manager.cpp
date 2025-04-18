#include "levion_arm_calibration/calibration_manager.hpp"

namespace levion_arm_calibration
{
CalibrationManager::CalibrationManager(const rclcpp::NodeOptions &options)
    : Node("calibration_manager", options)
{
  RCLCPP_INFO(this->get_logger(), "Calibration Manager Node Initialized");
} // CalibrationManager
} // namespace levion_arm_calibration