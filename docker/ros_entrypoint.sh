#!/bin/bash
set -e

# Setup ros environment.
# Order matters: underlay (/mnt, third-party deps) first, overlay (/UniLuFP)
# last so the repo's packages take precedence over the image-baked fallbacks.
source /opt/ros/humble/setup.bash
cd /mnt/ros_ws
colcon build --symlink-install
source "/mnt/ros_ws/install/setup.bash"
cd /UniLuFP/ros_ws
colcon build --symlink-install
source "/UniLuFP/ros_ws/install/setup.bash"
export ROS_DOMAIN_ID=0

exec "$@"
