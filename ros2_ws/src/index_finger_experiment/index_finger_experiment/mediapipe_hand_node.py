"""Camera/MediaPipe adapter. All other nodes work without this dependency."""

import time
import os

if os.path.isdir('/usr/share/fonts'):
    os.environ.setdefault('QT_QPA_FONTDIR', '/usr/share/fonts')

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

from .camera_source import open_camera


HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
)
FINGER_COLORS = (
    (220, 120, 255),  # thumb
    (80, 220, 80),    # index
    (255, 180, 40),   # middle
    (80, 180, 255),   # ring
    (220, 120, 80),   # little
)


class MediaPipeHand(Node):
    def __init__(self):
        super().__init__('mediapipe_hand_node')
        self.declare_parameter('camera_device', 'auto')
        self.declare_parameter('model_path', '')
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('show_preview', True)
        self.declare_parameter('mirror_preview', True)
        import cv2
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        self.cv2 = cv2
        self.mp = mp
        model_path = self.get_parameter('model_path').value
        if not model_path:
            raise ValueError('Set model_path to a downloaded hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        camera = self.get_parameter('camera_device').value
        try:
            self.cap, self.camera_path = open_camera(
                cv2, camera, self.get_parameter('width').value,
                self.get_parameter('height').value)
        except Exception:
            self.landmarker.close()
            raise
        self.get_logger().info(f'Using camera {self.camera_path}')
        self.preview_enabled = self.get_parameter('show_preview').value
        self.window_name = 'MediaPipe hand tracking'
        if self.preview_enabled:
            if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
                self.cap.release()
                self.landmarker.close()
                raise RuntimeError('No desktop display; launch with show_preview:=false')
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, 960, 720)
        self.start = time.monotonic()
        self.last_timestamp = -1
        self.pub = self.create_publisher(Float32MultiArray, '/human_hand/landmarks', 10)
        self.create_timer(1.0 / 30.0, self.read)

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            self.get_logger().warning('Camera frame unavailable', throttle_duration_sec=2.0)
            return
        rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
        timestamp = max(self.last_timestamp + 1, int((time.monotonic() - self.start) * 1000))
        self.last_timestamp = timestamp
        result = self.landmarker.detect_for_video(image, timestamp)
        if result.hand_landmarks:
            msg = Float32MultiArray()
            msg.data = [v for lm in result.hand_landmarks[0] for v in (lm.x, lm.y, lm.z)]
            self.pub.publish(msg)
        if self.preview_enabled:
            self.show_frame(frame, result.hand_landmarks)

    def show_frame(self, frame, hands):
        height, width = frame.shape[:2]
        if hands:
            points = [(int(lm.x * width), int(lm.y * height)) for lm in hands[0]]
            for start, end in HAND_CONNECTIONS:
                finger = (end - 1) // 4 if end in range(1, 21) else None
                color = FINGER_COLORS[finger] if finger is not None else (190, 190, 190)
                self.cv2.line(frame, points[start], points[end], color, 2)
            for index, point in enumerate(points):
                finger = (index - 1) // 4 if index else None
                self.cv2.circle(frame, point, 4 if index else 5,
                                FINGER_COLORS[finger] if finger is not None else (255, 255, 255), -1)
        if self.get_parameter('mirror_preview').value:
            frame = self.cv2.flip(frame, 1)  # Display only; published landmarks stay in camera coordinates.
        status = 'TRACKING 5 FINGERS' if hands else 'NO HAND DETECTED'
        self.cv2.putText(frame, f'{status} | {self.camera_path}', (12, 28),
                         self.cv2.FONT_HERSHEY_SIMPLEX, 0.58, (30, 255, 30) if hands else (0, 160, 255), 2)
        self.cv2.putText(frame, 'Q: hide preview (ROS tracking continues)', (12, height - 15),
                         self.cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        self.cv2.imshow(self.window_name, frame)
        if self.cv2.waitKey(1) & 0xFF == ord('q'):
            self.hide_preview()
        elif self.cv2.getWindowProperty(self.window_name, self.cv2.WND_PROP_VISIBLE) < 1:
            self.hide_preview()

    def hide_preview(self):
        if self.preview_enabled:
            self.preview_enabled = False
            self.cv2.destroyWindow(self.window_name)

    def destroy_node(self):
        self.hide_preview()
        self.cap.release()
        self.landmarker.close()
        return super().destroy_node()


def main():
    rclpy.init()
    node = MediaPipeHand()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
