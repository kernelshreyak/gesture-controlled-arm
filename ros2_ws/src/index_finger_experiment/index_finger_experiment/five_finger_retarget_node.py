"""Publish DG-5F finger targets and Panda arm targets from MediaPipe landmarks."""

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32MultiArray

from .arm_ik import ARM_JOINT_NAMES, READY, hand_target, solve
from .five_finger_geometry import JOINT_NAMES, clamp, joint_targets, palm_position


class FiveFingerRetarget(Node):
    def __init__(self):
        super().__init__('five_finger_retarget_node')
        self.declare_parameter('filter_alpha', 0.5)
        self.declare_parameter('landmark_timeout', 0.5)
        self.declare_parameter('arm_filter_alpha', 0.15)
        self.declare_parameter('grab_reach', False)
        self.target = None
        self.palm = None
        self.arm = np.array(READY)
        self.last_input = None
        self.pub = self.create_publisher(JointState, '/hand/desired_joint_states', 10)
        self.create_subscription(Float32MultiArray, '/human_hand/landmarks', self.on_landmarks, 10)
        self.create_timer(0.05, self.publish)

    def on_landmarks(self, msg):
        try:
            raw = joint_targets(msg.data)
            palm = palm_position(msg.data)
        except ValueError as exc:
            self.get_logger().warning(str(exc), throttle_duration_sec=2.0)
            return
        alpha = clamp(self.get_parameter('filter_alpha').value, 0.0, 1.0)
        self.target = raw if self.target is None else [
            alpha * value + (1 - alpha) * previous
            for value, previous in zip(raw, self.target)]
        # The arm is heavier and should glide, so the palm gets stronger smoothing.
        arm_alpha = clamp(self.get_parameter('arm_filter_alpha').value, 0.0, 1.0)
        self.palm = palm if self.palm is None else tuple(
            arm_alpha * value + (1 - arm_alpha) * previous
            for value, previous in zip(palm, self.palm))
        self.last_input = self.get_clock().now()

    def publish(self):
        if self.last_input is None:
            return
        now = self.get_clock().now()
        if (now - self.last_input).nanoseconds * 1e-9 > self.get_parameter('landmark_timeout').value:
            return  # Gazebo holds the last targets while the hand is out of view.
        position, rotation = hand_target(*self.palm, bool(self.get_parameter('grab_reach').value))
        self.arm, _ = solve(position, rotation, self.arm, rest=READY, iterations=15)
        msg = JointState()
        msg.header.stamp = now.to_msg()
        msg.name = list(JOINT_NAMES) + list(ARM_JOINT_NAMES)
        msg.position = list(self.target) + self.arm.tolist()
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = FiveFingerRetarget()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
