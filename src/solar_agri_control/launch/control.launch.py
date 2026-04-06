from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='solar_agri_control',
            executable='robot_controller',
            name='robot_controller',
            output='screen',
            parameters=[{
                'wheel_radius': 0.10,
                'wheel_base':   0.56,
                'max_speed':    1.5,
            }],
        ),
        Node(
            package='solar_agri_control',
            executable='solar_monitor',
            name='solar_monitor',
            output='screen',
            parameters=[{
                'publish_rate':   1.0,
                'panel_voc':      21.0,
                'panel_isc':      5.5,
                'battery_cap_wh': 100.0,
            }],
        ),
    ])
