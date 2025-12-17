import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from std_msgs.msg import Float32MultiArray
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from geometry_msgs.msg import PoseStamped, TwistStamped

import numpy as np


class PinguMBC(Node):
    """Node for Model-Based Control of Pingu Air Floating Platform."""

    def __init__(self):
        super().__init__('pingu_mbc_node')

        # Declare parameters
        self.declare_parameter('urdf_file', 'pingu.urdf')
        self.declare_parameter('nx', 3)  # state variables (e.g., x, y, theta)
        self.declare_parameter('nu', 8)  # control inputs (e.g., thrusters)

        # Setup parameters
        self.VALVE_CMD_SIZE = 10
        self.BEARING_CMD_SIZE = 2
        self.THRUSTER_CMD_SIZE = 8
        self.nx = self.get_parameter('nx').get_parameter_value().integer_value
        self.nu = self.get_parameter('nu').get_parameter_value().integer_value

        # Setup motion capture QoS
        mocap_qos = rclpy.qos.QoSProfile(depth=10)
        mocap_qos.reliability = rclpy.qos.ReliabilityPolicy.BEST_EFFORT

        # Setup publishers
        # TODO: Change topic names as needed
        self.thruster_command_publisher = self.create_publisher(
            Float32MultiArray, '/spacer_pingu_floating_platform/pingu_valves/input', 10)

        # Setup timer
        timer_period = .1  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info('Pingu MBC node initialized.')

    def update_base_state(self):
        pass

    def update_joint_state(self):
        pass

    def publish_thruster_commands(self, commands):
        """
        Publish thruster commands (0 to 1 PWM) to the ROS topic.
        """
        msg = Float32MultiArray()
        data_array = np.zeros(self.VALVE_CMD_SIZE, dtype=np.float32)
        # The first 2 are for the bearing
        data_array[self.BEARING_CMD_SIZE:] = commands[:self.THRUSTER_CMD_SIZE]
        msg.data = data_array.tolist()
        self.thruster_command_publisher.publish(msg)
        self.get_logger().debug(f'Published thruster commands: {msg.data}')

    def solve(self):
        pass

    def timer_callback(self):
        self.update_joint_state()
        self.solve()
        self.publish_thruster_commands(np.zeros(self.THRUSTER_CMD_SIZE))


def main(args=None):
    rclpy.init(args=args)

    pingu_mbc_node = PinguMBC()

    rclpy.spin(pingu_mbc_node)

    pingu_mbc_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
