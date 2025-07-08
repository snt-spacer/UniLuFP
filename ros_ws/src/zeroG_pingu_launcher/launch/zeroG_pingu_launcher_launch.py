import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, TextSubstitution

def generate_launch_description():
    ls = LaunchDescription()

    # Joy node
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen'
    )
    ls.add_action(joy_node)

    # Pingu CMD MUX
    pingu_cmd_mux_ns = LaunchConfiguration('pingu_cmd_mux_namespace')
    pingu_cmd_mux_ns_arg = DeclareLaunchArgument(
        'pingu_cmd_mux_namespace',
        default_value='pingu_cmd_mux',
    )
    ls.add_action(pingu_cmd_mux_ns_arg)
    config = os.path.join(
        get_package_share_directory('pingu_low_level_control'),
        'config',
        'pingu_config.yaml'
    )
    pingu_cmd_mux_node = Node(
        package='pingu_cmd_mux',
        namespace=pingu_cmd_mux_ns,
        executable='pingu_cmd_mux',
        name='pingu_cmd_mux',
        output='screen',
        parameters = [config], 
        remappings=[
            # ([TextSubstitution(text='/'), pingu_cmd_mux_ns, TextSubstitution(text='/joy_control_input')], '/joy'),
            # ([TextSubstitution(text='/'), pingu_cmd_mux_ns, TextSubstitution(text='/input_valve_2')], '/pingu_low_level_control/pingu_valves/input'),

            (TextSubstitution(text=pingu_cmd_mux_ns,
                              substitutions=[pingu_cmd_mux_ns, TextSubstitution(text="/joy_control_input")]),
             '/joy'),
            (TextSubstitution(text=pingu_cmd_mux_ns,
                              substitutions=[pingu_cmd_mux_ns, TextSubstitution(text="/input_valve_2")]),
             '/pingu_low_level_control/valves/input'),
        ],
    )
    ls.add_action(pingu_cmd_mux_node)

    # Pingu Manual Control
    pingu_manual_control_ns = LaunchConfiguration('pingu_manual_control_namespace')
    pingu_manual_control_ns_arg = DeclareLaunchArgument(
        'pingu_manual_control_namespace',
        default_value='pingu_manual_control',
    )
    ls.add_action(pingu_manual_control_ns_arg)
    manual_control_node = Node(
        package='pingu_cmd_mux',
        namespace=pingu_manual_control_ns,
        executable='pingu_manual_control',
        name='pingu_manual_control',
        output='screen',
        remappings=[
<<<<<<< HEAD
            # ([TextSubstitution(text='/'), pingu_manual_control_ns, TextSubstitution(text='/joy')], '/joy'),
            # ([TextSubstitution(text='/'), pingu_manual_control_ns, TextSubstitution(text='/manual_control_output')], '/pingu_cmd_mux/manual_control_input'),

            (TextSubstitution(text=pingu_manual_control_ns,
                              substitutions=[pingu_manual_control_ns, TextSubstitution(text="/joy")]),
             '/joy'),
            (TextSubstitution(text=pingu_manual_control_ns,
                              substitutions=[pingu_manual_control_ns, TextSubstitution(text="/manual_control_output")]),
             '/fp_cmd_mux/manual_control_input'),
=======
            ([TextSubstitution(text='/'), pingu_manual_control_ns, TextSubstitution(text='/joy')], '/joy'),
            ([TextSubstitution(text='/'), pingu_manual_control_ns, TextSubstitution(text='/manual_control_output')], '/pingu_cmd_mux/manual_control_input'),
>>>>>>> dev
        ],
    )
    ls.add_action(manual_control_node)

    # Pingu Low Level Controller
    pingu_low_level_control_ns = LaunchConfiguration('pingu_low_level_control_namespace')
    pingu_low_level_control_ns_arg = DeclareLaunchArgument(
        'pingu_low_level_control_namespace',
        default_value='pingu_low_level_control',
    )
    ls.add_action(pingu_low_level_control_ns_arg)
    pingu_low_level_control_node = Node(
        package='pingu_low_level_control',
        namespace=pingu_low_level_control_ns,
        executable='pingu_low_level_control',
        name='pingu_low_level_control',
        output='screen',
<<<<<<< HEAD
        parameters = [config, {'namespace': pingu_low_level_control_ns}], 
=======
        parameters = [config], 
>>>>>>> dev
    )
    ls.add_action(pingu_low_level_control_node)
    

    return ls