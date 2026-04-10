# std lib
from typing import List

import threading
import copy

# rclpy lib
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, Bool
from sensor_msgs.msg import Joy

class PinguCmdMux(Node):
    def __init__(self):
        super().__init__('pingu_cmd_mux_node')

        # Register params
        # self.declare_parameter('pub_topic_name', rclpy.Parameter.Type.STRING)

        # Last cmds
        self._last_manual_cmd = Float64MultiArray(data=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
        self._last_autonomous_cmd = Float64MultiArray(data=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])

        # Register subscriber
        self._manual_cmd_sub = self.create_subscription(Float64MultiArray, "manual_control_input", self.manual_cmd_callback, 1)
        self._autonomous_cmd_sub = self.create_subscription(Float64MultiArray, "autonomous_control_input", self.autonomous_cmd_callback, 1)
        self._joy_sub = self.create_subscription(Joy, "joy_control_input", self.joy_callback, 1)

        # Register publisher
        # self.low_level_publisher = self.create_publisher(Float64MultiArray, self.get_parameter("pub_topic_name").value, 1) 
        self.low_level_publisher = self.create_publisher(Float64MultiArray, "pingu_low_level", 1) 
        self.disarm_publisher = self.create_publisher(
            Bool,
            "cmd_mux_disarm",
            10,
        )
        self.arm_publisher = self.create_publisher(
            Bool,
            "cmd_mux_arm",
            10,
        )

        # Button state
        self._y_was_pressed = self._y_was_released = False
        self._permanent_y_press = self._permanent_y_release = False
        self._disarm_pressed_counter = self._arm_pressed_counter = 0
        self._y = self._y_prev = 0
        self._disarm_1 = self._disarm_2 = 0
        self._arm_1 = self._arm_2 = 0

        # Modes
        self._modes = ["manual", "autonomous"]
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
    
    def manual_cmd_callback(self, msg: Float64MultiArray):
        self._last_manual_cmd = msg
        # self.get_logger().info(f"Received manual command: {msg.data}, current mode: {self._current_mode}")
        if self._current_mode == "manual":
            # self.get_logger().info(f"Sending manual command: {msg.data}")
            self.low_level_publisher.publish(msg)
    
    def autonomous_cmd_callback(self, msg: Float64MultiArray):
        self._last_autonomous_cmd = msg
        print(f"Received autonomous command: {msg.data}, current mode: {self._current_mode}")
        self.get_logger().info(f"Received autonomous command: {msg.data}, current mode: {self._current_mode}")
        if self._current_mode == "autonomous":
            self.low_level_publisher.publish(msg)

    def joy_callback(self, msg: Joy):
        self._buttons = msg.buttons
        self._axes = msg.axes

        # Arm Buttons
        self._arm_1 = self._buttons[11]
        self._arm_2 = self._buttons[13]
        if self._arm_1 and self._arm_2:
            self._arm_pressed_counter += 1
        else:
            self._arm_pressed_counter = 0

        if self._arm_pressed_counter > 20:
            self.arm_publisher.publish(Bool(data=True))

        # Disarm Buttons
        self._disarm_1 = self._buttons[12]
        self._disarm_2 = self._buttons[14]
        if self._disarm_1 and self._disarm_2:
            self._disarm_pressed_counter += 1
        else:
            self._disarm_pressed_counter = 0

        if self._disarm_pressed_counter > 10:
            self.disarm_publisher.publish(Bool(data=True))


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
        valve_control_node.get_logger().info("Keyboard interrupt received, shutting down pingu_cmd_mux_node...")
    finally:
        valve_control_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()