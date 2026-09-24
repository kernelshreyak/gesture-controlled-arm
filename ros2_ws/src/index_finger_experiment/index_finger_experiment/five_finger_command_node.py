"""Send the hand's twenty joint targets and the arm's seven joint targets to Gazebo."""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64

from .five_finger_geometry import JOINT_NAMES


class FiveFingerCommand(Node):
    def __init__(self):
        super().__init__('five_finger_command_node')
        self.target_publishers = {
            name: self.create_publisher(Float64, f'/panda_five/{name}/target', 10)
            for name in JOINT_NAMES
        }
        self.target_publishers.update({
            f'panda_joint{index}': self.create_publisher(Float64, f'/panda/gz_arm_joint{index}', 10)
            for index in range(1, 8)
        })
        self.create_subscription(JointState, '/hand/desired_joint_states', self.on_target, 10)

    def on_target(self, msg):
        positions = dict(zip(msg.name, msg.position))
        for name, pub in self.target_publishers.items():
            value = positions.get(name)
            if value is not None and math.isfinite(value):
                pub.publish(Float64(data=value))


def main():
    rclpy.init()
    node = FiveFingerCommand()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
