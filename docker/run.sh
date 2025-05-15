#!/bin/bash
docker run --name unilufp-ros-deploy-container -it --privileged --gpus all -e "ACCEPT_EULA=Y" --rm --network host --ipc host \
    -v $HOME/.Xauthority:/root/.Xauthority \
    -v ${PWD}/ros_ws/src:/mnt/src \
    -e DISPLAY \
    -e "PRIVACY_CONSENT=Y" \
    unilufp-ros-deploy:latest