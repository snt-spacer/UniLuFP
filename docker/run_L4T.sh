#!/bin/bash
xhost +
docker run --name unilufp-ros-deploy-container -it --runtime=nvidia -e "ACCEPT_EULA=Y" --rm --network host --ipc host \
    -v $HOME/.Xauthority:/root/.Xauthority \
    -v ${PWD}/ros_ws/src/px4_simple:/UniLuFP/ros_ws/src/px4_simple \
    -v ${PWD}/ros_ws/src/pingu_low_level_control:/UniLuFP/ros_ws/src/pingu_low_level_control \
    -v ${PWD}/ros_ws/src/rw_ros2_control:/UniLuFP/ros_ws/src/rw_ros2_control \
    -v ${PWD}/ros_ws/src/pingu_cmd_mux:/UniLuFP/ros_ws/src/pingu_cmd_mux \
    -v ${PWD}/ros_ws/src/zeroG_pingu_launcher:/UniLuFP/ros_ws/src/zeroG_pingu_launcher \
    -v ${PWD}/CAN_Setup:/UniLuFP/CAN_Setup \
    -e DISPLAY \
    -e "PRIVACY_CONSENT=Y" \
    unilufp-ros-deploy-l4t:latest