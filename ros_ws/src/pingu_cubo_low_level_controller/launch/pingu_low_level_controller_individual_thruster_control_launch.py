import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    ls = LaunchDescription()
    
    #joy_node
    joy_node = Node(package='joy',executable='joy_node',name='joy_node',output='screen')
    ls.add_action(joy_node)

    # Pingu CMD MUX
    pingu_cmd_mux_ns = LaunchConfiguration('pingu_cmd_mux_namespace')
    pingu_cmd_mux_ns_arg = DeclareLaunchArgument(
        'pingu_cmd_mux_namespace',
        default_value='pingu_cmd_mux',
    )
    ls.add_action(pingu_cmd_mux_ns_arg)
    pingu_cmd_mux_node = Node(
        package='cmd_mux',
        namespace=pingu_cmd_mux_ns,
        executable='pingu_cmd_mux',
        name='pingu_cmd_mux',
        output='screen',
        remappings=[
            ("/pingu_cmd_mux/joy_control_input", "/joy"),
            ("/pingu_cmd_mux/cmd_mux_low_level_publisher", "/fp_low_level_controller/valves/input"),
        ],
    )
    ls.add_action(pingu_cmd_mux_node)
    
    return ls