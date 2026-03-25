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

from src.config import load_config
from src.visualization import draw_hand_skeleton


cfg = load_config()
camera = cfg["camera"]
model = cfg["model"]
window = cfg["window"]
tracker_cfg = cfg["tracker"]

MODEL_PATH = model["hand_landmarker"]
WINDOW_NAME = window["name"]
CAMERA_DEVICE = camera["device"]
FRAME_WIDTH = camera["width"]
FRAME_HEIGHT = camera["height"]

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        "HandLandmarker model not found. Place the model at "
        f"{MODEL_PATH} (e.g., hand_landmarker.task)."
    )

base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=tracker_cfg["max_hands"],
    min_hand_detection_confidence=tracker_cfg["min_detection_confidence"],
    min_hand_presence_confidence=tracker_cfg["min_presence_confidence"],
    min_tracking_confidence=tracker_cfg["min_tracking_confidence"],
)

# Use the 'with' statement for proper resource management
cap = cv2.VideoCapture(CAMERA_DEVICE, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
start_time = time.time()

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, FRAME_WIDTH, FRAME_HEIGHT)

try:
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera device {CAMERA_DEVICE}")
    with vision.HandLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                time.sleep(0.01)
                continue

            # Recolor image from BGR to RGB for MediaPipe processing
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            timestamp_ms = int((time.time() - start_time) * 1000)
            results = landmarker.detect_for_video(mp_image, timestamp_ms)

            if results.hand_landmarks:
                for hand_landmarks in results.hand_landmarks:
                    draw_hand_skeleton(frame, hand_landmarks)

            # Display the feed
            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            try:
                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except cv2.error:
                break
finally:
    cap.release()
    cv2.destroyAllWindows()
