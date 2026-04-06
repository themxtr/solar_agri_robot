import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_desc = get_package_share_directory('solar_agri_description')
    urdf_file = os.path.join(pkg_desc, 'urdf', 'solar_agri_robot.urdf.xacro')

    robot_description = ParameterValue(
        Command(['xacro ', urdf_file]),
        value_type=str
    )

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description}]
        ),

        Node(
            package='solar_agri_control',
            executable='robot_controller',
            name='robot_controller',
            output='screen',
        ),

        Node(
            package='solar_agri_control',
            executable='solar_monitor',
            name='solar_monitor',
            output='screen',
        ),
    ])
