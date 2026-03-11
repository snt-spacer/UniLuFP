#!/bin/bash
xhost +local:docker

docker run --name unilufp-ros-deploy-container -it \
    --privileged \
    --runtime=nvidia \
    -e "ACCEPT_EULA=Y" \
    --rm \
    --network host \
    --ipc host \
    --device /dev/input:/dev/input \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $HOME/.Xauthority:/root/.Xauthority \
    -v ${PWD}/ros_ws/src:/UniLuFP/ros_ws/src \
    -v $HOME/RANS_DeployToRobot:/mnt/ros_ws/src/rans_deploy/RANS_DeployToRobot \
    -v /run/udev:/run/udev \
    -v /dev/bus/usb:/dev/bus/usb \
    -e DISPLAY=${DISPLAY} \
    -e QT_X11_NO_MITSHM=1 \
    -e XAUTHORITY=/root/.Xauthority \
    unilufp-ros-deploy:latest