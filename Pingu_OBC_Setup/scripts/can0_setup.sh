#!/bin/bash

# Only add delay if script is being run at boot
if [ "$(systemctl is-system-running)" == "starting" ]; then
    sleep 10
fi

# Setup can
modprobe mttcan
ip link set can0 type can bitrate 1000000 restart-ms 100
ip link set can0 up