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
    package = FindPackageShare("pingu_launch")

    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "joint_state_publisher_gui",
            default_value="true",
            description="Start joint_state_publisher_gui automatically with this launch file. \
        If set to false, joint topic should be published by real robot or \
        simulated robot.",
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

    # Initialize Arguments
    joint_state_publisher_gui = LaunchConfiguration("joint_state_publisher_gui")
    prefix = LaunchConfiguration("prefix")

    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([package, "urdf", "pingu.urdf.xacro"]),
            " ",
            "prefix:=",
            prefix,
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    rviz_config_file = PathJoinSubstitution(
        [
            package,
            "rviz",
            "pingu.rviz",
        ]
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
    )

    joint_state_pub_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        output="log",
        parameters=[robot_description],
        condition=IfCondition(joint_state_publisher_gui),
    )

    nodes = [
        robot_state_pub_node,
        joint_state_pub_gui,
        rviz_node,
    ]

    return LaunchDescription(declared_arguments + nodes)
