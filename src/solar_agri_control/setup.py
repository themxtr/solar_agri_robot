from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'solar_agri_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Solar Agri Robot',
    maintainer_email='admin@solar-agri-robot.local',
    description='Control nodes for the Solar Agricultural Robot',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'robot_controller = solar_agri_control.robot_controller:main',
            'solar_monitor    = solar_agri_control.solar_monitor:main',
            'task_simulator   = solar_agri_control.task_simulator:main',
            'crop_marker_publisher = solar_agri_control.crop_marker_publisher:main',
            'field_navigator  = solar_agri_control.field_navigator:main',
        ],
    },
)
