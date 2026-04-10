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
from std_msgs.msg import Float64MultiArray, Bool
from geometry_msgs.msg import PoseStamped
from visualization_msgs.msg import Marker

from px4_msgs.msg import OffboardControlMode
from px4_msgs.msg import VehicleStatus
from px4_msgs.msg import ActuatorMotors
from px4_msgs.msg import VehicleCommand


import time


class MinimalThrusterPublisherPX4(Node):
    """
    Takes a 8D command input and publishes it to PX4 in direct actuator control mode.
    """

    def __init__(self):
        super().__init__("minimal_thruster_publisher_to_px4_node")
        
        # Get namespace
        self.namespace = self.declare_parameter('namespace', '').value
        self.namespace_prefix = f'/{self.namespace}' if self.namespace else ''

        # QoS profiles
        qos_profile_pub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )

        qos_profile_sub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # Subscribers
        self.status_sub = self.create_subscription(
            VehicleStatus,
            f"{self.namespace_prefix}/fmu/out/vehicle_status",
            self.vehicle_status_callback,
            qos_profile_sub,
        )
        
        self.command_sub = self.create_subscription(
            Float64MultiArray, 
            f"{self.namespace_prefix}/minimal_thruster_command_to_px4", 
            self.process_command_callback, 
            10
        )

        self.disarm_sub = self.create_subscription(
            Bool,
            f"{self.namespace_prefix}/disarm",
            self.disarm_callback,
            10,
        )
        self.arm_sub = self.create_subscription(
            Bool,
            f"{self.namespace_prefix}/arm",
            self.arm_callback,
            10,
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

        self.shutdown_requested = False
        timer_period = 0.1  # seconds
        self.timer = self.create_timer(timer_period, self.cmdloop_callback)

        self.nav_state = VehicleStatus.NAVIGATION_STATE_OFFBOARD

        # Enable direct actuator mode
        self.enable_offboard_control()
        # self.enable_direct_actuator_mode()

        # Must be called before arming
        self.publish_direct_actuator_mode()

        # Enable arm
        self.arm()
        
        self.shutdown_counter = 0
        self.u_command = np.zeros((1, 8))

    def arm(self):
        self.get_logger().info("Arming vehicle")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
            param1 = 1.0,
            param2 = 0.0
        )

    def disarm(self):
        self.get_logger().info("Disarming vehicle")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
            param1 = 0.0
        )

    def disarm_callback(self, msg: Bool):
        if msg.data:
            self.initiate_shutdown()

    def arm_callback(self, msg: Bool):
        if msg.data:
            # Enable direct actuator mode
            self.enable_offboard_control()
            # self.enable_direct_actuator_mode()

            # Must be called before arming
            self.publish_direct_actuator_mode()

            # Enable arm
            self.arm()

    def enable_offboard_control(self):
        self.get_logger().info("Enabling offboard control")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1 = 1.0,
            param2 = 6.0,  # Offboard mode
        )

    def enable_mannual_mode(self):
        self.get_logger().info("Enabling manual mode")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1=1.0,  # Custom mode
            param2=1.0   # PX4 manual mode (main mode = 1)
        )

    def enable_direct_actuator_mode(self):
        self.get_logger().info("Enabling direct actuator mode")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1 = 1.0,
            param2 = 7.0,  # Direct actuator mode
        )

    def vehicle_status_callback(self, msg):
        self.nav_state = msg.nav_state

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
        # self.get_logger().info(
        #     f"Sent command: {command}, \
        #     param1: {params.get('param1', 0.0)}, \
        #     param2: {params.get('param2', 0.0)}, \
        #     param3: {params.get('param3', 0.0)}, \
        #     param4: {params.get('param4', 0.0)}, \
        #     param5: {params.get('param5', 0.0)}, \
        #     param6: {params.get('param6', 0.0)}, \
        #     param7: {params.get('param7', 0.0)}"
        # )

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
        # self.get_logger().info("Sent direct actuator mode")

    def publish_direct_actuator_setpoint(self, u_command):
        actuator_outputs_msg = ActuatorMotors()
        actuator_outputs_msg.timestamp = int(Clock().now().nanoseconds / 1000)
        
        thrust_command = np.zeros(12, dtype=np.float32)
        thrust_command[:8] = u_command.squeeze()
        
        actuator_outputs_msg.control = thrust_command.flatten()
        self.publisher_direct_actuator.publish(actuator_outputs_msg)
        
    def process_command_callback(self, msg: Float64MultiArray):
        # Convert the incoming command to a numpy array
        command_array = np.array(msg.data, dtype=np.float32).reshape(1, -1)
        self.u_command = command_array
        # self.get_logger().info(f"Received command: {command_array}")

    def cmdloop_callback(self):
    
        self.publish_direct_actuator_mode()

        if self.nav_state == VehicleStatus.NAVIGATION_STATE_OFFBOARD:
            self.publish_direct_actuator_setpoint(self.u_command)

        # Begin disarm sequence on external trigger
        if self.shutdown_requested:
            self.shutdown_counter += 1

            if self.shutdown_counter == 5:
                self.enable_mannual_mode()

            elif self.shutdown_counter == 10:
                self.disarm()
                self.shutdown_requested = False

            # elif self.shutdown_counter > 20:
            #     self.get_logger().info("Shutting down...")
            #     rclpy.shutdown()

    def initiate_shutdown(self):
        if not self.shutdown_requested:
            self.get_logger().info("Shutdown requested, starting disarm sequence...")
            self.shutdown_requested = True
            self.shutdown_counter = 0

def main(args=None):
    rclpy.init(args=args)

    spacecraft_low_level_controller = MinimalThrusterPublisherPX4()

    try:
        rclpy.spin(spacecraft_low_level_controller)
    except KeyboardInterrupt:
        spacecraft_low_level_controller.get_logger().info("Keyboard interrupt received, disarming PX4 and shutting down...")
        spacecraft_low_level_controller.initiate_shutdown()
    finally:
        spacecraft_low_level_controller.destroy_node()

if __name__ == "__main__":
    main()