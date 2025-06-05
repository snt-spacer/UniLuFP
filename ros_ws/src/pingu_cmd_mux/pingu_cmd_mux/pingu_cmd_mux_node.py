# std lib
from typing import List

import threading
import copy

# rclpy lib
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import Joy

class PinguCmdMux(Node):
    def __init__(self):
        super().__init__('pingu_cmd_mux_node')

        # Register params
        self.declare_parameter('pub_topic_name', rclpy.Parameter.Type.STRING)

        # Last cmds
        self._last_manual_cmd = Float32MultiArray(data=[0,0,0,0,0,0,0,0,0,0])
        self._last_autonomous_cmd = Float32MultiArray(data=[0,0,0,0,0,0,0,0,0,0])

        # Register subscriber
        self._manual_cmd_sub = self.create_subscription(Float32MultiArray, "manual_control_input", self.manual_cmd_callback, 1)
        self._autonomous_cmd_sub = self.create_subscription(Float32MultiArray, "autonomous_control_input", self.autonomous_cmd_callback, 1)
        self._joy_sub = self.create_subscription(Joy, "joy_control_input", self.joy_callback, 1)

        # Register publisher
        # self.low_level_publisher = self.create_publisher(Float32MultiArray, self.get_parameter("pub_topic_name").value, 1) 
        self.low_level_publisher = self.create_publisher(Float32MultiArray, "input_valve_2", 1) 

        # Button state
        self._y_was_pressed = self._y_was_released = False
        self._permanent_y_press = self._permanent_y_release = False
        self._y = self._y_prev = 0

        # Modes
        self._modes = ["joy", "manual", "autonomous"]
        self._modes_idx = 0
        self._current_mode = self.last_mode = self._modes[self._modes_idx] # Default mode is manual
        self.get_logger().info(f"Current mode: {self._current_mode}")

    @property
    def y_was_pressed(self) -> bool:
        """Check if the 'D' button was pressed.
        
        Returns:
            bool: True if the 'D' button was pressed, False otherwise.
        """
        if self._permanent_y_press:
            self._permanent_y_press = False
            return True
        else:
            return False
        
    @property
    def y_was_released(self) -> bool:
        """Check if the 'D' button was released.
        
        Returns:
            bool: True if the 'D' button was released, False otherwise.
        """
        if self._permanent_y_release:
            self._permanent_y_release = False
            return True
        else:
            return False
    
    def manual_cmd_callback(self, msg: Float32MultiArray):
        self._last_manual_cmd = msg
        if self._current_mode == "manual":
            self.low_level_publisher.publish(msg)
    
    def autonomous_cmd_callback(self, msg: Float32MultiArray):
        self._last_autonomous_cmd = msg
        if self._current_mode == "autonomous":
            self.low_level_publisher.publish(msg)

    def joy_callback(self, msg: Joy):
        self._buttons = msg.buttons

        # Mode: Y Button
        self._prev_y = copy.copy(self._y)
        self._y = self._buttons[3]
        self._y_was_pressed = self._prev_y == 0 and self._y == 1
        if self._y_was_pressed:
            self._permanent_y_press = True
            self._modes_idx = (self._modes_idx + 1) % len(self._modes)
            self._current_mode = self._modes[self._modes_idx]
        self._y_was_released = self._prev_y == 1 and self._y == 0
        if self._y_was_released:
            self._permanent_y_release = True

        if self._current_mode != self.last_mode:
            self.get_logger().info(f"Current mode: {self._current_mode}")
            self.last_mode = self._current_mode

        
        

def main(args=None):
    rclpy.init(args=args)
    valve_control_node = PinguCmdMux()
    
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