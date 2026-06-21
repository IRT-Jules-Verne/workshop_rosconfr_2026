
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterFile
from launch_ros.substitutions import FindPackageShare


def launch_setup(context):
    # General arguments
    controllers_file = LaunchConfiguration("controllers_file")
    description_launchfile = LaunchConfiguration("description_launchfile")

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            ParameterFile(controllers_file, allow_substs=True),
        ],
        output="screen",
        remappings=[("~/robot_description", "/robot_description")],
    )


    # Spawn controllers
    def controller_spawner(controllers, active=True):
        inactive_flags = ["--inactive"] if not active else []
        return Node(
            package="controller_manager",
            executable="spawner",
            arguments=[
                "--controller-manager",
                "/controller_manager",
                "--controller-manager-timeout",
                "10"
            ]
            + inactive_flags
            + controllers,
        )

    controllers_active = [
        "joint_state_broadcaster",
        "joint_trajectory_controller",
    ]
    controllers_inactive = [
        "forward_velocity_controller",
        "forward_position_controller",
        "forward_effort_controller",
    ]


    controller_spawners = [
        controller_spawner(controllers_active),
        controller_spawner(controllers_inactive, active=False),
    ]

    rsp = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(description_launchfile),
        launch_arguments={
        }.items(),
    )

    nodes_to_start = [
        control_node,
        rsp,
    ] + controller_spawners

    return nodes_to_start


def generate_launch_description():
    declared_arguments = []
    # UR specific arguments
    # General arguments
    declared_arguments.append(
        DeclareLaunchArgument(
            "controllers_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare("workshop_robot_moveit_config"), "config", "ur_controllers.yaml"]
            ),
            description="YAML file with the controllers configuration.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "description_launchfile",
            default_value=PathJoinSubstitution(
                [FindPackageShare("workshop_robot_moveit_config"), "launch", "robot_rsp.launch.py"]
            ),
            description="Launchfile (absolute path) providing the description. "
            "The launchfile has to start a robot_state_publisher node that "
            "publishes the description topic.",
        )
    )
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
