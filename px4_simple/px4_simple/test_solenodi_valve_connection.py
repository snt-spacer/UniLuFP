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

# Removed unused imports for clarity (Path, Odometry, PoseStamped, Marker)
# import time # Not explicitly used, Clock().now() handles time

from px4_msgs.msg import OffboardControlMode
from px4_msgs.msg import VehicleStatus
from px4_msgs.msg import ActuatorMotors
from px4_msgs.msg import VehicleCommand


class MinimalPublisherPX4(Node):

    def __init__(self):
        super().__init__("minimal_publisher_to_px4")
        # Consider making namespace configurable or using launch files
        self.namespace_prefix = "/px4_1" # Example namespace, CHANGE if needed

        # QoS profiles - Keep BEST_EFFORT for commands/modes to PX4 is standard
        qos_profile_pub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            # TRANSIENT_LOCAL might be okay for commands, but VOLATILE is also common
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1, # Depth 1 is usually sufficient for command topics
        )

        qos_profile_sub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1, # Depth 1 for status topics
        )

        # Subscrivers
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

        # --- Parameters ---
        self.offboard_setpoint_counter = 0
        self.arming_counter = 0
        self.initial_mode_set = False
        self.initial_arm_sent = False
        # Frequency must be > 2 Hz for Offboard mode stability
        timer_period = 0.1  # seconds (50 Hz) -> Increased frequency
        self.timer = self.create_timer(timer_period, self.cmdloop_callback)

        self.nav_state = VehicleStatus.NAVIGATION_STATE_MAX
        self.arming_state = VehicleStatus.ARMING_STATE_INIT


        self.get_logger().info("PX4 Offboard Direct Actuator Controller Initialized")
        # Note: Actual mode switch and arming happen in the timer callback


    def vehicle_status_callback(self, msg):
        # self.get_logger().info(f"NAV_STATE: {msg.nav_state}")
        # self.get_logger().info(f"ARMING_STATE: {msg.arming_state}")
        self.nav_state = msg.nav_state
        self.arming_state = msg.arming_state

    def publish_vehicle_command(self, command, param1=0.0, param2=0.0, param7=0.0):
        msg = VehicleCommand()
        # Use time from the node's clock for consistency
        msg.timestamp = self.get_clock().now().nanoseconds // 1000
        msg.command = command
        msg.param1 = param1
        msg.param2 = param2
        msg.param7 = param7 # Often used for additional options
        msg.target_system = 1 # Default system ID for drone
        msg.target_component = 1 # Default component ID for autopilot
        msg.source_system = 255 # Standard ID for GCS or Companion Computer
        msg.source_component = 1 # Standard ID for path planner/controller component
        msg.from_external = True
        self.publisher_vehicle_command.publish(msg)
        # Limit verbose logging for commands sent frequently
        # self.get_logger().info(
        #     f"Sent command: {command} ({param1}, {param2})"
        # )

    def arm(self):
        self.get_logger().info("Sending Arm command")
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)
        self.initial_arm_sent = True # Mark that we have sent the arm command

    def disarm(self):
        self.get_logger().info("Sending Disarm command")
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 0.0)

    def engage_offboard_mode(self):
        self.get_logger().info("Setting mode to Offboard")
        # Mode 6 corresponds to MAV_MODE_OFFBOARD_ENABLED
        # param1 = 1.0 -> Base mode custom=1
        # param2 = 6.0 -> Sub mode OFFBOARD=6
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)
        self.initial_mode_set = True # Mark that we have requested the mode switch

    # REMOVED: This function tried to set a conflicting main flight mode.
    # def enable_direct_actuator_mode(self):
    #     self.get_logger().info("Enabling direct actuator mode")
    #     self.publish_vehicle_command(
    #         VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
    #         1.0,
    #         7.0,  # This sets a *different* main mode, not what we want
    #     )

    def publish_offboard_control_heartbeat_signal(self):
        """
        Publishes the OffboardControlMode message to enable direct actuator control.
        This needs to be sent continuously (>2Hz) to keep PX4 in Offboard mode
        when direct actuator control is active.
        """
        msg = OffboardControlMode()
        msg.timestamp = self.get_clock().now().nanoseconds // 1000
        msg.position = False
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.thrust_and_torque = False # Set to False if using ActuatorMotors
        msg.direct_actuator = True   # Enable direct actuator control
        self.publisher_offboard_mode.publish(msg)

    def publish_direct_actuator_setpoint(self, u_command):
        """
        Publishes the raw motor commands.
        Assumes u_command is a numpy array [thrust1, thrust2, thrust3, thrust4, ...]
        Values should typically be in the range [-1, 1] or [0, 1] depending on
        PX4 mixer configuration and ESC type. The example calculation splitting
        positive/negative seems specific to a particular setup (maybe bidirectional ESCs?).
        Adjust the normalization and mapping based on your specific hardware.
        """
        actuator_outputs_msg = ActuatorMotors()
        actuator_outputs_msg.timestamp = self.get_clock().now().nanoseconds // 1000

        # --- IMPORTANT: Adjust this mapping based on your PX4 Mixer ---
        # This example assumes MAIN outputs 1-8 are used and splits a
        # single thrust command per axis into two motor outputs (e.g., for tiltrotors or complex mixers)
        # For a standard quadcopter, you usually map directly:
        # control[0] = motor1_thrust
        # control[1] = motor2_thrust
        # control[2] = motor3_thrust
        # control[3] = motor4_thrust
        # Values are typically normalized (-1 to 1 for bidirectional, 0 to 1 for unidirectional)

        # Example mapping (KEEP OR MODIFY AS NEEDED)
        # Normalize assuming max thrust corresponds to '1.5' in input u_command
        # and output range is roughly [-1, 1] for the underlying mixer.
        # Ensure your u_command dimensions match expected input
        if u_command.shape != (1, 8):
             self.get_logger().warn(f"Incorrect u_command shape: {u_command.shape}")
             # Provide default zero command or handle error
             thrust_command = np.zeros(12, dtype=np.float32) # Example size
        else:
            thrust = u_command[0, :] / 1.5  # Normalize based on your system's scaling

            thrust_command = np.zeros(12, dtype=np.float32) # Ensure correct size (up to 16 possible)

            thrust_command[0] = 0.0 if thrust[0] <= 0.0 else thrust[0]
            thrust_command[1] = 0.0 if thrust[0] >= 0.0 else -thrust[0]

            thrust_command[2] = 0.0 if thrust[1] <= 0.0 else thrust[1]
            thrust_command[3] = 0.0 if thrust[1] >= 0.0 else -thrust[1]

            thrust_command[4] = 0.0 if thrust[2] <= 0.0 else thrust[2]
            thrust_command[5] = 0.0 if thrust[2] >= 0.0 else -thrust[2]

            thrust_command[6] = 0.0 if thrust[3] <= 0.0 else thrust[3]
            thrust_command[7] = 0.0 if thrust[3] >= 0.0 else -thrust[3]
            # Assign zeros to other unused motor outputs if needed
            # thrust_command[8:] = 0.0

        # --- End Mapping Section ---

        actuator_outputs_msg.control = thrust_command.flatten() # Ensure it's float32[N]
        # actuator_outputs_msg.reversible_flags = 0 # Set flags if using DShot reversible ESCs

        self.publisher_direct_actuator.publish(actuator_outputs_msg)


    def cmdloop_callback(self):
        """Main command loop running at high frequency."""

        # --- Mode Setting ---
        # Send Offboard mode command periodically initially until confirmed
        if not self.initial_mode_set or self.offboard_setpoint_counter < 10:
            self.engage_offboard_mode()
            # Send some initial heartbeat signals even before confirming mode
            # to prevent immediate fallback if mode switch is slow.
            self.publish_offboard_control_heartbeat_signal()

        # --- Arming ---
        # Arm only after requesting Offboard mode and if not already armed
        # Give it some time after sending the mode command
        if self.initial_mode_set and self.arming_state == VehicleStatus.ARMING_STATE_STANDBY:
            # Attempt arming periodically for a short time
            if not self.initial_arm_sent or self.arming_counter < 20: # Try arming for ~0.4 sec (20 * 0.02s)
                 self.arm()
                 self.arming_counter += 1
            elif not self.initial_arm_sent: # Log if arming wasn't attempted yet
                self.get_logger().warn("Arming not attempted yet, waiting for STANDBY state.")


        # --- Check State and Publish Setpoints ---
        if self.nav_state == VehicleStatus.NAVIGATION_STATE_OFFBOARD:
            # Continuously send the OffboardControlMode msg to keep direct actuator active
            self.publish_offboard_control_heartbeat_signal()

            # Prepare your motor commands
            u_command = np.zeros((1, 8), dtype=np.float32)
            # Example: Spin one motor (adjust index and value as needed)
            # Ensure the value is within the expected range for your mixer/ESCs
            u_command[0, 3] = 0.5 # Example: 50% thrust on motor associated with index 3

            # Publish the direct motor commands
            self.publish_direct_actuator_setpoint(u_command)

        else:
            # If not in offboard mode, maybe stop sending actuator commands
            # or send zero commands to be safe.
            # self.publish_direct_actuator_setpoint(np.zeros((1, 8))) # Optional: Send zero thrust
            if self.initial_mode_set:
                 # Keep trying to engage offboard if we requested it but aren't in it yet
                 self.engage_offboard_mode()
                 self.publish_offboard_control_heartbeat_signal() # Still need heartbeat

        # Increment counter (used for initial command sending)
        if self.offboard_setpoint_counter < 100: # Limit counter to avoid overflow
             self.offboard_setpoint_counter += 1


def main(args=None):
    print("Starting PX4 Offboard Direct Actuator Controller node...")
    rclpy.init(args=args)

    controller_node = MinimalPublisherPX4()

    try:
        rclpy.spin(controller_node)
    except KeyboardInterrupt:
        print("User requested shutdown.")
        # Optional: Send disarm command on shutdown
        if controller_node.arming_state == VehicleStatus.ARMING_STATE_ARMED:
             controller_node.disarm()
             # Give a moment for the command to be sent
             rclpy.spin_once(controller_node, timeout_sec=0.5)
    finally:
        # Clean up resources
        controller_node.destroy_node()
        rclpy.shutdown()
        print("Node shutdown complete.")


if __name__ == "__main__":
    main()