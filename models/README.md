# MediaPipe Models

This project uses MediaPipe Tasks models in `.task` format.

## Required Model
Place the HandLandmarker model at:

- `models/hand_landmarker.task`

## Where to Get It
Download the HandLandmarker model from the official MediaPipe Models page and save it with the exact filename above.

## Notes
- The script `hand_pose_detection_test.py` expects the model at the path above.
- If you want a lighter model, you can use a lite hand landmarker model and update `MODEL_PATH` in `hand_pose_detection_test.py` accordingly.
