import os
import re
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import (
    Command,
    FindExecutable,
    PathJoinSubstitution,
    LaunchConfiguration,
)

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import xacro

"""
Export the URDF of the Pingu robot to a file after resolving package URIs.
This script processes a XACRO file, generates a URDF, and replaces all 'package://' URIs
with absolute paths in the URDF string. The resulting URDF is saved under an install directory.

Note: The path depends on your ROS 2 workspace path.
"""

def resolve_package_uris_in_urdf(urdf_str):
    """
    Replace all 'package://' URIs in the URDF string with absolute paths.
    """
    def replacer(match):
        package_uri = match.group(1)
        parts = package_uri.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid package URI: package://{package_uri}")
        package_name, relative_path = parts
        pkg_path = get_package_share_directory(package_name)
        abs_path = os.path.join(pkg_path, relative_path)
        return f'filename="{abs_path}"'

    return re.sub(r'filename="package://([^"]+)"', replacer, urdf_str)

def generate_launch_description():
    # Set arguments TODO: make this a LaunchConfiguration
    prefix = ''
    floating_joint = 'true'
    ros2_control = 'true'
    hw_plugin = 'mujoco'
    left_arm = 'true'
    right_arm = 'true'

    # define file path
    package = get_package_share_directory("pingu_launch")
    xacro_path = os.path.join(package, "urdf", "pingu.urdf.xacro")
    urdf_path = os.path.join(package, "urdf", "pingu.urdf")

    # load xacro
    doc = xacro.process_file(xacro_path, 
        mappings={'prefix': prefix, 
                  'floating_joint': floating_joint,
                  'ros2_control': ros2_control,
                  'hw_plugin': hw_plugin,
                  'left_arm': left_arm,
                  'right_arm': right_arm})

    # make urdf
    robot_desc = doc.toprettyxml(indent=' ')

    # resolve package URIs in the URDF
    # robot_desc = resolve_package_uris_in_urdf(robot_desc)

    # export urdf to urdf path
    f = open(urdf_path, 'w')
    f.write(robot_desc)
    f.close()

    print(f"URDF exported to {urdf_path}")

    return LaunchDescription()