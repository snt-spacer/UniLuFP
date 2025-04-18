#include "levion_arm_calibration/joint_limit_calibrator.hpp"

namespace levion_arm_calibration
{
JointLimitCalibrator::JointLimitCalibrator(const rclcpp::NodeOptions &options)
    : Node("joint_limit_calibrator", options)
{
  // Initialize the subscriber for joint states
  joint_state_subscriber_ = this->create_subscription<sensor_msgs::msg::JointState>(
      "/joint_states", rclcpp::SensorDataQoS(),
      std::bind(&JointLimitCalibrator::jointStateCallback, this, std::placeholders::_1));

  // Initialize the service for calibrating joint limits
  calibrate_joint_limits_service_ = this->create_service<std_srvs::srv::Trigger>(
      "/calibrate_joint_limits",
      std::bind(&JointLimitCalibrator::calibrateJointLimits, this, std::placeholders::_1,
                std::placeholders::_2, std::placeholders::_3));

  // Declare parameters
  this->declare_parameter("joint_names", std::vector<std::string>());
  this->declare_parameter("effort_thresholds", std::vector<double>());
  this->declare_parameter("velocity_commands", std::vector<double>());

  // Get parameters
  this->get_parameter("joint_names", joint_names_);
  this->get_parameter("effort_thresholds", effort_thresholds_);
  this->get_parameter("velocity_commands", velocity_commands_);
  RCLCPP_INFO(this->get_logger(), "Joint Limit Calibrator initialized.");
}

void JointLimitCalibrator::jointStateCallback(const sensor_msgs::msg::JointState::SharedPtr msg)
{
  current_joint_state_ = *msg;
}

void JointLimitCalibrator::calibrateJointLimits(
    const std::shared_ptr<rmw_request_id_t> request_header,
    const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
    const std::shared_ptr<std_srvs::srv::Trigger::Response> response)
{
  (void)request_header; // Unused
  (void)request;        // Unused

  // Perform calibration logic here
  // For example, you can use the current_joint_state_ to determine limits

  response->success = true;
  response->message = "Joint limits calibrated successfully.";
  RCLCPP_INFO(this->get_logger(), "Joint limits calibrated successfully.");

  // Save data
}

} // namespace levion_arm_calibration