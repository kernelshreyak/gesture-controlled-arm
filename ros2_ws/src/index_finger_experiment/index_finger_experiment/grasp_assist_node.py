"""Lock the cube to the palm while a closed fist surrounds it, and release it on opening.

Gazebo's finger contacts alone let the cube slide out of a live, imprecise
grasp, so a detachable joint holds it once the grasp is plausible. The joint
exists from startup, so this node also detaches it and then unpauses the world.
"""

import numpy as np
import rclpy
from rclpy.node import Node
from ros_gz_interfaces.srv import ControlWorld, SetEntityPose
from sensor_msgs.msg import JointState
from std_msgs.msg import Empty, String
from tf2_msgs.msg import TFMessage

from .arm_ik import ARM_JOINT_NAMES, forward

FLEXION = ('rj_dg_2_2', 'rj_dg_3_2', 'rj_dg_4_2', 'rj_dg_5_3')
GRASP_POINT = np.array((0.045, 0.0, 0.14, 1.0))  # Between the curled fingers, in the hand frame.
CUBE_HOME = (0.71, 0.01, 0.12)


class GraspAssist(Node):
    def __init__(self):
        super().__init__('grasp_assist_node')
        self.declare_parameter('attach_closure', 0.55)
        self.declare_parameter('release_closure', 0.3)
        self.declare_parameter('grasp_radius', 0.05)
        self.closure = 0.0
        self.arm = None
        self.cube = None
        self.state = None
        self.started = False
        self.floor_since = None
        self.attach_pub = self.create_publisher(Empty, '/cube/attach', 10)
        self.detach_pub = self.create_publisher(Empty, '/cube/detach', 10)
        self.control = self.create_client(ControlWorld, '/world/finger_world/control')
        self.set_pose = self.create_client(SetEntityPose, '/world/finger_world/set_pose')
        self.create_subscription(String, '/cube/state', self.on_state, 10)
        self.create_subscription(JointState, '/hand/desired_joint_states', self.on_desired, 10)
        self.create_subscription(JointState, '/hand/joint_states', self.on_actual, 10)
        self.create_subscription(TFMessage, '/world/poses', self.on_poses, 10)
        self.create_timer(0.1, self.update)

    def on_state(self, msg):
        self.state = msg.data

    def on_desired(self, msg):
        positions = dict(zip(msg.name, msg.position))
        if all(name in positions for name in FLEXION):
            self.closure = min(1.0, sum(positions[name] for name in FLEXION) / (1.4 * len(FLEXION)))

    def on_actual(self, msg):
        positions = dict(zip(msg.name, msg.position))
        if all(name in positions for name in ARM_JOINT_NAMES):
            self.arm = [positions[name] for name in ARM_JOINT_NAMES]

    def on_poses(self, msg):
        for transform in msg.transforms:
            if transform.child_frame_id == 'cube':
                t = transform.transform.translation
                self.cube = np.array((t.x, t.y, t.z))

    def update(self):
        if not self.started:
            self.start_world()
            return
        if self.arm is None or self.cube is None:
            return
        attached = self.state == 'attached'
        grasp = (forward(self.arm) @ GRASP_POINT)[:3]
        near = np.linalg.norm(grasp - self.cube) < self.get_parameter('grasp_radius').value
        if not attached and near and self.closure > self.get_parameter('attach_closure').value:
            self.attach_pub.publish(Empty())
            self.get_logger().info('Cube grasped')
        elif attached and self.closure < self.get_parameter('release_closure').value:
            self.detach_pub.publish(Empty())
            self.get_logger().info('Cube released')
        self.reset_if_dropped(attached)

    def start_world(self):
        """Detach the cube while paused, then run the simulation."""
        if self.state != 'detached':
            self.detach_pub.publish(Empty())
            return
        if not self.control.service_is_ready():
            return
        request = ControlWorld.Request()
        request.world_control.pause = False
        self.control.call_async(request)
        self.started = True
        self.get_logger().info('Cube detached; simulation running')

    def reset_if_dropped(self, attached):
        if attached or self.cube[2] > 0.05:
            self.floor_since = None
            return
        now = self.get_clock().now()
        self.floor_since = self.floor_since or now
        if (now - self.floor_since).nanoseconds > 2e9 and self.set_pose.service_is_ready():
            request = SetEntityPose.Request()
            request.entity.name = 'cube'
            request.pose.position.x, request.pose.position.y, request.pose.position.z = CUBE_HOME
            request.pose.orientation.w = 1.0
            self.set_pose.call_async(request)
            self.floor_since = None
            self.get_logger().info('Cube dropped; returned to the table')


def main():
    rclpy.init()
    node = GraspAssist()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
