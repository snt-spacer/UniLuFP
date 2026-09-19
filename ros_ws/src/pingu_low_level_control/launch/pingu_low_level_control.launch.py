import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    ls = LaunchDescription()
    config = os.path.join(
        get_package_share_directory('pingu_low_level_control'),
        'config',
        'pingu_config.yaml'
        )
    ns = LaunchConfiguration('namespace')
    ns_arg = DeclareLaunchArgument(
        'namespace',
        default_value='spacer_pingu_floating_platform',
    )
    fp_node = Node(
            package='pingu_low_level_control',
            namespace=ns,
            executable='pingu_low_level_control',
            name='pingu_low_level_control',
            output='screen',
            parameters = [config], 
        )
    ls.add_action(ns_arg)
    ls.add_action(fp_node)
    return ls