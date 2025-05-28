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

    # Initialize Arguments
    gui = LaunchConfiguration("gui")
    prefix = LaunchConfiguration("prefix")

    # Get URDF via xacro
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

    robot_controllers = PathJoinSubstitution(
        [
            package,
            "config",
            "pingu_controllers.yaml",
        ]
    )
    rviz_config_file = PathJoinSubstitution(
        [
            package,
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

    #TODO Make is better
    controller_spawners = [
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["left_arm_velocity_controller", "--param-file", robot_controllers],
        ),

        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["right_arm_velocity_controller", "--param-file", robot_controllers],
        ),

        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["rw_velocity_controller", "--param-file", robot_controllers],
        ),
    ]

    # Delay rviz start after `joint_state_broadcaster`
    delay_rviz_after_joint_state_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[rviz_node],
        )
    )

    delay_joint_state_broadcaster_after_robot_controller_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=controller_spawners[-1], # Wait for the last controller spawner
            on_exit=[joint_state_broadcaster_spawner],
        )
    )

    nodes = [
        control_node,
        robot_state_pub_node,
        delay_joint_state_broadcaster_after_robot_controller_spawner,
        delay_rviz_after_joint_state_broadcaster_spawner,
    ]

    # Add controller spawners to the nodes list
    nodes.extend(controller_spawners)

    return LaunchDescription(declared_arguments + nodes)
