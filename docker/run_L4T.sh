#!/bin/bash
xhost +
docker run --name unilufp-ros-deploy-container -it --runtime=nvidia -e "ACCEPT_EULA=Y" --rm --network host --ipc host \
    -v $HOME/.Xauthority:/root/.Xauthority \
    -v ${PWD}/ros_ws/src:/UniLuFP/ros_ws/src/px4_simple \
    -v ${PWD}/CAN_Setup:/UniLuFP/CAN_Setup \
    -e DISPLAY \
    -e "PRIVACY_CONSENT=Y" \
    unilufp-ros-deploy-l4t:latest