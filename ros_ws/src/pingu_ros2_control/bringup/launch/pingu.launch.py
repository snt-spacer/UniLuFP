from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.actions import OpaqueFunction
from launch.substitutions import (
    Command,
    FindExecutable,
    PathJoinSubstitution,
    LaunchConfiguration,
)

from launch_ros.actions import Node
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
    # Set package name
    package = FindPackageShare("pingu_ros2_control")
    description_package = FindPackageShare("pingu_description")
    arm_package = FindPackageShare("levion_arm_ros2_control")
    rw_package = FindPackageShare("rw_ros2_control")

    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "gui",
            default_value="false",
            description="Start RViz2 automatically with this launch file.",
        )
    )
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
            default_value="true",
            description="Enable left arm.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "right_arm",
            default_value="true",
            description="Enable right arm.",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "controllers",
            default_value="actuators_position_controller",
            description="Comma-separated list of controllers to spawn. \
        Check the `pingu_controllers.yaml` file for available controllers."
        )
    )

    # Initialize Arguments
    gui = LaunchConfiguration("gui")
    prefix = LaunchConfiguration("prefix")
    hw_plugin = LaunchConfiguration("hw_plugin")
    left_arm = LaunchConfiguration("left_arm")
    right_arm = LaunchConfiguration("right_arm")
    controllers = LaunchConfiguration("controllers")

    # Get URDF via xacro
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

    robot_controllers = PathJoinSubstitution(
        [
            package,
            "config",
            "pingu_controllers.yaml",
        ]
    )
    rviz_config_file = PathJoinSubstitution(
        [
            description_package,
            "rviz",
            "rw.rviz",
        ]
    )

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_controllers, robot_description],
        output="both",
    )
    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        condition=IfCondition(gui),
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    controller_spawners = OpaqueFunction(
        function=generate_controller_spawners,
        kwargs={
            'controllers_str': controllers,
            'robot_controllers_path': robot_controllers
        }
    )

    # Delay rviz start after `joint_state_broadcaster`
    delay_rviz_after_joint_state_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[rviz_node],
        )
    )

    nodes = [
        control_node,
        robot_state_pub_node,
        controller_spawners,
        joint_state_broadcaster_spawner,
        delay_rviz_after_joint_state_broadcaster_spawner,
    ]

    return LaunchDescription(declared_arguments + nodes)
