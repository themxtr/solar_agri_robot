import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_description = get_package_share_directory('solar_agri_description')
    rviz_config = os.path.join(pkg_description, 'config', 'sim_display.rviz')

    return LaunchDescription([
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config]
        )
    ])
