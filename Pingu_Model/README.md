# Pingu_Model

## Summary

## Generate URDF

Check [export_pingu.launch.py](ros_ws/src/pingu_ros2_control/description/launch/export_ping.launch.py)

## Export Mujoco

```bash
python3 -c "import mujoco; model = mujoco.MjModel.from_xml_path('pingu.urdf'); mujoco.mj_saveLastXML('pingu.xml', model)"
```

## Reference

- <https://docs.picknik.ai/6/getting_started/configuration_tutorials/migrate_to_mujoco_config/>
