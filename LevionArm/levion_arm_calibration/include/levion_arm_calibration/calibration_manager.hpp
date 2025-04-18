#ifndef LEVION_ARM__LEVION_ARM_CALIBRATION__CALIBRATION_MANAGER_HPP_
#define LEVION_ARM__LEVION_ARM_CALIBRATION__CALIBRATION_MANAGER_HPP_

#include <rclcpp/rclcpp.hpp>

namespace levion_arm_calibration
{
class CalibrationManager : public rclcpp::Node
{
public:
  CalibrationManager(const rclcpp::NodeOptions &options);
  ~CalibrationManager() = default;
}; // class CalibrationManager
} // namespace levion_arm_calibration

#endif // LEVION_ARM__LEVION_ARM_CALIBRATION__CALIBRATION_MANAGER_HPP_