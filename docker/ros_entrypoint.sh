#!/bin/bash
set -e

# setup ros environment
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source "/UniLuFP/ros_ws/install/setup.bash"
export ROS_DOMAIN_ID=0

# Merge host src directory with container src directory
echo "Merging host src directory with container src directory..."
cp -r /mnt/src/* /UniLuFP/ros_ws/src/

exec "$@"