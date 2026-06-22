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
        # Index of each joint in the 4-element arm command [LS, LE, RS, RE].
        LS, LE, RS, RE = 0, 1, 2, 3
        ls, le = "left_shoulder_joint", "left_elbow_joint"
        rs, re = "right_shoulder_joint", "right_elbow_joint"

        # Registry of every arm controller this node can drive.
        #   name -> (indices into [LS, LE, RS, RE], joint names, kind)
        # kind:
        #   'trajectory'  -> JointTrajectory goal (command mapped [-1,1] -> joint limits)
        #   'position'    -> Float64MultiArray on /commands (mapped to limits, slew-limited)
        #   'passthrough' -> Float64MultiArray on /commands (raw [-1,1]; effort/velocity)
        self._arm_controllers = {
            # Dual arm (all four joints)
            "dual_arm_trajectory_controller": ([LS, LE, RS, RE], [ls, le, rs, re], "trajectory"),
            "dual_arm_position_controller":   ([LS, LE, RS, RE], [ls, le, rs, re], "position"),
            "dual_arm_velocity_controller":   ([LS, LE, RS, RE], [ls, le, rs, re], "passthrough"),
            "dual_arm_effort_controller":     ([LS, LE, RS, RE], [ls, le, rs, re], "passthrough"),
            # Left arm (shoulder + elbow)
            "left_arm_trajectory_controller": ([LS, LE], [ls, le], "trajectory"),
            "left_arm_position_controller":   ([LS, LE], [ls, le], "position"),
            "left_arm_velocity_controller":   ([LS, LE], [ls, le], "passthrough"),
            "left_arm_effort_controller":     ([LS, LE], [ls, le], "passthrough"),
            # Right arm (shoulder + elbow)
            "right_arm_trajectory_controller": ([RS, RE], [rs, re], "trajectory"),
            "right_arm_position_controller":   ([RS, RE], [rs, re], "position"),
            "right_arm_velocity_controller":   ([RS, RE], [rs, re], "passthrough"),
            "right_arm_effort_controller":     ([RS, RE], [rs, re], "passthrough"),
            # Left single joint
            "left_arm_shoulder_trajectory_controller": ([LS], [ls], "trajectory"),
            "left_arm_shoulder_effort_controller":     ([LS], [ls], "passthrough"),
            "left_arm_elbow_trajectory_controller":    ([LE], [le], "trajectory"),
            "left_arm_elbow_effort_controller":        ([LE], [le], "passthrough"),
            # Right single joint
            "right_arm_shoulder_trajectory_controller": ([RS], [rs], "trajectory"),
            "right_arm_shoulder_effort_controller":     ([RS], [rs], "passthrough"),
            "right_arm_elbow_trajectory_controller":    ([RE], [re], "trajectory"),
            "right_arm_elbow_effort_controller":        ([RE], [re], "passthrough"),
        }

        self._active_controllers = set()
        self._controller_publishers = {}
        self._trajectory_publishers = {}
        self._impedance_desired_pub = self.create_publisher(
            Float64MultiArray,
            '/arm_impedance_controller/desired_position',
            10,
        )

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

    def _map_arm_positions(self, command, indices):
        """Map normalized arm commands in [-1, 1] to each joint's [lower, upper] limit.
        `indices` selects rows of self._arm_position_limits for the active joints."""
        limits = self._arm_position_limits[indices]
        lower, upper = limits[:, 0], limits[:, 1]
        return lower + (np.asarray(command, dtype=np.float64) + 1.0) * (upper - lower) / 2.0

    def _ensure_arm_state(self):
        if self._current_arm_position is None:
            self._current_arm_position = np.zeros(4, dtype=np.float64)

    def _apply_arm_slew_rate(self, indices, target: np.ndarray) -> np.ndarray:
        """Clamp the active joints (selected by `indices`) to max slew rate (rad/s),
        tracking a full 4-joint state so partial controllers don't disturb the others."""
        now = self.get_clock().now().nanoseconds * 1e-9
        target = np.asarray(target, dtype=np.float64)

        if self._current_arm_position is None:
            self._current_arm_position = np.zeros(4, dtype=np.float64)
            self._current_arm_position[indices] = target
            self._last_arm_cmd_time = now
            return target.copy()

        dt = now - self._last_arm_cmd_time
        self._last_arm_cmd_time = now

        cur = self._current_arm_position[indices]
        if dt <= 0.0 or self._arm_position_slew_rate <= 0.0:
            self._current_arm_position[indices] = target
            return target.copy()

        max_delta = self._arm_position_slew_rate * dt
        cur = cur + np.clip(target - cur, -max_delta, max_delta)
        self._current_arm_position[indices] = cur
        return cur.copy()

    def _publish_to_controller(self, controller_name, command):
        if controller_name not in self._controller_publishers:
            self._controller_publishers[controller_name] = self.create_publisher(
                Float64MultiArray,
                f"{controller_name}/commands",
                10,
            )

        command_msg = Float64MultiArray(data=[float(value) for value in command])
        self._controller_publishers[controller_name].publish(command_msg)

    def _publish_joint_trajectory(self, controller_name, joint_names, indices, target: np.ndarray):
        """Send a JointTrajectory goal for the active joints. time_from_start is computed from
        the slew rate so the controller interpolates at the same effective max speed."""
        if controller_name not in self._trajectory_publishers:
            self._trajectory_publishers[controller_name] = self.create_publisher(
                JointTrajectory,
                f"{controller_name}/joint_trajectory",
                10,
            )

        self._ensure_arm_state()
        target = np.asarray(target, dtype=np.float64)

        # Compute how long the move should take based on the slew rate.
        if self._arm_position_slew_rate > 0.0:
            max_dist = float(np.max(np.abs(target - self._current_arm_position[indices])))
            duration_sec = max(max_dist / self._arm_position_slew_rate, 0.05)
        else:
            duration_sec = 1.0

        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = list(joint_names)

        point = JointTrajectoryPoint()
        point.positions = [float(p) for p in target]
        # Explicit velocity limit so the JTC validates against URDF <limit velocity> and
        # interpolates at a bounded speed rather than as fast as the motor allows.
        point.velocities = [float(self._arm_position_slew_rate)] * len(joint_names)
        point.time_from_start = RosDuration(
            sec=int(duration_sec),
            nanosec=int((duration_sec % 1.0) * 1e9),
        )
        msg.points = [point]
        self._trajectory_publishers[controller_name].publish(msg)

        # Track the target so the next call can compute a correct duration.
        self._current_arm_position[indices] = target

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
        # print(f"Received cmd_mux_low_level command: {cmd}")

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
        
        # Publish to arms — drive every active arm controller with its own joint slice.
        # This supports dual-arm, per-arm, and single-joint (shoulder/elbow) controllers,
        # in trajectory, position, or effort/velocity form.
        if self._arms_enabled:
            arm_command = cmd[10:14]  # [left_shoulder, left_elbow, right_shoulder, right_elbow] in [-1, 1]
            for name, (indices, joint_names, kind) in self._arm_controllers.items():
                if name not in self._active_controllers:
                    continue

                sub_cmd = arm_command[indices]
                if kind == "trajectory":
                    target = self._map_arm_positions(sub_cmd, indices)
                    self._publish_joint_trajectory(name, joint_names, indices, target)
                elif kind == "position":
                    target = self._map_arm_positions(sub_cmd, indices)
                    target = self._apply_arm_slew_rate(indices, target)
                    self._publish_to_controller(name, target)
                else:  # passthrough: effort / velocity get the raw [-1, 1] command
                    self._publish_to_controller(name, sub_cmd)
        

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