# MediaPipe model

The camera node needs the MediaPipe HandLandmarker model at `models/hand_landmarker.task`. It is ignored by Git. Download it with:

```bash
curl -fL -o models/hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

`run_live.sh` passes this path to the ROS launch automatically.
