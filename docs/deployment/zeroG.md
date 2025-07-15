# ZeroG Lab

## Experiment setup

### Calibrate optitrack

## Launch pingu

### Launch optitrack

```bash
ros2 launch vrpn_mocap client.launch.yaml server:=192.168.88.13
```

### Launch thrusters

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