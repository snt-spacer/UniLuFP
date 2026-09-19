# UniLuFP

## Cloning the repository

The repo uses git submodules for [LevionArm](https://github.com/aky-u/LevionArm.git) (with its own nested submodules `cubemars_hardware` and `leptrino_force_torque`), [RANS_DeployToRobot](https://github.com/SpaceR-x-DreamLab-RL/RANS_DeployToRobot) (branch `Pingu_Cubo`), and [cubemars-ak-c-drivers](https://github.com/leggedrobotics/cubemars-ak-c-drivers) (RSL CAN drivers for the AK motors). They live under `ros_ws/src/` and are mounted into the Docker container at runtime — **they must be present on the host**.

```bash
git clone --recurse-submodules https://github.com/snt-spacer/UniLuFP.git
```

> [!NOTE]
> If you already cloned without the flag, clone the submodules manually from inside the repo:
> ```bash
> git clone https://github.com/aky-u/LevionArm.git --recurse-submodules
> git clone -b Pingu_Cubo git@github.com:SpaceR-x-DreamLab-RL/RANS_DeployToRobot.git
> ```
> Or simply run `git submodule update --init --recursive`.


## Docker setup

```bash
cd ~/UniLuFP
./docker/build.sh   # build the image
./docker/run.sh     # start the container
```

`run.sh` mounts the submodules into the container over the fallback clones baked into the image, so any edits on the host are immediately visible inside. After editing, run `colcon build` inside the container.

| Host path | Container path |
|---|---|
| `ros_ws/src/LevionArm` | `/mnt/ros_ws/src/LevionArm` |
| `ros_ws/src/RANS_DeployToRobot` | `/mnt/ros_ws/src/RANS_DeployToRobot` |


## CubeMars AK motor drivers

The arm motors (AK80-8) run in **servo mode** — that is the firmware mode they are configured in and the protocol the whole stack uses. The CAN ids are:

| Joint | CAN id |
|---|---|
| `left_shoulder_joint` | 204 |
| `left_elbow_joint` | 105 |
| `right_shoulder_joint` | 104 |
| `right_elbow_joint` | 205 |

The driver code lives in three places:

| Location | What it is |
|---|---|
| `ros_ws/src/cubemars-ak-c-drivers` (git submodule) | [leggedrobotics/cubemars-ak-c-drivers](https://github.com/leggedrobotics/cubemars-ak-c-drivers) — plain C drivers (`ak_servo`, `ak_mit`) + standalone demos. `COLCON_IGNORE` at its root keeps colcon out of it; the sources are compiled directly by `cubemars_servo_hardware`. |
| `ros_ws/src/cubemars_servo_hardware` | **The interface to use.** ros2_control plugin for the 4 arm motors in servo mode, compiling `ak_servo.c` straight from the submodule (no vendored copies). Supports effort (current loop), velocity (speed loop), and position (position / position-speed loop) commands; publishes position, velocity, effort, temperature. |
| `ros_ws/src/cubemars_mit_hardware` | MIT-mode ros2_control plugin (vendored driver copies). **Not usable while the motors are in servo mode** — MIT mode is a persistent firmware setting changed per-motor with the CubeMars Tool + R-Link. Kept for reference/future experiments. |

There is also `cubemars_hardware` inside the LevionArm submodule — the original servo-mode interface the full stack currently launches.

> [!NOTE]
> Both servo interfaces use the same effort convention (`current = τ / kt`, no gear ratio — i.e. "effort" is motor-side torque), so controller gains transfer 1:1 between `cubemars_hardware` and `cubemars_servo_hardware`.

### Dockerfile notes

- **CMake 3.28.6 is built from source** in the image (installs to `/usr/local/bin`, shadowing apt's 3.22) because the cubemars-ak-c-drivers demos require CMake ≥ 3.28.
- The submodule reaches the container through the repo mount (`/UniLuFP/ros_ws/src/cubemars-ak-c-drivers`).

### Testing the raw drivers (no ROS, inside the container)

```bash
cd /UniLuFP/ros_ws/src/cubemars-ak-c-drivers/drivers
cmake -B build && cmake --build build   # demos; needs the CMake ≥ 3.28 from the image
```

Or just watch the bus: `candump can0` — in servo mode every motor periodically broadcasts a status frame with extended id `0x29<id>` (e.g. `0x29CC` for the left shoulder, id 204 = 0xCC), so you can verify wiring and ids without any software.

### Testing a single motor via cubemars_servo_hardware

Prerequisite: `can0` up on the Jetson (`can0_setup` systemd service — check with `ip link show can0`). Run inside the container.

```bash
# Terminal 1 — bring up ros2_control with all 4 arm motors.
# Joint states stream immediately (servo motors broadcast on their own);
# no motor is driven until you activate a controller.
ros2 launch cubemars_servo_hardware servo_test_launch.py
```

Moving any arm by hand should now show in `/joint_states` (PlotJuggler or `ros2 topic echo /joint_states`). To actively drive **one** motor, spawn only its effort controller and run the impedance test node:

```bash
# Terminal 2 — e.g. left shoulder
ros2 run controller_manager spawner left_arm_shoulder_effort_controller
ros2 run pingu_cubo_low_level_controller single_motor_test_impedance \
    --ros-args -p joint:=left_shoulder_joint -p kp:=0.5 -p kd:=0.03
```

| Joint | Effort controller |
|---|---|
| `left_shoulder_joint` | `left_arm_shoulder_effort_controller` |
| `left_elbow_joint` | `left_arm_elbow_effort_controller` |
| `right_shoulder_joint` | `right_arm_shoulder_effort_controller` |
| `right_elbow_joint` | `right_arm_elbow_effort_controller` |

A one-off torque command without the test node (0.3 Nm, then 0 to stop):

```bash
ros2 topic pub --once /left_arm_shoulder_effort_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.3]}"
ros2 topic pub --once /left_arm_shoulder_effort_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.0]}"
```

> [!WARNING]
> Start with the motor free to move and the default gains before increasing anything. Effort commands are clamped to the `effort_limit` of the xacro macro (10 Nm ≈ 6.3 A).

### Integrating cubemars_servo_hardware into the whole stack

The full-stack launch exposes `hw_plugin`; `rsl_servo` selects `cubemars_servo_hardware` for the arms (the reaction wheel stays on ODrive):

```bash
ros2 launch pingu_cubo_low_level_controller pingu_low_level_controller_individual_thruster_control_launch.py \
    hw_plugin:=rsl_servo \
    arm_controllers:="left_arm_shoulder_effort_controller"
ros2 control switch_controllers --activate left_arm_shoulder_effort_controller
ros2 run pingu_cubo_low_level_controller single_motor_test_impedance --ros-args -p joint:=left_shoulder_joint
```

Without `hw_plugin:=rsl_servo` the stack uses the default LevionArm `cubemars_hardware` interface, same commands. Remember the effort-scaling warning above when switching between the two — controller gains tuned on one are not valid on the other.


### Test Thrusters
It keeps thruster 7 always on and every 2 seconds keeps opening a new thruster from 0 to 8. 
```
ros2 launch leptrino_force_torque leptrino.launch.py
ros2 run px4_simple logger_thruster_test
ros2 run px4_simple test_solenoid_valve_connection
```

### Launch 
```bash
ros2 launch pingu_cubo_low_level_controller pingu_low_level_controller_individual_thruster_controll_launch.py
```

**Wall Docking**

Three-phase pipeline: Phase 1 RL approach → Phase 2 passive glide (thrusters off) → Phase 3 arm damping.

Terminal 0 — low level control (reaction wheel + dual arm effort controllers)
```
ros2 launch pingu_cubo_low_level_controller pingu_low_level_controller_individual_thruster_control_launch.py controllers:="rw_effort_controller, dual_arm_effort_controller"
```
Terminal 1 — FT sensors (order vs. docking node doesn't matter)
```
ros2 launch leptrino_force_torque leptrino.launch.py
```
Terminal 2 — wall docking pipeline
```
ros2 launch rl_inference pingu_wall_docking_launch.py ft_contact_threshold:=10.0 thruster_brake_gain:=0.0
```

#### Arm control modes (`use_admittance`)

| Mode | Flag | Behaviour |
|---|---|---|
| **Pure PD** (default) | `use_admittance:=False` | Spring-damper anchored at contact snapshot. Simple, one arm or both arms independently, easy to tune. |
| **PD + Admittance** | `use_admittance:=True` | PD baseline + admittance layer that estimates external torque and shifts the reference, allowing the arms to yield to sustained forces. Requires pushing both arms simultaneously — pushing one arm only causes the admittance integrator to accumulate asymmetrically and jitter. |

#### Key parameters

| Parameter | Default | Description |
|---|---|---|
| `kp_shoulder` / `kp_elbow` | 5.0 / 3.0 | Position stiffness (Nm/rad). Increase to fight displacement more. |
| `kd_shoulder` / `kd_elbow` | 0.3 / 0.2 | Velocity damping (Nm·s/rad). Increase to kill oscillations. |
| `ft_contact_threshold` | 10.0 | FT force (N) that ends Phase 2 and starts damping. |
| `thruster_brake_gain` | 0.0 | [0–1] reverse thrust on t2/t7 during Phase 3. 0 = arms only. |
| `damping_timeout` | 30.0 | Phase 3 safety timeout (s). |
| `skip_to_damping` | False | `True` skips Phases 1 & 2 and goes straight to damping — useful for testing arm control without needing an ArUco goal or wall contact. |
| `use_admittance` | False | `True` enables the admittance layer on top of PD. |
| `d_admit_shoulder` / `d_admit_elbow` | 5.0 / 5.0 | Admittance damping. Set to ~50 to nearly disable compliance while keeping `use_admittance:=True`. |

#### Testing arm damping only (no RL, no glide)
```
ros2 launch rl_inference pingu_wall_docking_launch.py \
    skip_to_damping:=True \
    kp_shoulder:=5.0 kp_elbow:=3.0 \
    kd_shoulder:=0.3 kd_elbow:=0.2 \
    damping_timeout:=60.0
```

### LED with micro-ros
```bash
docker run -it  --name microros-bridge --rm -v /dev:/dev --privileged --net=host microros/micro-ros-agent:humble serial --dev /dev/ttyUSB0 
```

Reaction wheel

`ros2 topic pub /rw_velocity_controller/commands std_msgs/msg/Float64MultiArray "{data: [3.0]}"`

### Packages Descriptions
- `pingu_cubo_low_level_controller`
  - Umbrella launcher for the `joy`, `*cmd_mux`, and `low_level_controller` packages
- `pingu_cmd_mux`
    - Takes the inputs of the joy and sends it to the low level controller
- `low_level_controller`
  - Launches the low level controller of the Pingu or the Cubo.

[Notion](https://www.notion.so/Pingu-FP-1c7aaf8bff7f8098a08bc9bdcd53db11)

## Pixhawk setup

Inherited from [here](https://atmos.discower.io/pages/PX4/).

Build QGC from [daily](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/releases/daily_builds.html#daily-builds)

```nsh
param set UXRCE_DDS_AG_IP 170461697 # The int32 version of 10.41.10.1

# Pingu: 192.168.88.159 -> 3232258207
```

## Jetson setup

### Connect via SSH

Currently, using personal Android as a wi-fi rooter. TODO: Set static IP through ZeroG wi-fi.
Set IP following [here](https://docs.px4.io/main/en/companion_computer/holybro_pixhawk_jetson_baseboard.html#jetson-network-ssh-login).

```host PC
ssh spacer@192.168.177.210 # "177" can be changed.
```

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
chmod +x ~/UniLuFP/Pingu_OBC_Setup/scripts/**
find ~/UniLuFP/Pingu_OBC_Setup/scripts -type f -exec chmod +x {} +
sudo cp ~/UniLuFP/Pingu_OBC_Setup/scripts/* /usr/local/bin/
sudo cp ~/UniLuFP/Pingu_OBC_Setup/services/* /etc/systemd/system/
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

### Trouble shoot

- After running high-freq (100Hz) topic to pixhawk, micro-xrce killed. Even after reboot, still not active (after reloading daemon, get active)

```bash
ros2 run px4_ros_com offboard_control \
  --ros-args \
  -r /fmu/in/offboard_control_mode:=/spacer/fmu/in/offboard_control_mode \
  -r /fmu/in/trajectory_setpoint:=/spacer/fmu/in/trajectory_setpoint \
  -r /fmu/in/vehicle_command:=/spacer/fmu/in/vehicle_command
```
