import sys
import math
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtWidgets import QApplication, QWidget

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class JoystickPublisher(Node):
    def __init__(self):
        super().__init__("joystick_publisher")
        self.publisher = self.create_publisher(Twist, "cmd_vel", 10)

    def publish(self, x, y):
        msg = Twist()
        msg.linear.x = y  # Forward/backward
        msg.linear.y = -x  # Left/right
        self.publisher.publish(msg)


class JoystickWidget(QWidget):
    def __init__(self, ros_node):
        super().__init__()
        self.setWindowTitle("Joystick GUI")
        self.setFixedSize(300, 300)
        self.center = QPointF(150, 150)
        self.knob = QPointF(150, 150)
        self.radius = 100
        self.ros_node = ros_node
        self.active = False

        # Update ROS every 100ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_command)
        self.timer.start(100)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.setBrush(QBrush(QColor(230, 230, 230)))
        painter.drawEllipse(self.center, self.radius, self.radius)

        # Knob
        painter.setBrush(QBrush(QColor(100, 100, 250)))
        painter.drawEllipse(self.knob, 20, 20)

    def mousePressEvent(self, event):
        self.active = True
        self.update_knob(event.position())

    def mouseMoveEvent(self, event):
        if self.active:
            self.update_knob(event.position())

    def mouseReleaseEvent(self, event):
        self.active = False
        self.knob = QPointF(self.center)
        self.update()
        self.ros_node.publish(0.0, 0.0)

    def update_knob(self, pos):
        # Vector from center to pointer
        dx = pos.x() - self.center.x()
        dy = pos.y() - self.center.y()

        dist = math.hypot(dx, dy)
        if dist > self.radius:
            scale = self.radius / dist
            dx *= scale
            dy *= scale

        self.knob = QPointF(self.center.x() + dx, self.center.y() + dy)
        self.update()

    def send_command(self):
        dx = self.knob.x() - self.center.x()
        dy = self.knob.y() - self.center.y()

        # Normalize to [-1, 1]
        x = dx / self.radius
        y = -dy / self.radius  # Flip Y for intuitive forward movement

        self.ros_node.publish(x, y)


def main():
    rclpy.init()
    ros_node = JoystickPublisher()

    app = QApplication(sys.argv)
    widget = JoystickWidget(ros_node)
    widget.show()

    def spin_ros():
        rclpy.spin_once(ros_node, timeout_sec=0.01)

    ros_timer = QTimer()
    ros_timer.timeout.connect(spin_ros)
    ros_timer.start(10)

    sys.exit(app.exec())
    rclpy.shutdown()


if __name__ == "__main__":
    main()
