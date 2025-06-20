# ZeroG Lab

## Experiment setup

### Calibrate optitrack

## Launch pingu

### Launch thrusters

## Launch actuators

Actuators are controlled using [`ros2_control`](https://control.ros.org/humble/index.html).
To launch, run the following command.

```bash
ros2 launch pingu_ros2_control pingu.launch.py # option:=value controllers:=rw_velocity_controller,left_arm_position_controller
```

options:

| Option         | Default                       | Description                                            |
|----------------|-------------------------------|--------------------------------------------------------|
| `gui`          | false                         | Launch Rviz with controllers                           |
| `prefix`       | ""                            | Prefix of the joint names                              |
| `hw_plugin`    | real                          | Hardware plugin to use. Options: 'real' or 'mujoco`.   |
| `left_arm`     | true                          | Enable left-arm                                        |
| `right_arm`    | true                          | Enable right-arm                                       |
| `controllers`  | actuators_position_controller | Comma-separated list of controllers to spawn.          |

See [`pingu_controllers.yaml`](ros_ws/src/pingu_ros2_control/bringup/config/pingu_controllers.yaml) for available controllers.
