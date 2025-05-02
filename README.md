# UniLuFP

## Pixhawk setup

Inherited from [here](https://atmos.discower.io/pages/PX4/).

```nsh
param set UXRCE_DDS_AG_IP 170461697 # The int32 version of 10.41.10.1
```

## Jetson setup

### Connect via SSH

Currently, using personal Android as a wi-fi rooter. TODO: Set static IP through ZeroG wi-fi.
Set IP following [here](https://docs.px4.io/main/en/companion_computer/holybro_pixhawk_jetson_baseboard.html#jetson-network-ssh-login).

```host PC
ssh spacer@192.168.177.210 # "177" can be changed.
```

### Clone UniFP repository

First clone this repo at into home directory.

```bash
git clone --recurse-submodules https://github.com/snt-spacer/UniLuFP.git
```

> [!NOTE]
> If you have cloned without submodules, use the following command to clone submodules.
>
> `git submodule update --init --recursive`

### Setup ethernet

Inherited from [here](https://docs.px4.io/main/en/companion_computer/holybro_pixhawk_jetson_baseboard.html#ethernet-setup-using-netplan).

You need to setup ethernet communication between Pixhawk and Jetson.
Make config file using the following command, and copy the setting below. The default IP is `10.41.10.1`.

```bash
sudo nano /etc/netplan/01-netcfg.yaml
```

```sh
network:
  version: 2
  renderer: networkd
  ethernets:
    enP8p1s0:
      dhcp4: no
      addresses:
        - 10.41.10.1/24
      routes:
        - to: 0.0.0.0/0
          via: 10.41.10.254
      nameservers:
        addresses:
          - 10.41.10.254
```

Then apply settings.

```bash
sudo netplan apply
```

Check connection between Pixhawk.

```bash spacer@jetson-pix
ping 10.41.10.2
```

>[!Note]
> If you have internet connection error after configuring ether net, change the priority.
>
> ```bash
> sudo nano /etc/systemd/resolved.conf
> ```
>
> ```ini
> [Resolve]
> DNS=8.8.8.8
> FallbackDNS=1.1.1.1
> ```
>
> ```bash
> ping google.com
> ```

### Set the hostname

```bash
sudo hostnamectl set-hostname spacer
```

```bash
sudo vim /etc/hosts
```

```/etc/hosts
127.0.0.1 localhost
127.0.1.1 spacer

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
```

### Setup Mavlink

Download and build Mavlink.

```bash
sudo apt install git meson ninja-build pkg-config gcc g++ systemd
sudo pip3 install meson
git clone git@github.com:mavlink-router/mavlink-router.git ~/mavlink_router
cd ~/mavlink_router
git submodule update --init --recursive
meson setup build .
sudo ninja -C build install
sudo mkdir -p /etc/mavlink-router/
sudo cp $HOME/UniLuFP/Pingu_OBC_Setup/mavlink.conf/* /etc/mavlink-router/
```

### Add Rules

```bash
sudo cp $HOME/UniLuFP/Pingu_OBC_Setup/rules/* /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Add the startup service

```bash
chmod +x /home/spacer/UniLuFP/Pingu_OBC_Setup/scripts/**
sudo cp $HOME/UniLuFP/Pingu_OBC_Setup/services/* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable px4_comm
sudo systemctl start px4_comm
sudo systemctl start can0_setup
sudo systemctl enable can0_setup
sudo systemctl enable mavlink_router
sudo systemctl start mavlink_router
sudo systemctl start arms_comm # FIXME: Has error
sudo systemctl enable arms_comm # FIXME: Has error
```

### Install ros2 humble

Follow instruction.

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source /home/spacer/fp_ws/install/setup.bash" >> ~/.bashrc
```

### Levion arm setting

```bash
cd fp_ws/src
ln -s ~/UniLuFP/LevionArm/
```

### Trouble shoot

- After running high-freq (100Hz) topic to pixhawk, micro-xrce killed. Even after reboot, still not active (after reloading daemon, get active)

```bash
ros2 run px4_ros_com offboard_control \
  --ros-args \
  -r /fmu/in/offboard_control_mode:=/spacer/fmu/in/offboard_control_mode \
  -r /fmu/in/trajectory_setpoint:=/spacer/fmu/in/trajectory_setpoint \
  -r /fmu/in/vehicle_command:=/spacer/fmu/in/vehicle_command
````
