import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class FakeHand(Node):
    def __init__(self):
        super().__init__('fake_hand_node')
        self.declare_parameter('period', 8.0)
        self.pub = self.create_publisher(Float32MultiArray, '/human_hand/landmarks', 10)
        self.start = self.get_clock().now()
        self.create_timer(0.05, self.publish)

    def publish(self):
        elapsed = (self.get_clock().now() - self.start).nanoseconds * 1e-9
        period = max(0.1, self.get_parameter('period').value)
        points = [[0.5, 0.5, 0.0] for _ in range(21)]
        points[0] = [0.5, 0.8, 0.0]
        for finger, (base, x, y) in enumerate(((1, .40, .68), (5, .43, .56),
                                               (9, .50, .53), (13, .57, .56),
                                               (17, .64, .62))):
            close = 0.5 * (1.0 - math.cos(2.0 * math.pi * elapsed / period + finger * .8))
            points[base] = [x, y, 0.0]
            direction = math.atan2(x - points[0][0], points[0][1] - y)
            for segment, (length, bend) in enumerate(((.09, .65), (.07, .85), (.055, .55)), start=1):
                direction += bend * close
                prior = points[base + segment - 1]
                points[base + segment] = [prior[0] + length * math.sin(direction),
                                          prior[1] - length * math.cos(direction), 0.0]
        drift_x = 0.2 * math.sin(2.0 * math.pi * elapsed / (2.5 * period))
        drift_y = 0.12 * math.sin(2.0 * math.pi * elapsed / (1.7 * period))
        points = [[x + drift_x, y + drift_y - 0.1, z] for x, y, z in points]
        msg = Float32MultiArray()
        msg.data = [value for point in points for value in point]
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = FakeHand()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
