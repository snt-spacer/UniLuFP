# UniLuFP

## Pixhawk setup

Flash Pixhawk following the instructions from [here](https://atmos.discower.io/pages/PX4/).

TODO: Currently using default instead of space
Install QGC (default) from [here](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/releases/daily_builds.html).

> FIXME: I could not change pixhawk network setting by the following steps. ([Reference](https://docs.px4.io/main/en/advanced_config/ethernet_setup.html))
>
> ```MAVLink Console (QGC > Analyze Tools)
> echo DEVICE=enP8p1s0 > /fs/microsd/net.cfg
> echo BOOTPROTO=fallback > /fs/microsd/net.cfg
> echo IPADDR=10.41.10.2 > /fs/microsd/net.cfg
> echo NETMASK=255.255.255.0 > /fs/microsd/net.cfg
> echo ROUTER=10.41.10.254 > /fs/microsd/net.cfg
> echo DNS=10.41.10.254 > /fs/microsd/net.cfg
> ```

## Jetson setup

### Connect via SSH

Currently, using personal Android as a wi-fi rooter. TODO: Need to update ssh to use in ZeoG.
Set IP following [here](https://docs.px4.io/main/en/companion_computer/holybro_pixhawk_jetson_baseboard.html#jetson-network-ssh-login).

```host PC
ssh spacer@192.168.236.210
```

### Set up ethernet

Inherited from [here](https://docs.px4.io/main/en/companion_computer/holybro_pixhawk_jetson_baseboard.html#ethernet-setup-using-netplan).

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

```bash
sudo netplan apply
```

Change Ethernet name from enP8p1s0 to eth0 (not permanent. Maybe not needed.)

```bash spacer@jetson-pix
sudo ip link set enP8p1s0 down
sudo ip link set enP8p1s0 name eth0
sudo ip link set eth0 up
```

```bash spacer@jetson-pix
ping 10.41.10.2
```

```bash
sudo hostnamectl set-hostname spacer
```

### Set the hostname

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

### Add Rules

```bash
sudo cp $HOME/UniLuFP/Pingu_OBC_Setup/rules/* /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Mavlink

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

### Add the startup service

```bash
sudo cp $HOME/UniLuFP/Pingu_OBC_Setup/services/* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable px4_comm
sudo systemctl start px4_comm
sudo systemctl enable vehicle_mocap_odom
sudo systemctl start vehicle_mocap_odom
sudo systemctl enable mavlink_router
sudo systemctl start mavlink_router
```
