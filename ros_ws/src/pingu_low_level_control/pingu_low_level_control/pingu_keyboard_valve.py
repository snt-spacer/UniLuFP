import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from pynput import keyboard
import threading
import time

class KeyboardPublisher(Node):
    """
    For debugging purposes to open/close valves using keyboard input.
    """
    def __init__(self):
        super().__init__('keyboard_publisher')
        self.publisher_ = self.create_publisher(Float32MultiArray, 'pingu_low_level_control/pingu_valves/input', 10)
        self.timer = self.create_timer(1.0 / 50.0, self.timer_callback)  # 50Hz

        # Store key states
        self.keys = ['1','2','3','4','5','6','7','8','9','0']
        self.key_state = {k: 0.0 for k in self.keys}

        # Start the keyboard listener in a separate thread
        listener_thread = threading.Thread(target=self.keyboard_listener, daemon=True)
        listener_thread.start()

    def timer_callback(self):
        msg = Float32MultiArray()
        msg.data = [self.key_state[k] for k in self.keys]
        self.publisher_.publish(msg)

    def keyboard_listener(self):
        def on_press(key):
            try:
                k = key.char
                if k in self.key_state:
                    self.key_state[k] = 1.0
                    print(f"Key {k} pressed")
            except AttributeError:
                pass

        def on_release(key):
            try:
                k = key.char
                if k in self.key_state:
                    self.key_state[k] = 0.0
                    print(f"Key {k} released")
            except AttributeError:
                pass

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

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
