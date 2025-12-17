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

        # Setup parameters
        VALVE_CMD_SIZE = 10
        BEARING_CMD_SIZE = 2
        THRUSTER_CMD_SIZE = 8

        # Setup motion capture QoS
        mocap_qos = rclpy.qos.QoSProfile(depth=10)
        mocap_qos.reliability = rclpy.qos.ReliabilityPolicy.BEST_EFFORT

    def update_base_state(self):
        pass

    def update_joint_state(self):
        pass

    def publish_thruster_commands(self, commands):
        msg = Float32MultiArray()
        data_array = np.zeros(self.THRUSTER_CMD_SIZE, dtype=np.float32)
        # The first 2 are for the bearing
        data_array[self.BEARING_CMD_SIZE:] = commands[:self.THRUSTER_CMD_SIZE]
        msg.data = data_array.tolist()
        self.thruster_command_publisher.publish(msg)
        self.get_logger().debug(f'Published thruster commands: {msg.data}')

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
