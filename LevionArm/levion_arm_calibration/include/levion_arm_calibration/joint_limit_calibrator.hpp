#ifndef LEVION_ARM__LEVION_ARM_CALIBRATION__JOINT_LIMIT_CALIBRATOR_HPP_
#define LEVION_ARM__LEVION_ARM_CALIBRATION__JOINT_LIMIT_CALIBRATOR_HPP_

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_srvs/srv/trigger.hpp>
#include <string>
#include <vector>

#include "cubemars_hardware/can.hpp"

namespace levion_arm_calibration
{
class JointLimitCalibrator : public rclcpp::Node
{
public:
  JointLimitCalibrator(const rclcpp::NodeOptions &options);
  ~JointLimitCalibrator() = default;

  // subscription callback
  void jointStateCallback(const sensor_msgs::msg::JointState::SharedPtr msg);

  // service callback
  void calibrateJointLimits(const std::shared_ptr<rmw_request_id_t> request_header,
                            const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
                            const std::shared_ptr<std_srvs::srv::Trigger::Response> response);

private:
  // ROS2 node handle
  rclcpp::Node::SharedPtr node_handle_;

  // subscriber for joint states
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_subscriber_;

  // service for calibrating joint limits
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr calibrate_joint_limits_service_;

  // joint state data
  sensor_msgs::msg::JointState current_joint_state_;

  // Send velocity commands to the robot
  void sendVelocityCommands(const std::vector<double> &velocities);

  // Check if the joint limits are reached reading the effort
  bool detectJointLimit(const sensor_msgs::msg::JointState &joint_state);

  // Send command to motors to set zero position
  void setZeroPosition(const std::vector<double> &positions);

  // Parameters
  std::vector<std::string> joint_names_;
  std::vector<double> effort_thresholds_;
  std::vector<double> velocity_commands_;

  // CAN bus interface
  cubemars_hardware::CanSocket can_;
};

} // namespace levion_arm_calibration

#endif // LEVION_ARM__LEVION_ARM_CALIBRATION__JOINT_LIMIT_CALIBRATOR_HPP_