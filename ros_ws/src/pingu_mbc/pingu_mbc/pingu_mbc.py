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
    def __init__(self):
        super().__init__('pingu_mbc_node')

        # Declare parameters
        self.declare_parameter('urdf_file', 'pingu.urdf')

        # Get parameters

        # Setup motion capture QoS
        mocap_qos = rclpy.qos.QoSProfile(depth=10)
        mocap_qos.reliability = rclpy.qos.ReliabilityPolicy.BEST_EFFORT

    def update_base_state():
        pass

    def update_joint_state():
        pass

    def publish_thruster_commands():
        pass

    def control_callback(self):
        pass


def main(args=None):
    rclpy.init(args=args)

    pingu_mbc_node = PinguMBC()

    rclpy.spin(pingu_mbc_node)

    pingu_mbc_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
