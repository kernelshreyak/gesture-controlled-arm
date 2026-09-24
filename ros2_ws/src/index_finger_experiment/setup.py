from glob import glob
import os
from setuptools import setup

package_name = 'index_finger_experiment'
model_files = [
    (os.path.join('share', package_name, os.path.dirname(path)), [path])
    for path in glob('models/**/*', recursive=True) if os.path.isfile(path)
]

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/worlds', glob('worlds/*.sdf')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ] + model_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Shreyak',
    maintainer_email='shreyak@example.com',
    description='Five-finger hand teleoperation on a Panda arm in Gazebo',
    license='Apache-2.0',
    entry_points={'console_scripts': [
        'fake_hand_node = index_finger_experiment.fake_hand_node:main',
        'mediapipe_hand_node = index_finger_experiment.mediapipe_hand_node:main',
        'five_finger_retarget_node = index_finger_experiment.five_finger_retarget_node:main',
        'five_finger_command_node = index_finger_experiment.five_finger_command_node:main',
        'grasp_assist_node = index_finger_experiment.grasp_assist_node:main',
    ]},
)
