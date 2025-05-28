# UniLuFP

[Notion](https://www.notion.so/Pingu-FP-1c7aaf8bff7f8098a08bc9bdcd53db11)


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
```

## Docker setup
```
cd ~/UniLuFP
./docker/build.sh
```

## Getting Started
```
./docker/run.sh
 ros2 run px4_simple test_solenoid_valve_connection --ros-args --param namespace:=spacer
```

## temp

WARNING: Gauss-Newton Hessian approximation with EXTERNAL cost type not well defined!
got cost_type EXTERNAL for cost_type_0, cost_type, cost_type_e, hessian_approx: 'GAUSS_NEWTON'.
With this setting, acados will proceed computing the exact Hessian for the cost term and no Hessian contribution from constraints and dynamics.
If the external cost is a linear least squares cost, this coincides with the Gauss-Newton Hessian.
Note: There is also the option to use the external cost module with a numerical Hessian approximation (see `ext_cost_num_hess`).
OR the option to provide a symbolic custom Hessian approximation (see `cost_expr_ext_cost_custom_hess`).

sh: 1: /home/spacer/acados/bin/t_renderer: not found
Traceback (most recent call last):
  File "/home/spacer/fp_ws/install/px4_mpc/lib/px4_mpc/mpc_spacecraft", line 33, in <module>
    sys.exit(load_entry_point('px4-mpc', 'console_scripts', 'mpc_spacecraft')())
  File "/home/spacer/fp_ws/build/px4_mpc/px4_mpc/mpc_spacecraft.py", line 474, in main
    spacecraft_mpc = SpacecraftMPC()
  File "/home/spacer/fp_ws/build/px4_mpc/px4_mpc/mpc_spacecraft.py", line 125, in __init__
    self.mpc = SpacecraftWrenchMPC(self.model)
  File "/home/spacer/fp_ws/build/px4_mpc/px4_mpc/controllers/spacecraft_wrench_mpc.py", line 47, in __init__
    self.ocp_solver, self.integrator = self.setup(self.x0, self.N, self.Tf)
  File "/home/spacer/fp_ws/build/px4_mpc/px4_mpc/controllers/spacecraft_wrench_mpc.py", line 139, in setup
    ocp_solver = AcadosOcpSolver(ocp, json_file=json_path)
  File "/home/spacer/acados/interfaces/acados_template/acados_template/acados_ocp_solver.py", line 231, in __init__
    self.generate(acados_ocp, json_file=acados_ocp.json_file, simulink_opts=simulink_opts, cmake_builder=cmake_builder, verbose=verbose)
  File "/home/spacer/acados/interfaces/acados_template/acados_template/acados_ocp_solver.py", line 132, in generate
    acados_ocp.render_templates(cmake_builder=cmake_builder)
  File "/home/spacer/acados/interfaces/acados_template/acados_template/acados_ocp.py", line 1214, in render_templates
    render_template(tup[0], tup[1], output_dir, json_path)
  File "/home/spacer/acados/interfaces/acados_template/acados_template/utils.py", line 304, in render_template
    raise RuntimeError(f'Rendering of {in_file} failed!\n\nAttempted to execute OS command:\n{os_cmd}\n\n')
RuntimeError: Rendering of main.in.c failed!

Attempted to execute OS command:
~/acados/bin/t_renderer '/home/spacer/acados/interfaces/acados_template/acados_template/c_templates_tera/**/*' 'main.in.c' '/home/spacer/fp_ws/build/px4_mpc/px4_mpc/mpc_codegen/acados_ocp.json' 'main_spacecraft_direct_allocation_model.c'


