# Use ROS2 Humble base image
FROM ros:humble

# Set the working directory to the main folder of your repository
WORKDIR /UniLuFP

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    ros-humble-rclpy \
    ros-humble-geometry-msgs \
    ros-humble-joy \
    ros-humble-ackermann-msgs \
    ros-humble-hardware-interface \
    ffmpeg \
    vim \
    git \
    byobu \
    build-essential \
    python3-vcstool \
    && rm -rf /var/lib/apt/lists/*

# Source ROS 2 in every shell
SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

COPY ./requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Github repositories
WORKDIR /UniLuFP/ros_ws/src
COPY ./repositories.yaml .
RUN vcs import --input repositories.yaml --recursive .

RUN git clone https://github.com/aky-u/LevionArm.git \
 && cd LevionArm \
 && git submodule set-url cubemars_hardware https://github.com/aky-u/cubemars_hardware.git \
 && git submodule update --init --recursive

# Source ROS2 setup
SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

WORKDIR /UniLuFP/ros_ws
RUN . /opt/ros/humble/setup.sh && colcon build --symlink-install
RUN echo "source /UniLuFP/ros_ws/install/setup.bash" >> ~/.bashrc

WORKDIR /UniLuFP/ros_ws
# Default command
COPY ./ros_entrypoint.sh /
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]