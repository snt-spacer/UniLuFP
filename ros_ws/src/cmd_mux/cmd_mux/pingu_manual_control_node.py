
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import Joy

import copy

class PinguManualControl(Node):
    def __init__(self):
        super().__init__('manual_control_node')

        # Last cmds
        self._last_manual_cmd = Float64MultiArray(data=[0,0,0,0,0,0,0,0,0,0]) # (air_bearing(on/off), thrusters(on/off), t1, t2, t3, t4, t5, t6, t7, t8)

        # Button state
        self._x_was_pressed = self._x_was_released = False
        self._permanent_x_press = self._permanent_x_release = False
        self._x = self._x_prev = 0

        # Register subscriber
        self._joy_sub = self.create_subscription(Joy, "joy", self.joy_callback, 1)

        # Register publisher
        self.manual_control_publisher = self.create_publisher(Float64MultiArray, "pingu_cmd_mux/manual_control_input", 1)


    @property
    def x_was_pressed(self) -> bool:
        """Check if the 'D' button was pressed.
        
        Returns:
            bool: True if the 'D' button was pressed, False otherwise.
        """
        if self._permanent_x_press:
            self._permanent_x_press = False
            return True
        else:
            return False
        
    @property
    def x_was_released(self) -> bool:
        """Check if the 'D' button was released.
        
        Returns:
            bool: True if the 'D' button was released, False otherwise.
        """
        if self._permanent_x_release:
            self._permanent_x_release = False
            return True
        else:
            return False
        
    def joy_callback(self, msg):
        self._buttons = msg.buttons
        self._axes = msg.axes

        # Air bearings: X Button
        self._prev_x = copy.copy(self._x)
        self._x = self._buttons[2]
        self._x_was_pressed = self._prev_x == 0 and self._x == 1
        if self._x_was_pressed:
            self._permanent_x_press = True
        self._x_was_released = self._prev_x == 1 and self._x == 0
        if self._x_was_released:
            self._permanent_x_release = True

        if self.x_was_pressed:
            if self._last_manual_cmd.data[0] == 0:
                self._last_manual_cmd = Float64MultiArray(data=[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
                self.manual_control_publisher.publish(self._last_manual_cmd)
            else:
                self._last_manual_cmd = Float64MultiArray(data=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
                self.manual_control_publisher.publish(self._last_manual_cmd)

        """
        Lab Thruster configuration
        """
        # Left/Right: Left Trigger Axis 0
        if self._axes[0] > 0.1: #L
            self._last_manual_cmd = Float64MultiArray(data=[1,0,1,0,0,0,0,1,0,0,0,0,0,0,0])
            self.manual_control_publisher.publish(self._last_manual_cmd)
        elif self._axes[0] < -0.1: #R
            self._last_manual_cmd = Float64MultiArray(data=[1,0,0,1,0,0,1,0,0,0,0,0,0,0,0])
            self.manual_control_publisher.publish(self._last_manual_cmd)
        else:
            self._last_manual_cmd = Float64MultiArray(data=[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
            self.manual_control_publisher.publish(self._last_manual_cmd)

        # Forward/Backward: Left Trigger Axis 1
        if self._axes[1] > 0.1: #F
            self._last_manual_cmd = Float64MultiArray(data=[1,0,0,0,1,0,0,0,0,1,0,0,0,0,0])
            self.manual_control_publisher.publish(self._last_manual_cmd)
        elif self._axes[1] < -0.1: #B
            self._last_manual_cmd = Float64MultiArray(data=[1,0,0,0,0,1,0,0,1,0,0,0,0,0,0])
            self.manual_control_publisher.publish(self._last_manual_cmd)
        else:
            self._last_manual_cmd = Float64MultiArray(data=[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
            self.manual_control_publisher.publish(self._last_manual_cmd)

        # Rotate CW/CCW: Right Trigger Axis 2
        if self._axes[2] > 0.1: #CCW
            self._last_manual_cmd = Float64MultiArray(data=[1,0,0,0,1,0,0,0,1,0,0,0,0,0,0])
            self.manual_control_publisher.publish(self._last_manual_cmd)
        elif self._axes[2] < -0.1: #CW
            self._last_manual_cmd = Float64MultiArray(data=[1,0,0,0,0,1,0,0,0,1,0,0,0,0,0])
            self.manual_control_publisher.publish(self._last_manual_cmd)
        else:
            self._last_manual_cmd = Float64MultiArray(data=[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
            self.manual_control_publisher.publish(self._last_manual_cmd)

        # self.get_logger().info(f"Axes: {self._axes}")
        
    
def main(args=None):
    rclpy.init(args=args)
    manual_control_node = PinguManualControl()
    
    try:
        rclpy.spin(manual_control_node)
    except KeyboardInterrupt:
        pass
    finally:
        manual_control_node.on_shutdown()
        manual_control_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()