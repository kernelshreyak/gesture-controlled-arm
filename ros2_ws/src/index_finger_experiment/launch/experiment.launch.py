import os

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('index_finger_experiment')
    workspace = os.path.dirname(os.path.dirname(get_package_prefix('index_finger_experiment')))
    camera_python = os.path.join(workspace, '.venv', 'bin', 'python')
    config = os.path.join(share, 'config', 'experiment.yaml')
    world = os.path.join(share, 'worlds', 'panda_world.sdf')
    resource_paths = os.pathsep.join(filter(None, [os.environ.get('GZ_SIM_RESOURCE_PATH'),
                                                   os.path.join(share, 'models')]))
    input_source = LaunchConfiguration('input')
    gui = LaunchConfiguration('gui')
    # The world starts paused; grasp_assist_node detaches the cube, then runs it.
    grasp_assist = LaunchConfiguration('grasp_assist')
    # Grasp assist (off) needs GRASP_ASSIST in build_panda_five_model.py. The
    # world then starts paused; grasp_assist_node detaches the cube and runs it.
    run_flag = PythonExpression(["'' if '", grasp_assist, "' == 'true' else '-r'"])
    finger_joints = [f'rj_dg_{finger}_{joint}'
                     for finger in range(1, 6) for joint in range(1, 5)]
    return LaunchDescription([
        DeclareLaunchArgument('input', default_value='fake', description='fake or camera'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('camera_device', default_value='auto', description='auto, /dev/v4l/by-id/... or /dev/videoN'),
        DeclareLaunchArgument('show_preview', default_value='true'),
        DeclareLaunchArgument('model_path', default_value=''),
        DeclareLaunchArgument('grasp_assist', default_value='false', description='Experimental cube grab'),
        ExecuteProcess(cmd=['gz', 'sim', run_flag, '-s', world], additional_env={'GZ_SIM_RESOURCE_PATH': resource_paths},
                       condition=IfCondition(PythonExpression(["'", gui, "' == 'false'"])), output='screen'),
        ExecuteProcess(cmd=['gz', 'sim', run_flag, world],
                       additional_env={'GZ_SIM_RESOURCE_PATH': resource_paths},
                       condition=IfCondition(gui), output='screen'),
        Node(package='ros_gz_bridge', executable='parameter_bridge', output='screen',
             arguments=[
                 '/world/finger_world/model/panda_five/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',
                 '/world/finger_world/pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
                 '/cube/attach@std_msgs/msg/Empty]gz.msgs.Empty',
                 '/cube/detach@std_msgs/msg/Empty]gz.msgs.Empty',
                 '/cube/state@std_msgs/msg/String[gz.msgs.StringMsg',
                 '/world/finger_world/control@ros_gz_interfaces/srv/ControlWorld',
                 '/world/finger_world/set_pose@ros_gz_interfaces/srv/SetEntityPose',
             ] + [f'/panda/gz_arm_joint{index}@std_msgs/msg/Float64]gz.msgs.Double'
                  for index in range(1, 8)]
               + [f'/panda_five/{joint}/target@std_msgs/msg/Float64]gz.msgs.Double'
                  for joint in finger_joints],
             remappings=[('/world/finger_world/model/panda_five/joint_state', '/hand/joint_states'),
                         ('/world/finger_world/pose/info', '/world/poses')]),
        Node(package='index_finger_experiment', executable='fake_hand_node',
             condition=IfCondition(PythonExpression(["'", input_source, "' == 'fake'"]))),
        Node(package='index_finger_experiment', executable='mediapipe_hand_node',
             prefix=camera_python,
             parameters=[{'camera_device': LaunchConfiguration('camera_device'),
                          'model_path': LaunchConfiguration('model_path'),
                          'show_preview': LaunchConfiguration('show_preview')}],
             condition=IfCondition(PythonExpression(["'", input_source, "' == 'camera'"]))),
        Node(package='index_finger_experiment', executable='five_finger_retarget_node',
             parameters=[config, {'grab_reach': PythonExpression(["'", grasp_assist, "' == 'true'"])}]),
        Node(package='index_finger_experiment', executable='five_finger_command_node'),
        Node(package='index_finger_experiment', executable='grasp_assist_node', output='screen',
             condition=IfCondition(grasp_assist)),
    ])
