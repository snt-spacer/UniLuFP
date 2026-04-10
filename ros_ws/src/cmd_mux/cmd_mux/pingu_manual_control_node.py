
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import Joy

import copy

import numpy as np

class PinguManualControl(Node):
    def __init__(self):
        super().__init__('manual_control_node')

        # Last cmds
        self._last_manual_cmd = Float64MultiArray(data=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]) # (air_bearing(on/off), thrusters(on/off), t1, t2, t3, t4, t5, t6, t7, t8, reaction wheel, shoulder 1, elbow 1, shoulder 2, elbow 2)

        # Button state
        self._x_was_pressed = self._x_was_released = False
        self._permanent_x_press = self._permanent_x_release = False
        self._x = self._x_prev = 0

        # Register subscriber
        self._joy_sub = self.create_subscription(Joy, "joy", self.joy_callback, 1)

        # Register publisher
        self.manual_control_publisher = self.create_publisher(Float64MultiArray, "manual_control_input", 1)


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

        thruster_cmd = np.zeros(15)

        # --- Air Bearings: X Button (Toggle logic) ---
        self._prev_x = copy.copy(self._x)
        self._x = self._buttons[2]
        self._x_was_pressed = (self._prev_x == 0 and self._x == 1)
        
        # Toggle the first index (index 0)
        if self._x_was_pressed:
            self.air_bearing_active = not getattr(self, 'air_bearing_active', False)

        if getattr(self, 'air_bearing_active', False):
            thruster_cmd[0] = 1

        # Left/Right: Left Stick Horizontal (Axis 0)
        if self._axes[0] > 0.1:   # Left
            thruster_cmd[5] += self._axes[0]; thruster_cmd[8] += self._axes[0]
        elif self._axes[0] < -0.1: # Right
            thruster_cmd[4] += self._axes[0]; thruster_cmd[9] += self._axes[0]

        # Forward/Backward: Left Stick Vertical (Axis 1)
        if self._axes[1] > 0.1:   # Forward
            thruster_cmd[2] += self._axes[1]; thruster_cmd[7] += self._axes[1]
        elif self._axes[1] < -0.1: # Backward
            thruster_cmd[3] += self._axes[1]; thruster_cmd[6] += self._axes[1]

        # Rotate CW/CCW: Right Stick Horizontal (Axis 2)
        if self._axes[2] > 0.1:   # CCW
            thruster_cmd[3] += self._axes[2]; thruster_cmd[5] += self._axes[2]; thruster_cmd[7] += self._axes[2]; thruster_cmd[9] += self._axes[2]
        elif self._axes[2] < -0.1: # CW
            thruster_cmd[2] += self._axes[2]; thruster_cmd[4] += self._axes[2]; thruster_cmd[6] += self._axes[2]; thruster_cmd[8] += self._axes[2]

        # Clip values to stay within [-1, 1] and make all of the commands positive
        thruster_cmd = np.abs(np.clip(thruster_cmd, -1.0, 1.0))

        # Publish at the end
        self._last_manual_cmd = Float64MultiArray(data=thruster_cmd.tolist())
        self.manual_control_publisher.publish(self._last_manual_cmd)
        
    
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