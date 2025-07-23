# ZeroG Lab

## Experiment setup

### Calibrate optitrack

TODO: How to setup the lab.

## Launch pingu

### Launch optitrack

```bash
ros2 launch vrpn_mocap client.launch.yaml server:=192.168.88.13
```

### Launch thrusters

TODO: Add launch arg for low level.

### Launch actuators

Actuators are controlled using [`ros2_control`](https://control.ros.org/humble/index.html).
To launch, run the following command.

```bash
ros2 launch pingu_ros2_control pingu.launch.py # option:=value controllers:=rw_velocity_controller,left_arm_position_controller
```

| Option         | Default                       | Description                                            |
|----------------|-------------------------------|--------------------------------------------------------|
| `gui`          | false                         | Launch Rviz with controllers                           |
| `prefix`       | ""                            | Prefix of the joint names                              |
| `hw_plugin`    | real                          | Hardware plugin to use. Options: 'real' or 'mujoco`.   |
| `left_arm`     | true                          | Enable left-arm                                        |
| `right_arm`    | true                          | Enable right-arm                                       |
| `controllers`  | actuators_position_controller | Comma-separated list of controllers to spawn.          |

See [`pingu_controllers.yaml`](../../ros_ws/src/pingu_ros2_control/bringup/config/pingu_controllers.yaml) for available controllers.

#### Examples 

The default launch argument equals to running the same as the following command.

```bash
ros2 launch pingu_ros2_control pingu.launch.py controllers:=actuators_position_controller
```

This controller controls the position of all the actuators at the same time using the **5 doubles** in `std_msgs::Float64MultiArray` message like,

```bash
# rw,left shoulder,left elbow,right shoulder,right elbow
ros2 topic pub /actuators_position_controller/commands std_msgs/msg/Float64MultiArray "data:
- 0.0   
- 0.0   
- -1.57 
- 0.0   
- 1.57" 
```

If you want to control each system separately, like velocity control for reaction wheel and position control for arms, check the example below.

```bash
ros2 launch pingu_ros2_control pingu.launch.py controllers:=rw_velocity_controller,dual_arm_position_controller
```

Then, you can send the command separately like,

```bash
# rw
ros2 topic pub /rw_velocity_controller/commands std_msgs/msg/Float64MultiArray "data:
- 5.0" 
```

```bash
# left shoulder,left elbow,right shoulder,right elbow
ros2 topic pub /dual_arm_position_controller/commands std_msgs/msg/Float64MultiArray "data:
- 0.0   
- -1.57 
- 0.0   
- 1.57" 
```

#### Controller GUI

You can also use the [ros2_control_gui](https://github.com/aky-u/ros2_control_gui) package to command the ros2 controllers, even though it's still under development.

After build the package using the `colcon build` command, launch it by the following command.

```bash
ros2 run ros2_control_gui joint_controller_gui
```

Then select the controller that you want to use.

## Launch Rviz

The default viewer is placed under [`pingu_description`](../../ros_ws/src/pingu_description).
To launch, run the following command.

```bash
ros2 launch pingu_description view_pingu.launch.py # joint_state_publisher_gui:=true
```

| Option                     | Default | Description                                               |
|----------------------------|---------|-----------------------------------------------------------|
| `joint_state_publisher_gui`| false   | Launch with virtual joint_state publisher for debug usage.|
| `zero_g`                   | true    | Visualize ZeroG lab in Rviz.                              |

If you want to see the current pose of the platform in Rviz, run the following command to get the TF from optitrack. Do not forget to launch `vrpn_mocap` and match the topic name.

```bash
ros2 run pingu_optitrack pose_to_tf 
```


# Errors
## Ubuntu 22.04 ros2 humble installing error GPG, libc-bin
https://answers.ros.org/question/410123/