import rclpy
import numpy as np
from rclpy.node import Node
from rclpy.clock import Clock
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy

from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import PoseStamped
from visualization_msgs.msg import Marker

from px4_msgs.msg import OffboardControlMode
from px4_msgs.msg import VehicleStatus
from px4_msgs.msg import ActuatorMotors

class MinimalPublisherPX4(Node):

    def __init__(self):
        super().__init__('minimal_publisher_to_px4')
        
        # QoS profiles
        qos_profile_pub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=0
        )

        qos_profile_sub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=0
        )

        self.status_sub = self.create_subscription(
            VehicleStatus,
            f'{self.namespace_prefix}/fmu/out/vehicle_status',
            self.vehicle_status_callback,
            qos_profile_sub)
        
        self.publisher_offboard_mode = self.create_publisher(
            OffboardControlMode,
            f'{self.namespace_prefix}/fmu/in/offboard_control_mode',
            qos_profile_pub)
        
        self.publisher_direct_actuator = self.create_publisher(
            ActuatorMotors,
            f'{self.namespace_prefix}/fmu/in/actuator_motors',
            qos_profile_pub)
        
        timer_period = 0.1  # seconds
        self.timer = self.create_timer(timer_period, self.cmdloop_callback)

        self.nav_state = VehicleStatus.NAVIGATION_STATE_MAX

    def vehicle_status_callback(self, msg):
        self.nav_state = msg.nav_state

    def publish_direct_actuator_setpoint(self, u_command):
        actuator_outputs_msg = ActuatorMotors()
        actuator_outputs_msg.timestamp = int(Clock().now().nanoseconds / 1000)

        # NOTE:
        # Output is float[16]
        # u1 needs to be divided between 1 and 2
        # u2 needs to be divided between 3 and 4
        # u3 needs to be divided between 5 and 6
        # u4 needs to be divided between 7 and 8
        # positve component goes for the first, the negative for the second
        thrust = u_command[0, :] / 1.5  # normalizes w.r.t. max thrust
        # print("Thrust rates: ", thrust[0:4])

        thrust_command = np.zeros(12, dtype=np.float32)
        thrust_command[0] = 0.0 if thrust[0] <= 0.0 else thrust[0]
        thrust_command[1] = 0.0 if thrust[0] >= 0.0 else -thrust[0]

        thrust_command[2] = 0.0 if thrust[1] <= 0.0 else thrust[1]
        thrust_command[3] = 0.0 if thrust[1] >= 0.0 else -thrust[1]

        thrust_command[4] = 0.0 if thrust[2] <= 0.0 else thrust[2]
        thrust_command[5] = 0.0 if thrust[2] >= 0.0 else -thrust[2]

        thrust_command[6] = 0.0 if thrust[3] <= 0.0 else thrust[3]
        thrust_command[7] = 0.0 if thrust[3] >= 0.0 else -thrust[3]

        actuator_outputs_msg.control = thrust_command.flatten()
        self.publisher_direct_actuator.publish(actuator_outputs_msg)


    def cmdloop_callback(self):
        # Publish offboard control modes
        offboard_msg = OffboardControlMode()
        offboard_msg.timestamp = int(Clock().now().nanoseconds / 1000)
        offboard_msg.position = False
        offboard_msg.velocity = False
        offboard_msg.acceleration = False
        offboard_msg.attitude = False
        offboard_msg.body_rate = False
        offboard_msg.direct_actuator = True
        self.publisher_offboard_mode.publish(offboard_msg)

        u_command = np.zeros((1, 12))
        u_command[0, 0] = 1.0
        self.publish_direct_actuator_setpoint(u_command)



def main(args=None):
    rclpy.init(args=args)

    spacecraft_mpc = MinimalPublisherPX4()
    rclpy.spin(spacecraft_mpc)
    spacecraft_mpc.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()