# Use ROS2 Humble base image
FROM ros:humble

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
    ros-humble-rclpy \
    ros-humble-geometry-msgs \
    ros-humble-joy \
    ros-humble-ackermann-msgs \
    ros-humble-hardware-interface \
    ros-humble-teleop-twist-keyboard \
    ros-humble-rqt*\
    ros-humble-rviz2 \
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
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

COPY ./requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Github repositories
WORKDIR /UniLuFP

# =========================
# Acados
# =========================
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

# =========================
# Pinocchio installation
# =========================
# Add robotpkg repository and install Pinocchio (C++ & Python bindings)
RUN set -eux; \
    mkdir -p /etc/apt/keyrings; \
    curl -fsSL http://robotpkg.openrobots.org/packages/debian/robotpkg.asc -o /etc/apt/keyrings/robotpkg.asc; \
    codename=$(lsb_release -cs); \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/robotpkg.asc] http://robotpkg.openrobots.org/packages/debian/pub ${codename} robotpkg" \
      > /etc/apt/sources.list.d/robotpkg.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        robotpkg-eigen3 \
        robotpkg-py3*-pinocchio; \
    apt-get autoremove -y; \
    rm -rf /var/lib/apt/lists/*

# Environment Variables
ENV PATH=/opt/openrobots/bin:$PATH \
    PKG_CONFIG_PATH=/opt/openrobots/lib/pkgconfig:$PKG_CONFIG_PATH \
    LD_LIBRARY_PATH=/opt/openrobots/lib:$LD_LIBRARY_PATH \
    PYTHONPATH=/opt/openrobots/lib/python3.10/site-packages:$PYTHONPATH \
    CMAKE_PREFIX_PATH=/opt/openrobots:$CMAKE_PREFIX_PATH


## ROS packages
WORKDIR /mnt/ros_ws/src
COPY ./repositories.yaml .
RUN vcs import --input repositories.yaml --recursive .

# RUN git clone https://github.com/aky-u/LevionArm.git \
#  && cd LevionArm \
#  && git submodule set-url cubemars_hardware https://github.com/aky-u/cubemars_hardware.git \
#  && git submodule set-url leptrino_force_torque https://github.com/aky-u/leptrino_force_torque.git \
#  && git submodule update --init --recursive

RUN apt-get update && apt-get install -y \
 && rosdep install --from-paths . --ignore-src -r -y
 
# Source ROS2 setup
SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

WORKDIR /mnt/ros_ws
RUN . /opt/ros/humble/setup.sh && colcon build --symlink-install
RUN echo "source /mnt/ros_ws/install/setup.bash" >> ~/.bashrc

# WORKDIR /
# Default command
# COPY ./ros_entrypoint.sh /
# RUN chmod +x /ros_entrypoint.sh
# ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]