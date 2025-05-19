import threading
import rclpy
import numpy as np
from rclpy.node import Node
from rclpy.clock import Clock
from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    QoSHistoryPolicy,
    QoSDurabilityPolicy,
)

from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import PoseStamped
from visualization_msgs.msg import Marker

from px4_msgs.msg import OffboardControlMode
from px4_msgs.msg import VehicleStatus
from px4_msgs.msg import ActuatorMotors
from px4_msgs.msg import VehicleCommand

from geometry_msgs.msg import Twist
import time


class MinimalPublisherPX4(Node):

    def __init__(self):
        super().__init__("minimal_publisher_to_px4")

        # Get namespace
        self.namespace = self.declare_parameter('namespace', '').value
        self.namespace_prefix = f'/{self.namespace}' if self.namespace else ''

        # QoS profiles
        qos_profile_pub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=0,
        )

        qos_profile_sub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=0,
        )

        # Subscribers
        self.status_sub = self.create_subscription(
            VehicleStatus,
            f"{self.namespace_prefix}/fmu/out/vehicle_status",
            self.vehicle_status_callback,
            qos_profile_sub,
        )

        # Publishers
        self.publisher_vehicle_command = self.create_publisher(
            VehicleCommand,
            f"{self.namespace_prefix}/fmu/in/vehicle_command",
            qos_profile_pub,
        )

        self.publisher_offboard_mode = self.create_publisher(
            OffboardControlMode,
            f"{self.namespace_prefix}/fmu/in/offboard_control_mode",
            qos_profile_pub,
        )

        self.publisher_direct_actuator = self.create_publisher(
            ActuatorMotors,
            f"{self.namespace_prefix}/fmu/in/actuator_motors",
            qos_profile_pub,
        )

        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',  # Change this if you're using a different topic
            self.cmd_vel_callback,
            0
        )

        self.nav_state = VehicleStatus.NAVIGATION_STATE_MAX

        # Enable direct actuator mode
        self.enable_offboard_control()

        # Must be called before arming
        self.publish_direct_actuator_mode()

    def vehicle_status_callback(self, msg):
        self.nav_state = msg.nav_state

    def disarm(self):
        self.get_logger().info("Disarming vehicle")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
            param1 = 0.0
        )
    def enable_mannual_mode(self):
        self.get_logger().info("Enabling manual mode")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1=1.0,  # Custom mode
            param2=1.0   # PX4 manual mode (main mode = 1)
        )

    def enable_offboard_control(self):
        self.get_logger().info("Enabling offboard control")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1 = 1.0,
            param2 = 6.0,  # Offboard mode
        )

    def publish_direct_actuator_mode(self):
        offboard_msg = OffboardControlMode()
        offboard_msg.timestamp = int(Clock().now().nanoseconds / 1000)
        offboard_msg.position = False
        offboard_msg.velocity = False
        offboard_msg.acceleration = False
        offboard_msg.attitude = False
        offboard_msg.body_rate = False
        offboard_msg.direct_actuator = True
        self.publisher_offboard_mode.publish(offboard_msg)
        self.get_logger().info(f"Publishing direct to: {self.namespace_prefix}")


    def publish_vehicle_command(self, command, **params) -> None:
        """Publish a vehicle command."""
        msg = VehicleCommand()
        msg.command = command
        msg.param1 = params.get("param1", 0.0)
        msg.param2 = params.get("param2", 0.0)
        msg.param3 = params.get("param3", 0.0)
        msg.param4 = params.get("param4", 0.0)
        msg.param5 = params.get("param5", 0.0)
        msg.param6 = params.get("param6", 0.0)
        msg.param7 = params.get("param7", 0.0)
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        self.publisher_vehicle_command.publish(msg)
        self.get_logger().info(f"Publishing offboard to: {self.namespace_prefix}")

    def run(self):
        """Call offboard msg every 0.1 seconds"""
        wait_rate = self.create_rate(1.0)
        while rclpy.ok():
            self.publish_direct_actuator_mode()
            wait_rate.sleep()

    def cmd_vel_callback(self, msg: Twist):
        self.get_logger().info(
            f'Received velocity command: linear=({msg.linear.x}, {msg.linear.y}, {msg.linear.z}) '
            f'angular=({msg.angular.x}, {msg.angular.y}, {msg.angular.z})'
        )

    def on_interupt(self) -> None:
        wait_rate = self.create_rate(2.0)
        self.enable_mannual_mode()
        wait_rate.sleep()
        self.clean_termination()


    def clean_termination(self) -> None:
        """Terminate the node."""
        self.destroy_node()
        rclpy.shutdown()


def main(args=None) -> None:
    import signal
    import sys

    rclpy.init(args=args)
    spacecraft_node = MinimalPublisherPX4()

    spin_thread = threading.Thread(target=rclpy.spin, args=(spacecraft_node,), daemon=True)
    spin_thread.start()

    def signal_handler(sig, frame):
        spacecraft_node.on_interupt()
        spin_thread.join()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)

    spacecraft_node.run()

    spacecraft_node.clean_termination()
    spin_thread.join()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)