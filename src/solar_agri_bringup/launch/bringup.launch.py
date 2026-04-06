import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # ---- package paths ----
    pkg_desc  = get_package_share_directory('solar_agri_description')
    pkg_ctrl  = get_package_share_directory('solar_agri_control')

    urdf_file = os.path.join(pkg_desc, 'urdf', 'solar_agri_robot.urdf.xacro')

    robot_description = ParameterValue(
        Command(['xacro ', urdf_file]),
        value_type=str
    )

    # ---- launch args ----
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),

        # Robot state publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': robot_description,
                'use_sim_time': use_sim_time,
            }]
        ),

        # Include control launch (robot_controller + solar_monitor)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ctrl, 'launch', 'control.launch.py')
            )
        ),
    ])
