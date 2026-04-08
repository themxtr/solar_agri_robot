import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_simulation = get_package_share_directory('solar_agri_simulation')
    pkg_description = get_package_share_directory('solar_agri_description')
    pkg_navigation = get_package_share_directory('solar_agri_navigation')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    world_file = os.path.join(pkg_simulation, 'worlds', 'field.world')
    urdf_file = os.path.join(pkg_description, 'urdf', 'solar_agri_robot.urdf.xacro')
    nav2_params_file = os.path.join(pkg_navigation, 'config', 'nav2_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')

    robot_description = ParameterValue(
        Command(['xacro ', urdf_file]),
        value_type=str
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='true', description='Start RViz2 if true'),

        # 1. Start Gazebo Server with the field world
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
            ),
            launch_arguments={'world': world_file}.items()
        ),

        # 2. Start Gazebo Client
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
            )
        ),

        # 3. Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description, 'use_sim_time': use_sim_time}]
        ),

        # 4. Spawn Robot in Gazebo
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-topic', 'robot_description', '-entity', 'solar_agri_robot', '-x', '-2.0', '-y', '0.0', '-z', '0.2'],
            output='screen'
        ),

        # 5. Start async SLAM Toolbox mapping
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'odom_frame': 'odom',
                'map_frame': 'map',
                'base_frame': 'base_footprint',
                'scan_topic': '/scan',
                'mode': 'mapping'
            }]
        ),

        # 6. Start Nav2 using our custom parameters (which forces Dijkstra on global planner)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_navigation, 'launch', 'navigation.launch.py')
            ),
            launch_arguments={'use_sim_time': use_sim_time, 'params_file': nav2_params_file}.items()
        ),
        
        # 6.5 Publish 3D Crop Markers for RViz
        Node(
            package='solar_agri_control',
            executable='crop_marker_publisher',
            name='crop_marker_publisher',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}]
        ),

        # 6.6 Autonomous Field Navigator
        Node(
            package='solar_agri_control',
            executable='field_navigator',
            name='field_navigator',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}]
        ),

        # 7. RViz visualization (Conditional)
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', os.path.join(pkg_description, 'config', 'sim_display.rviz')],
            parameters=[{'use_sim_time': use_sim_time}],
            condition=IfCondition(use_rviz)
        )
    ])
