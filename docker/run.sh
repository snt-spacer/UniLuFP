#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" &>/dev/null && pwd)"

# X11 setup — works on the attached screen and over `ssh -X`.
# Over plain SSH, DISPLAY is empty: fall back to the attached screen's X server
# (auto-detected from /tmp/.X11-unix). The cookie for that GDM session lives in
# /run/user/<uid>/gdm/Xauthority, NOT in ~/.Xauthority.
DISPLAY="${DISPLAY:-:$(ls /tmp/.X11-unix 2>/dev/null | head -n1 | tr -d 'X')}"
if [ -z "${XAUTHORITY}" ]; then
    if [ -f "/run/user/$(id -u)/gdm/Xauthority" ]; then
        XAUTHORITY="/run/user/$(id -u)/gdm/Xauthority"
    else
        XAUTHORITY="${HOME}/.Xauthority"
    fi
fi
echo "Using DISPLAY=${DISPLAY}  XAUTHORITY=${XAUTHORITY}"
DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" xhost +local:docker

# sudo chmod 666 /dev/ttyUSB0
# echo "Starting micro-ROS bridge..."
# docker run -it -d --name microros-bridge --rm -v /dev:/dev --privileged --net=host microros/micro-ros-agent:humble serial --dev /dev/ttyUSB0
# cleanup() {
#     echo "Stopping micro-ROS bridge..."
#     docker kill microros-bridge
#     exit
# }

# trap cleanup SIGINT SIGTERM

## Persist bash history across container restarts
mkdir -p "${SCRIPT_DIR}/.history"

docker run --name unilufp-ros-deploy-container -it \
    --privileged \
    --runtime=nvidia \
    -e "ACCEPT_EULA=Y" \
    --rm \
    --network host \
    --ipc host \
    --device /dev/input:/dev/input \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v ${XAUTHORITY}:/root/.Xauthority \
    -v ${PWD}:/UniLuFP \
    -v /run/udev:/run/udev \
    -v /dev/bus/usb:/dev/bus/usb \
    -v "${SCRIPT_DIR}/.history:/history:rw" \
    -e DISPLAY=${DISPLAY} \
    -e QT_X11_NO_MITSHM=1 \
    -e XAUTHORITY=/root/.Xauthority \
    -e HISTFILE="/history/bash_history" \
    -e HISTCONTROL="ignoredups:erasedups" \
    -e PROMPT_COMMAND="history -a; history -c; history -r" \
    unilufp-ros-deploy:latest

# cleanup