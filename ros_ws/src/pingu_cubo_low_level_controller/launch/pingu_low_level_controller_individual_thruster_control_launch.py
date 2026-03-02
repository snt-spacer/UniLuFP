import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import OpaqueFunction
from launch.substitutions import (
    Command,
    FindExecutable,
    PathJoinSubstitution,
    LaunchConfiguration,
)
from launch_ros.substitutions import FindPackageShare

def parse_controller_names(context, controllers_str):
    value = controllers_str.perform(context)
    return [c.strip() for c in value.split(",") if c.strip()]

def generate_controller_spawners(context, controllers_str, robot_controllers_path):
    controllers = parse_controller_names(context, controllers_str)
    return [
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=[controller, "--param-file", robot_controllers_path],
            output="screen"
        ) for controller in controllers
    ]

def generate_launch_description():
    package = FindPackageShare("pingu_cubo_low_level_controller")
    description_package = FindPackageShare("pingu_description")
    arm_package = FindPackageShare("levion_arm_ros2_control")
    rw_package = FindPackageShare("rw_ros2_control")

    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "prefix",
            default_value='""',
            description="Prefix of the joint names, useful for \
        multi-robot setup. If changed than also joint names in the controllers' configuration \
        have to be updated.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "hw_plugin",
            default_value='real',
            description="Hardware plugin to use. Options: 'real' or 'mujoco`. \
        'real' uses the real hardware, while 'mujoco' uses the Mujoco"
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "left_arm",
            default_value="false",
            description="Enable left arm.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "right_arm",
            default_value="false",
            description="Enable right arm.",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "controllers",
            default_value="rw_effort_controller",
            description="Comma-separated list of controllers to spawn. \
        Check the `pingu_controllers.yaml` file for available controllers. EX: [actuators_position_controller, actuators_velocity_controller, actuators_effort_controller, actuators_trajectory_controller, rw_velocity_controller, rw_effort_controller, dual_arm_position_controller...]."
        )
    )

    # Initialize Arguments
    prefix = LaunchConfiguration("prefix")
    hw_plugin = LaunchConfiguration("hw_plugin")
    left_arm = LaunchConfiguration("left_arm")
    right_arm = LaunchConfiguration("right_arm")
    controllers = LaunchConfiguration("controllers")

    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([description_package, "urdf", "pingu.urdf.xacro"]),
            " ",
            "prefix:=",
            prefix,
            " ",
            "hw_plugin:=",
            hw_plugin,
            " ",
            "left_arm:=",
            left_arm,
            " ",
            "right_arm:=",
            right_arm,
        ]   
    )
    robot_description = {"robot_description": robot_description_content}
    pingu_cmd_mux_ns = LaunchConfiguration('pingu_cmd_mux_namespace')
    pingu_cmd_mux_ns_arg = DeclareLaunchArgument(
        'pingu_cmd_mux_namespace',
        default_value='pingu_cmd_mux',
    )

    
    #joy_node
    joy_node = Node(package='joy',executable='joy_node',name='joy_node',output='screen')

    # Pingu CMD MUX
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

    # Pingu Arms and Reaction Wheel
    robot_controllers = PathJoinSubstitution(
        [
            package,
            "config",
            "pingu_controllers.yaml",
        ]
    )
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_controllers, robot_description],
        output="both",
    )

    # Robot State Publisher
    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )

    # Joint State Publisher
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    # Controller Spawners
    controller_spawners = OpaqueFunction(
        function=generate_controller_spawners,
        kwargs={
            'controllers_str': controllers,
            'robot_controllers_path': robot_controllers
        }
    )

    # rw_controller_arg = DeclareLaunchArgument(
    #     'rw_controller',
    #     default_value='rw_effort_controller',
    # )
    # ls.add_action(rw_controller_arg)

    # pingu_ros2_control_launch = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(
    #         PathJoinSubstitution([
    #             FindPackageShare('pingu_ros2_control'),
    #             'launch',
    #             'pingu.launch.py',
    #         ])
    #     ),
    #     launch_arguments={
    #         'gui': 'false',
    #         'left_arm': 'false',
    #         'right_arm': 'false',
    #         'controllers': LaunchConfiguration('rw_controller'),
    #     }.items(),
    # )
    # ls.add_action(pingu_ros2_control_launch)
    
    nodes_list = [
        joy_node,
        pingu_cmd_mux_ns_arg,
        pingu_cmd_mux_node,
        control_node,
        robot_state_pub_node,
        joint_state_broadcaster_spawner,
        controller_spawners,
    ]
    return LaunchDescription(declared_arguments + nodes_list)