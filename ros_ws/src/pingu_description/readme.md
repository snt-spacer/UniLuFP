# Pingu Description

From the UniluFP `ros_ws` folder
```
ros2 launch pingu_description export_pingu.launch.py
ros2 launch pingu_description view_pingu.launch.py
```

For Rviz and Mujoco `pingu.urdf.xacro` will do. If you want to import as UDS for Isaac Lab use `pingu_v2.urdf.xacro`

Note: If changes are made on the ros2_control of the rw and the arms, those will be reflected on the `pingu.urdf.xacro` but they wont be visible in `pingu_v2.urdf.xacro` since it uses local files. 


Open IsaacLab and import the URDF to convert it into USD ([Docs](https://isaac-sim.github.io/IsaacLab/main/source/how-to/import_new_asset.html)).

```
./isaaclab.sh -p ./scripts/tools/convert_urdf.py ".../pingu_2025_10_22.urdf" ".../pingu_code_2.usd" --joint-stiffness 0.0 --joint-damping 0.0 --joint-target-type none
```

Remove Drive and Joint State from all the joints. Set the limits and break force to inf.

Add a fixed joint between empty and the world xform
