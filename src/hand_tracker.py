import os
import time

# Reduce noisy logs from OpenCV/TF/MediaPipe and fix Qt font warnings if possible.
if os.path.isdir("/usr/share/fonts"):
    os.environ.setdefault("QT_QPA_FONTDIR", "/usr/share/fonts")
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("GLOG_minloglevel", "2")

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandLandmarkTracker:
    def __init__(
        self,
        model_path,
        camera_device,
        width,
        height,
        max_hands,
        min_detection_confidence,
        min_presence_confidence,
        min_tracking_confidence,
    ):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                "HandLandmarker model not found. Place the model at "
                f"{model_path} (e.g., hand_landmarker.task)."
            )

        self.model_path = model_path
        self.camera_device = camera_device
        self.width = width
        self.height = height
        self.max_hands = max_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_presence_confidence = min_presence_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self._cap = None
        self._landmarker = None
        self._start_time = None

    def start(self):
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=self.max_hands,
            min_hand_detection_confidence=self.min_detection_confidence,
            min_hand_presence_confidence=self.min_presence_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)

        self._cap = cv2.VideoCapture(self.camera_device, cv2.CAP_V4L2)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open camera device {self.camera_device}")

        self._start_time = time.time()

    def close(self):
        if self._cap is not None:
            self._cap.release()
        if self._landmarker is not None:
            self._landmarker.close()
        self._cap = None
        self._landmarker = None

    def read(self):
        if self._cap is None or self._landmarker is None:
            raise RuntimeError("Tracker not started. Call start() first.")

        success, frame = self._cap.read()
        if not success:
            return None, None, None

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int((time.time() - self._start_time) * 1000)
        results = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        return frame, results.hand_landmarks, results.hand_world_landmarks
