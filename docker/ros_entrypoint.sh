#!/bin/bash
set -e

# setup ros environment
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source "/UniLuFP/ros_ws/install/setup.bash"
cd /mnt
colcon build --symlink-install
source "/mnt/install/setup.bash"
export ROS_DOMAIN_ID=0

exec "$@"