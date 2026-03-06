#!/bin/bash
set -e

# setup ros environment
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source "/UniLuFP/ros_ws/install/setup.bash"
cd /mnt/ros_ws
colcon build --symlink-install
source "/mnt/ros_ws/install/setup.bash"
cd /UniLuFP/ros_ws
export ROS_DOMAIN_ID=0

exec "$@"