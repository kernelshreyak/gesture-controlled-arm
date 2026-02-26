import os
import time

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = "models/hand_landmarker.task"

HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),  # thumb
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),  # index
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),  # middle
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),  # ring
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),  # pinky
]


def draw_hand_skeleton(image, landmarks, line_color=(66, 230, 245), point_color=(245, 117, 66), radius=2):
    height, width = image.shape[:2]
    points = []
    for landmark in landmarks:
        x_px = int(landmark.x * width)
        y_px = int(landmark.y * height)
        points.append((x_px, y_px))
        cv2.circle(image, (x_px, y_px), radius, point_color, -1)

    for start_idx, end_idx in HAND_CONNECTIONS:
        cv2.line(image, points[start_idx], points[end_idx], line_color, 2)


if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        "HandLandmarker model not found. Place the model at "
        f"{MODEL_PATH} (e.g., hand_landmarker.task)."
    )

base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,
)

# Use the 'with' statement for proper resource management
cap = cv2.VideoCapture(0)  # 0 refers to the default webcam
start_time = time.time()

with vision.HandLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
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
        cv2.imshow("MediaPipe Hand Detection (HandLandmarker)", frame)

        # Break the loop when 'q' is pressed
        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
