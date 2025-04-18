#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QSlider,
    QLabel,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, QTimer

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray


class SmartSlider(QSlider):
    """Custom QSlider that resets value to zero on mouse release."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.publishing_velocity = 0.0

    def mouseReleaseEvent(self, event):
        self.setValue(0)  # Reset to zero
        super().mouseReleaseEvent(event)


class JointVelocityGui(Node):
    def __init__(self, joint_count=6):
        super().__init__("joint_velocity_slider_gui")
        self.joint_count = joint_count

        self.publisher_ = self.create_publisher(
            Float64MultiArray, "forward_velocity_controller/commands", 10
        )

        self.app = QApplication(sys.argv)
        self.window = QWidget()
        self.window.setWindowTitle("Joint Velocity GUI")
        self.layout = QVBoxLayout()

        self.sliders = []

        for i in range(joint_count):
            row = QHBoxLayout()
            label = QLabel(f"Joint {i}")
            slider = SmartSlider(Qt.Horizontal)
            slider.setMinimum(-100)
            slider.setMaximum(100)
            slider.setValue(0)
            slider.setTickInterval(1)
            slider.setTickPosition(QSlider.TicksBelow)
            slider.valueChanged.connect(self.publish_velocities)
            self.sliders.append(slider)
            row.addWidget(label)
            row.addWidget(slider)
            self.layout.addLayout(row)

        self.window.setLayout(self.layout)
        self.window.show()

        # Optional: polling for publishing updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.publish_velocities)
        self.timer.start(20)  # 50Hz

    def publish_velocities(self):
        msg = Float64MultiArray()
        msg.data = [slider.value() * 0.01 for slider in self.sliders]
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    gui_node = JointVelocityGui(joint_count=2)

    try:
        rclpy.spin_once(gui_node, timeout_sec=0.1)
        sys.exit(gui_node.app.exec_())
    except KeyboardInterrupt:
        pass
    finally:
        gui_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
