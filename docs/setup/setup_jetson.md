# Setup Jetson

## Set static IP

- Go to setting and open ZeoG_Lab_wifi settings.
- Disable IP6v and set IP4v manual.

- Set the following values.

```settings
IP: 192.168.88.210
mask: 255.255.255.255
domain: 192.168.88.1
```

## Setup ROS 2 workspace

It is recommended to use docker in this project. In case you want to launch the program locally, here we describe how to set up workspace locally. 

```bash
cd
git clone -b dev git@github.com:snt-spacer/UniLuFP.git
mkdir -p fp_ws/src # or whatever name you want
cd fp_ws/src
ln -s ~/UniLuFP/ros_ws/src
git clone https://github.com/DISCOWER/px4_msgs.git
git clone https://github.com/DISCOWER/px4-mpc.git
git clone https://github.com/odriverobotics/ros_odrive.git
git clone --recurse-submodules -j8 git@github.com:aky-u/LevionArm.git

cd ..
rosdep install --from-paths src --ignore-src -r -y
``` 