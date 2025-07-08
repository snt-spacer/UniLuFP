import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import sys, select, termios, tty
import time

settings = termios.tcgetattr(sys.stdin)

class KeyboardPublisher(Node):
    """
    For debugging purposes to open/close valves using keyboard input.
    """
    def __init__(self):
        super().__init__('keyboard_publisher')
        self.publisher_ = self.create_publisher(Float32MultiArray, 'spacer_pingu_floating_platform/pingu_valves/input', 10)
        self.timer = self.create_timer(1.0 / 50.0, self.timer_callback)  # 50Hz

        # Store key states
        self.keys = ['a','s','1','2','3','4','5','6','7','8']
        self.key_state = {k: 0.0 for k in self.keys}

        # Start the keyboard listener in a separate thread

    def timer_callback(self):  
        key = self.getKey()
        if key in self.keys:
            self.key_state[key] = 1.0 if self.key_state[key] == 0.0 else 0.0
            self.get_logger().info(f'Key {key} toggled to {self.key_state[key]}')

        elif key == '\x03':  # Ctrl+C to exit
            self.get_logger().info('Exiting keyboard listener.')
            rclpy.shutdown()

        msg = Float32MultiArray()
        msg.data = [self.key_state[k] for k in self.keys]
        self.publisher_.publish(msg)
            

    def getKey(self):
        tty.setraw(sys.stdin.fileno())
        select.select([sys.stdin], [], [], 0)
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key

def main(args=None):
    rclpy.init(args=args)
    node = KeyboardPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
