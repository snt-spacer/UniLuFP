#!/bin/bash

# Only add delay if script is being run at boot
if [ "$(systemctl is-system-running)" == "starting" ]; then
    sleep 10
fi

# Source ROS2 workspaces
source /opt/ros/humble/setup.bash

# Launch the ros2 control with default controller
source /home/spacer/fp_ws/install/setup.bash
ros2 launch levion_arm_ros2_control ak80_8.launch.py