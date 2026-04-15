# Use ROS2 Humble base image
ARG ROS_DISTRO=humble

FROM ros:${ROS_DISTRO}

# Set the working directory to the main folder of your repository
WORKDIR /mnt

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    ffmpeg \
    vim \
    git \
    byobu \
    terminator \
    build-essential \
    python3-vcstool \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# Install ROS 2 packages
RUN apt-get update && apt-get install -y \
    ros-${ROS_DISTRO}-rclpy \
    ros-${ROS_DISTRO}-geometry-msgs \
    ros-${ROS_DISTRO}-joy \
    ros-${ROS_DISTRO}-ackermann-msgs \
    ros-${ROS_DISTRO}-hardware-interface \
    ros-${ROS_DISTRO}-teleop-twist-keyboard \
    ros-${ROS_DISTRO}-rqt*\
    ros-${ROS_DISTRO}-rviz2 \
    ros-${ROS_DISTRO}-joint-state-publisher-gui \
    && rm -rf /var/lib/apt/lists/*

# Install QT dependencies
RUN apt-get update && apt-get install -y \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xkb1 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Source ROS 2 in every shell
SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc

COPY ./requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Github repositories
## Install acados
WORKDIR /mnt
RUN git clone https://github.com/acados/acados.git \
 && cd acados \
 && git submodule update --recursive --init \
 && mkdir -p build \
 && cd build \
 && cmake -DACADOS_WITH_QPOASES=ON .. \
 && make install -j4 \
 && cd ../ \
 && pip install ./interfaces/acados_template \
 && export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:"/mnt/acados/lib" \
 && export ACADOS_SOURCE_DIR="/mnt/acados"

## ROS packages
WORKDIR /mnt/ros_ws/src
COPY ./repositories.yaml .
RUN vcs import --input repositories.yaml --recursive .

# LevionArms
RUN git clone https://github.com/aky-u/LevionArm.git \
 && cd LevionArm \
 && git submodule set-url cubemars_hardware https://github.com/aky-u/cubemars_hardware.git \
 && git submodule set-url leptrino_force_torque https://github.com/aky-u/leptrino_force_torque.git \
 && git submodule update --init --recursive


## Reinforcement Learning
ARG RSL_RL_DEV=true
ARG RSL_RL_PATH="/root/rsl_rl"
ARG RSL_RL_REMOTE="https://github.com/leggedrobotics/rsl_rl.git"
ARG RSL_RL_BRANCH="main"
ARG RSL_RL_COMMIT_SHA="91c7554e67f7f9c39fbcddf46fb42b82c07f4144" # rsl_rl v3.3.0
RUN if [[ "${RSL_RL_DEV,,}" = true ]]; then \
    git clone "${RSL_RL_REMOTE}" "${RSL_RL_PATH}" --branch "${RSL_RL_BRANCH}" && \
    git -C "${RSL_RL_PATH}" reset --hard "${RSL_RL_COMMIT_SHA}" && \
    python3 -m pip install --no-input --no-cache-dir --editable "${RSL_RL_PATH}" ; \
    fi

RUN apt-get update && apt-get install -y \
 && rosdep install --from-paths . --ignore-src -r -y


# Source ROS2 setup
SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc

WORKDIR /mnt/ros_ws
RUN . /opt/ros/humble/setup.sh && colcon build --symlink-install
RUN echo "source /mnt/ros_ws/install/setup.bash" >> ~/.bashrc

WORKDIR /UniLuFP/ros_ws
# Default command
COPY ./ros_entrypoint.sh /
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]