# std lib
from typing import List

# rclpy lib
import rclpy
from rclpy.node import Node
from rclpy.clock import Clock
from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    QoSHistoryPolicy,
    QoSDurabilityPolicy,
)
from std_msgs.msg import Int16MultiArray, Float32MultiArray
import numpy as np

from px4_msgs.msg import (
    OffboardControlMode,
    VehicleControlMode,
    VehicleStatus,
    ActuatorMotors,
    VehicleCommand,
)

class PinguDirectValveControl(Node):
    def __init__(self):
        """
        Pins (List[int]): (bearing, thrusters(on/off), t1, t2, t3, t4, t5, t6, t7, t8)
        """
        super().__init__('pingu_valve_control_node')
        # Register parameter
        self.register_param()

        self.namespace = self.get_param("namespace")
        self.namespace_prefix = f'/{self.namespace}' if self.namespace else ''
        self.nav_state = VehicleStatus.NAVIGATION_STATE_MAX
        self.pingu_armed = False
        self.armed_counter = 0
        self.thrust_command = np.zeros(12, dtype=np.float32)

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

        # Subscribers
        self.status_sub = self.create_subscription(
            VehicleStatus,
            f"{self.namespace_prefix}/fmu/out/vehicle_status",
            self.vehicle_status_callback,
            qos_profile_sub,
        )
        self.vehicle_control_mode_sub = self.create_subscription(
            VehicleControlMode,
            f"{self.namespace_prefix}/fmu/out/vehicle_control_mode",
            self.vehicle_control_mode_callback,
            qos_profile_sub,
        )
        self.subscriber = self.create_subscription(Float32MultiArray, self.get_param("topic_name"), self.valve_callback, 10)

        timer_period = 0.1  # seconds (10Hz)
        self.timer = self.create_timer(timer_period, self.offboard_loop)

    def _arm(self):
        self.get_logger().info("Attempting to arm Pingu...")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
            param1 = 1.0,
            param2 = 0.0
        )

    def enable_offboard_control(self):
        # self.get_logger().info("Enabling offboard control")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1 = 1.0,
            param2 = 6.0,  # Offboard mode
        )

    def register_param(self):
        """
        Register rosparams.
        """
        self.declare_parameter('topic_name', rclpy.Parameter.Type.STRING)
        self.declare_parameter('namespace', rclpy.Parameter.Type.STRING)
        self.declare_parameter('device', rclpy.Parameter.Type.STRING)
        self.declare_parameter('pins_ids', rclpy.Parameter.Type.INTEGER_ARRAY)
    
    def get_param(self, name):
        """
        Retrieve parameter value given its name.
        Args:
            name (str): name of parameter.
        """
        return self.get_parameter(name).value

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
        msg.target_system = 2
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
    
    def offboard_loop(self):
        """
        Publish offboard control mode.
        """
        self.enable_offboard_control()
        offboard_msg = OffboardControlMode()
        offboard_msg.timestamp = int(Clock().now().nanoseconds / 1000)
        offboard_msg.position = False
        offboard_msg.velocity = False
        offboard_msg.acceleration = False
        offboard_msg.attitude = False
        offboard_msg.body_rate = False
        offboard_msg.direct_actuator = True
        self.publisher_offboard_mode.publish(offboard_msg)
        if not self.pingu_armed:
            self._arm()
            self.armed_counter += 1
        if self.pingu_armed and self.armed_counter <= 1:
            self.get_logger().info("Pingu is armed.")
            self.armed_counter += 1

        if self.nav_state == VehicleStatus.NAVIGATION_STATE_OFFBOARD:
            actuator_outputs_msg = ActuatorMotors()
            actuator_outputs_msg.timestamp = int(Clock().now().nanoseconds / 1000)
            actuator_outputs_msg.control = self.thrust_command.flatten()
            # self.get_logger().info(f"Publishing direct actuator command: {actuator_outputs_msg}")
            self.publisher_direct_actuator.publish(actuator_outputs_msg)
            
    def vehicle_control_mode_callback(self, msg):
        self.pingu_armed = msg.flag_armed

    def valve_callback(self, msg):
        """
        Subscriber callback function.
        Args:
            msg (std_msgs/Float32MultiArray): ros2 message.
        """
        if len(msg.data) < 10:
            self.get_logger().error("Received message with insufficient data.")
            return
        if not self.pingu_armed:
            self.get_logger().warn("Pingu is not armed. Ignoring valve command.")
            return
        if self.nav_state != VehicleStatus.NAVIGATION_STATE_OFFBOARD:
            self.get_logger().warn("Pingu is not in offboard mode. Ignoring valve command.")
            return
        self.get_logger().info(f"Received valve command: {msg.data}")
        self.thrust_command = np.zeros(12, dtype=np.float32)
        self.thrust_command[:8] = np.array(list(msg.data), dtype=np.float32)[2:]

        

def main(args=None):
    rclpy.init(args=args)
    valve_control_node = PinguDirectValveControl()
    
    try:
        rclpy.spin(valve_control_node)
    except KeyboardInterrupt:
        pass
    finally:
        # valve_control_node.on_shutdown()
        valve_control_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()