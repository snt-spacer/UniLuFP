# Model

The configuration of pingu is written using [xacro](http://wiki.ros.org/xacro). See [this launch file](../../ros_ws/src/pingu_ros2_control/bringup/launch/pingu.launch.py) to how to use xacro as robot_description.

## Export URDF form Xacro

You can also parse xacro to native urdf using the following command.

```bash
ros2 launch pingu_description export_ping.launch.py 
```

## Export MJCF from URDF

Use [this file](../../Pingu_Model/description/mujoco_models/export_mj_model.py) to generate MuJoCo xml model.
