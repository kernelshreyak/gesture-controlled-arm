import os
import time

# Helps suppress Qt font warnings if system fonts are available.
if os.path.isdir("/usr/share/fonts"):
    os.environ.setdefault("QT_QPA_FONTDIR", "/usr/share/fonts")
# Reduce noisy OpenCV logging.
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")

import cv2

from src.config import load_config
from src.hand_tracker import HandLandmarkTracker
from src.mapping import (
    finger_curls_from_landmarks,
    finger_joint_targets,
    landmarks_to_points,
    to_sim_space,
)
from src.sim_pybullet import SimpleHandSim
from src.visualization import draw_hand_skeleton

def main():
    cfg = load_config()
    camera = cfg["camera"]
    window = cfg["window"]
    model = cfg["model"]
    tracker_cfg = cfg["tracker"]
    mapping_cfg = cfg["mapping"]
    sim_cfg = cfg["sim"]

    tracker = HandLandmarkTracker(
        model_path=model["hand_landmarker"],
        camera_device=camera["device"],
        width=camera["width"],
        height=camera["height"],
        max_hands=tracker_cfg["max_hands"],
        min_detection_confidence=tracker_cfg["min_detection_confidence"],
        min_presence_confidence=tracker_cfg["min_presence_confidence"],
        min_tracking_confidence=tracker_cfg["min_tracking_confidence"],
    )
    sim = SimpleHandSim(
        use_gui=sim_cfg["use_gui"],
        motor_force=sim_cfg.get("motor_force", 6.0),
        max_velocity=sim_cfg.get("max_velocity", 10.0),
    )

    tracker.start()
    sim.connect()
    sim.build()

    cv2.namedWindow(window["name"], cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window["name"], window["width"], window["height"])

    try:
        while True:
            frame, hand_landmarks, hand_world_landmarks = tracker.read()
            if frame is None:
                time.sleep(0.01)
                continue

            if hand_world_landmarks:
                sim_points = to_sim_space(
                    landmarks_to_points(hand_world_landmarks[0]),
                    scale=mapping_cfg["scale"],
                    offset=tuple(mapping_cfg["offset"]),
                )
                _ = sim_points

            if hand_landmarks:
                curls = finger_curls_from_landmarks(hand_landmarks[0])
                targets = finger_joint_targets(curls, joint_scale=mapping_cfg.get("joint_scale"))
                sim.set_finger_targets(targets)
                draw_hand_skeleton(frame, hand_landmarks[0])

            cv2.imshow(window["name"], frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            try:
                if cv2.getWindowProperty(window["name"], cv2.WND_PROP_VISIBLE) < 1:
                    break
            except cv2.error:
                break

            substeps = sim_cfg.get("substeps", 1)
            for _ in range(substeps):
                sim.step(sim_cfg["dt"])
    finally:
        tracker.close()
        sim.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
from src.visualization import draw_hand_skeleton
