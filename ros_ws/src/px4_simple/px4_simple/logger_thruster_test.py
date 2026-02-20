import rclpy
from rclpy.node import Node
from geometry_msgs.msg import WrenchStamped
import csv

class WrenchCsvSubscriber(Node):
    def __init__(self):
        super().__init__('wrench_to_csv_node')

        # --- CONFIGURATION ---
        self.topic_name = '/left/force_torque'  
        self.csv_filename = 'wrench_data.csv'   # Name of the output file

        # 1. Open the CSV file and set up the writer
        # We keep the file open for the lifetime of the node to write continuously
        self.csv_file = open(self.csv_filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)

        # 2. Write the header row
        self.csv_writer.writerow([
            'timestamp_sec', 'timestamp_nanosec',
            'force_x', 'force_y', 'force_z',
            'torque_x', 'torque_y', 'torque_z'
        ])

        # 3. Create the subscriber
        self.subscription = self.create_subscription(
            WrenchStamped,
            self.topic_name,
            self.listener_callback,
            10  # QoS profile depth
        )
        
        self.get_logger().info(f"Subscribed to {self.topic_name}. Writing data to {self.csv_filename}...")

    def listener_callback(self, msg):
        """This function runs every time a new message arrives on the topic."""
        
        # Extract timestamp
        sec = msg.header.stamp.sec
        nanosec = msg.header.stamp.nanosec
        
        # Extract Force (Translational)
        fx = msg.wrench.force.x
        fy = msg.wrench.force.y
        fz = msg.wrench.force.z
        
        # Extract Torque (Rotational)
        tx = msg.wrench.torque.x
        ty = msg.wrench.torque.y
        tz = msg.wrench.torque.z

        # Write the data as a new row in the CSV
        self.csv_writer.writerow([sec, nanosec, fx, fy, fz, tx, ty, tz])
        
        # Optional: Flush the buffer to ensure data is written to disk immediately.
        # This is slightly slower but safer if the node crashes unexpectedly.
        # self.csv_file.flush()

    def destroy_node(self):
        """Ensure the CSV file is closed properly when the node shuts down."""
        if not self.csv_file.closed:
            self.csv_file.close()
            self.get_logger().info(f"Successfully closed {self.csv_filename}.")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = WrenchCsvSubscriber()

    try:
        # Spin keeps the node running and listening for messages
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Gracefully handle Ctrl+C
        node.get_logger().info('Keyboard interrupt detected. Shutting down...')
    finally:
        # Clean up the node and ROS 2 context
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()