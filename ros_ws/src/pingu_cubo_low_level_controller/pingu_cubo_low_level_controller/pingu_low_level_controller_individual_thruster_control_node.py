from typing import List
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

import numpy as np

class PinguLowLevelControllerIndividualThrusterControl(Node):
    def __init__(self):
        super().__init__('pingu_low_level_controller_individual_thruster_control_node')
                
        # Subscriber
        self.subscriber = self.create_subscription(
            Float32MultiArray, 
            "/cmd_mux_low_level", 
            self.cmd_mux_low_level_callback, 
            10
        )
        
        # Publisher
        self.publisher = self.create_publisher(
            Float32MultiArray,
            "minimal_thruster_command_to_px4",
            10
        )
        
        self.thruster_command = np.zeros(8, dtype=np.float32)
        
    def cmd_mux_low_level_callback(self, msg: Float32MultiArray):
        """Callback function for the cmd_mux_low_level topic. It takes the incoming command, processes it, and publishes it to the thruster command topic.
        
        Args:
            msg (Float32MultiArray): The incoming command message from the cmd_mux_low_level topic.
        """
        # Process the incoming command and convert it to thruster commands
        self.thruster_command = np.array(msg.data, dtype=np.float32)[:8]
        self.reaction_wheel_command = np.array(msg.data, dtype=np.float32)[-1]
        
        # Publish the thruster command
        thruster_command_msg = Float32MultiArray(data=self.thruster_command.tolist())
        self.publisher.publish(thruster_command_msg)
        
        # Publish the reaction wheel command TODO
        
    

def main(args=None):
    rclpy.init(args=args)
    valve_control_node = PinguLowLevelControllerIndividualThrusterControl()
    
    try:
        rclpy.spin(valve_control_node)
    except KeyboardInterrupt:
        pass
    finally:
        valve_control_node.on_shutdown()
        valve_control_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()