#!/bin/bash
# Resets can0 after BUS-OFF (e.g. after emergency motor power cut).
# Safe to run from inside the Docker container (--privileged + --net=host).
set -e

ip link set can0 down
ip link set can0 type can bitrate 1000000 restart-ms 100
ip link set can0 up
echo "can0 reset OK"
