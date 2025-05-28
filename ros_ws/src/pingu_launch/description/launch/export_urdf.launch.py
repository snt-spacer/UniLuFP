import os
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

def generate_launch_description():
  # define file path
  package = get_package_share_directory("pingu_launch")
  xacro_path = os.path.join(package, "urdf", "pingu.urdf.xacro")
  urdf_path = os.path.join(package, "urdf", "pingu.urdf")

  # load xacro
  doc = xacro.process_file(xacro_path)
  # make urdf
  robot_desc = doc.toprettyxml(indent=' ')
  # export urdf to urdf path
  f = open(urdf_path, 'w')
  f.write(robot_desc)
  f.close()

  return LaunchDescription()