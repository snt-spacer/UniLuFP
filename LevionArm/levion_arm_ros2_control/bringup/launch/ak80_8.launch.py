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


def generate_launch_description():
    # Set package name
    package = FindPackageShare("levion_arm_ros2_control")

    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="Start RViz2 automatically with this launch file.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "controller_type",
            default_value="forward_position_controller",
            description="Controller type to use."
        )
    )

    # Initialize Arguments
    gui = LaunchConfiguration("gui")
    controller_type = LaunchConfiguration("controller_type")

    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([package, "urdf", "ak80_8.urdf.xacro"]),
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    robot_controllers = PathJoinSubstitution(
        [
            package,
            "config",
            "ak80_8_controller.yaml",
        ]
    )
    rviz_config_file = PathJoinSubstitution(
        [
            package,
            "rviz",
            "ak80_8.rviz",
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

    joint_state_pub_gui = Node(
        package="joint_state_publisher_gui", executable="joint_state_publisher_gui"
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[controller_type, "--param-file", robot_controllers],
    )

    # Delay rviz start after `joint_state_broadcaster`
    delay_rviz_after_joint_state_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[rviz_node],
        )
    )

    delay_joint_state_broadcaster_after_robot_controller_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=controller_spawner,
            on_exit=[joint_state_broadcaster_spawner],
        )
    )

    nodes = [
        control_node,
        robot_state_pub_node,
        # joint_state_pub_gui,
        controller_spawner,
        delay_joint_state_broadcaster_after_robot_controller_spawner,
        delay_rviz_after_joint_state_broadcaster_spawner,
    ]

    return LaunchDescription(declared_arguments + nodes)
