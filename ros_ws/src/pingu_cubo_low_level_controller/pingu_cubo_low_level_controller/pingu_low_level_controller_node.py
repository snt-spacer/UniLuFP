import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, Bool
from controller_manager_msgs.srv import ListControllers
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration as RosDuration

from rcl_interfaces.msg import ParameterDescriptor
import yaml

import numpy as np

from pingu_cubo_low_level_controller.utils import log_yaml

class PinguLowLevelControllerIndividualThrusterControl(Node):
    def __init__(self, config_file=None):
        super().__init__('pingu_low_level_controller_itc_rw_arms_node')

        # Config file path
        config_file_path_desc = ParameterDescriptor(description="The path to the file containing the configuration.")
        self.declare_parameter("config_file", "", config_file_path_desc)
        self._config_file_path = self.get_parameter("config_file").get_parameter_value().string_value

        with open(self._config_file_path, "r") as file:
            self._pingu_config = yaml.safe_load(file)

        # Print config parameters
        log_yaml(
            self.get_logger(),
            f"Loaded configuration from {self._config_file_path}:",
            self._pingu_config,
        )

        pingu_cfg = self._pingu_config.get("pingu", {})
        self._reaction_wheel_enabled = bool(pingu_cfg.get("reaction_wheel", False))
        self._arms_enabled = bool(pingu_cfg.get("arms", False))

        # Position limits for arm joints: shape (4, 2), order [left_shoulder, left_elbow, right_shoulder, right_elbow]
        raw_limits = pingu_cfg.get("arm_position_limits", [[-np.inf, np.inf]] * 4)
        self._arm_position_limits = np.array(raw_limits, dtype=np.float64)  # (4, 2)

        # Slew-rate limiter for arm position commands (rad/s). 0.0 = disabled.
        self._arm_position_slew_rate = float(pingu_cfg.get("arm_position_slew_rate", 0.0))
        self._current_arm_position = None  # lazily initialized on first command
        self._last_arm_cmd_time = None
        
        self._rw_controller_candidates = [
            "rw_effort_controller",
            "rw_velocity_controller",
        ]
        self._dual_arm_controller_candidates = [
            "dual_arm_effort_controller",
            "dual_arm_velocity_controller",
            "dual_arm_trajectory_controller",
            "dual_arm_position_controller",
        ]
        self._left_arm_controller_candidates = [
            "left_arm_effort_controller",
            "left_arm_velocity_controller",
            "left_arm_position_controller",
        ]
        self._right_arm_controller_candidates = [
            "right_arm_effort_controller",
            "right_arm_velocity_controller",
            "right_arm_position_controller",
        ]

        # Joint names for each trajectory controller (must match pingu_controllers.yaml)
        self._trajectory_controller_joints = {
            "dual_arm_trajectory_controller": [
                "left_shoulder_joint", "left_elbow_joint",
                "right_shoulder_joint", "right_elbow_joint",
            ],
            "actuators_trajectory_controller": [
                "left_shoulder_joint", "left_elbow_joint",
                "right_shoulder_joint", "right_elbow_joint",
                "rw_joint",
            ],
        }

        self._active_controllers = set()
        self._controller_publishers = {}
        self._trajectory_publishers = {}

        self._controller_list_client = self.create_client(
            ListControllers,
            "/controller_manager/list_controllers",
        )
        self._controller_list_timer = self.create_timer(1.0, self._refresh_active_controllers)
        self._controller_list_future = None
                
        # Subscriber
        self.subscriber = self.create_subscription(
            Float64MultiArray, 
            "pingu_low_level", 
            self.cmd_mux_low_level_callback, 
            10
        )
        self.cmd_mux_disarm = self.create_subscription(
            Bool,
            "cmd_mux_disarm",
            self.disarm_callback,
            10,
        )
        self.cmd_mux_arm = self.create_subscription(
            Bool,
            "cmd_mux_arm",
            self.arm_callback,
            10,
        )
        
        # Publisher
        self.thruster_publisher = self.create_publisher(
            Float64MultiArray,
            "minimal_thruster_command_to_px4",
            10
        )
        self.disarm_publisher = self.create_publisher(
            Bool,
            "disarm",
            10,
        )
        self.arm_publisher = self.create_publisher(
            Bool,
            "arm",
            10,
        )
        self._disarm_sent = False
        
        self.thruster_command = np.zeros(8, dtype=np.float32)

    def disarm_callback(self, msg: Bool):
        if msg.data:
            self.disarm_publisher.publish(Bool(data=True))
    
    def arm_callback(self, msg: Bool):
        if msg.data:
            self.arm_publisher.publish(Bool(data=True))

    def _refresh_active_controllers(self):
        if not self._controller_list_client.service_is_ready():
            return

        if self._controller_list_future is not None and not self._controller_list_future.done():
            return

        request = ListControllers.Request()
        self._controller_list_future = self._controller_list_client.call_async(request)
        self._controller_list_future.add_done_callback(self._on_list_controllers_response)

    def _on_list_controllers_response(self, future):
        try:
            response = future.result()
        except Exception as exc:
            self.get_logger().warn(f"Failed to query controllers: {exc}")
            return

        self._active_controllers = {
            controller.name
            for controller in response.controller
            if controller.state == "active"
        }

    def _pick_active_controller(self, candidates):
        for candidate in candidates:
            if candidate in self._active_controllers:
                return candidate
        return None

    def _map_arm_positions(self, command, joint_slice):
        """Map NN arm position commands from [-1, 1] to per-joint [lower, upper] limits."""
        limits = self._arm_position_limits[joint_slice]
        lower, upper = limits[:, 0], limits[:, 1]
        return lower + (np.asarray(command) + 1.0) * (upper - lower) / 2.0

    def _apply_arm_slew_rate(self, target: np.ndarray) -> np.ndarray:
        """Clamp arm position commands to max slew rate (rad/s). Returns the limited command."""
        now = self.get_clock().now().nanoseconds * 1e-9

        if self._current_arm_position is None:
            self._current_arm_position = target.copy()
            self._last_arm_cmd_time = now
            return self._current_arm_position.copy()

        dt = now - self._last_arm_cmd_time
        self._last_arm_cmd_time = now

        if dt <= 0.0 or self._arm_position_slew_rate <= 0.0:
            self._current_arm_position = target.copy()
            return self._current_arm_position.copy()

        max_delta = self._arm_position_slew_rate * dt
        delta = np.clip(target - self._current_arm_position, -max_delta, max_delta)
        self._current_arm_position += delta
        return self._current_arm_position.copy()

    def _publish_to_controller(self, controller_name, command):
        if controller_name not in self._controller_publishers:
            self._controller_publishers[controller_name] = self.create_publisher(
                Float64MultiArray,
                f"{controller_name}/commands",
                10,
            )

        command_msg = Float64MultiArray(data=[float(value) for value in command])
        self._controller_publishers[controller_name].publish(command_msg)

    def _publish_joint_trajectory(self, controller_name, joint_names, target: np.ndarray):
        """Send a JointTrajectory goal. time_from_start is computed from the slew rate so
        the controller interpolates at the same effective max speed as the slew-rate limiter."""
        if controller_name not in self._trajectory_publishers:
            self._trajectory_publishers[controller_name] = self.create_publisher(
                JointTrajectory,
                f"{controller_name}/joint_trajectory",
                10,
            )

        # Compute how long the move should take based on the slew rate.
        if self._current_arm_position is not None and self._arm_position_slew_rate > 0.0:
            max_dist = float(np.max(np.abs(target - self._current_arm_position)))
            duration_sec = max(max_dist / self._arm_position_slew_rate, 0.05)
        else:
            duration_sec = 1.0

        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = list(joint_names)

        point = JointTrajectoryPoint()
        point.positions = [float(p) for p in target]
        point.time_from_start = RosDuration(
            sec=int(duration_sec),
            nanosec=int((duration_sec % 1.0) * 1e9),
        )
        msg.points = [point]
        self._trajectory_publishers[controller_name].publish(msg)

        # Track the target so the next call can compute a correct duration.
        self._current_arm_position = target.copy()

    # def send_disarm_signal(self):
    #     if self._disarm_sent:
    #         return

    #     self.get_logger().info("Sending disarm signal to PX4 thruster node before shutdown")
    #     self.disarmed_publisher.publish(Bool(data=True))
    #     self._disarm_sent = True
        
    def cmd_mux_low_level_callback(self, msg: Float64MultiArray):
        """Callback function for the cmd_mux_low_level topic. It takes the incoming command, processes it, and publishes it to the thruster command topic.
        
        Args:
            msg (Float64MultiArray): The incoming command message from the cmd_mux_low_level. Shape (15,).
        """
        cmd = np.array(msg.data, dtype=np.float32)
        if cmd.size < 15:  # We expect at least 8 for thrusters, 1 for reaction wheel, and 4 for arms
            self.get_logger().warn(f"Received command with invalid size {cmd.size}; expected at least 15 values")
            return

        # self.get_logger().debug(f"Received cmd_mux_low_level command: {cmd}")
        print(f"Received cmd_mux_low_level command: {cmd}")

        # Publish the thruster command
        self.thruster_command = cmd[2:10] # TODO: First two values are for airbearings and thrusters
        # self.get_logger().info(f"Received cmd_mux_low_level command: {msg.data}")
        # self.get_logger().info(f"Processed thruster command: {self.thruster_command}")
        thruster_command_msg = Float64MultiArray(data=self.thruster_command.tolist())
        self.thruster_publisher.publish(thruster_command_msg)

        # Publish to reaction wheel
        if self._reaction_wheel_enabled:
            rw_controller = self._pick_active_controller(self._rw_controller_candidates)
            if rw_controller is not None:
                reaction_wheel_command = cmd[-1]  # Last value is for reaction wheel

                # self.get_logger().info(
                #     f"Processed reaction wheel command for {rw_controller}: {reaction_wheel_command}"
                # )
                self._publish_to_controller(rw_controller, [reaction_wheel_command])
        
        # Publish to arms
        if self._arms_enabled:
            arm_command = cmd[10:14]  # 4 values for arms
            dual_arm_controller = self._pick_active_controller(self._dual_arm_controller_candidates)
            if dual_arm_controller is not None:
                if "trajectory" in dual_arm_controller:
                    arm_command = self._map_arm_positions(arm_command, slice(None))
                    joint_names = self._trajectory_controller_joints[dual_arm_controller]
                    self._publish_joint_trajectory(dual_arm_controller, joint_names, arm_command)
                elif "position" in dual_arm_controller:
                    arm_command = self._map_arm_positions(arm_command, slice(None))
                    arm_command = self._apply_arm_slew_rate(arm_command)
                    self._publish_to_controller(dual_arm_controller, arm_command)
                else:
                    self._publish_to_controller(dual_arm_controller, arm_command)
            else:
                left_arm_controller = self._pick_active_controller(self._left_arm_controller_candidates)
                right_arm_controller = self._pick_active_controller(self._right_arm_controller_candidates)

                if left_arm_controller is not None:
                    left_cmd = arm_command[:2]
                    if "position" in left_arm_controller:
                        left_cmd = self._map_arm_positions(left_cmd, slice(0, 2))
                        left_cmd = self._apply_arm_slew_rate(
                            np.concatenate([left_cmd, self._current_arm_position[2:] if self._current_arm_position is not None else np.zeros(2)])
                        )[:2]

                    # self.get_logger().info(f"Left Arms command {left_cmd}")
                    self._publish_to_controller(left_arm_controller, left_cmd)

                if right_arm_controller is not None:
                    right_cmd = arm_command[2:4]
                    if "position" in right_arm_controller:
                        right_cmd = self._map_arm_positions(right_cmd, slice(2, 4))
                        right_cmd = self._apply_arm_slew_rate(
                            np.concatenate([self._current_arm_position[:2] if self._current_arm_position is not None else np.zeros(2), right_cmd])
                        )[2:]

                    # self.get_logger().info(f"Right Arms command {right_cmd}")
                    self._publish_to_controller(right_arm_controller, right_cmd)
        

def main(args=None):
    rclpy.init(args=args)
    valve_control_node = PinguLowLevelControllerIndividualThrusterControl(config_file=None)
    
    try:
        rclpy.spin(valve_control_node)
    finally:
        # valve_control_node.send_disarm_signal()
        valve_control_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()