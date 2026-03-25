# Gesture-Controlled Bionic Arm

This repository is for building a camera-driven bionic arm system controlled by real-time hand tracking. The input side stays consistent across implementations: camera frames are processed with MediaPipe, landmarks are extracted, and those landmarks are mapped into a simulator or robot representation.

The current repository has two active directions:
- a Python hand-tracking and simulation pipeline
- a Webots project for the bionic arm model and world

Future simulator backends such as MuJoCo and Genesis will be added later, but they will reuse the same tracker stage: camera input followed by MediaPipe hand landmark detection.

## Core Flow

1. Capture video from the configured camera device.
2. Run MediaPipe HandLandmarker on each frame.
3. Convert landmarks into joint or pose targets.
4. Drive a simulator or robot model from those targets.

## Main Scripts

- `run_pipeline.py`
  Main Python entry point for the current working pipeline. It reads `config.yaml`, runs the hand tracker, maps landmarks into joint targets, and drives the simplified PyBullet hand.

- `hand_pose_detection_test.py`
  Standalone tracker visualization script. Use this to verify camera input, MediaPipe detection, and on-screen hand skeleton rendering before debugging simulator behavior.

## Python Modules

- `src/hand_tracker.py`
  MediaPipe hand tracking wrapper. Handles camera capture and returns 2D and world landmarks.

- `src/mapping.py`
  Landmark conversion and finger curl mapping logic used by the simulation pipeline.

- `src/sim_pybullet.py`
  Simplified CPU-friendly hand simulation backend built on PyBullet.

- `src/visualization.py`
  Shared drawing helpers for rendering the hand skeleton on video frames.

- `src/config.py`
  YAML config loader used by the scripts.

## Webots Project

The Webots project lives under `bionic_arm_webots/`.

- `bionic_arm_webots/worlds/bionic_arm.wbt`
  Main Webots world for the arm model.

- `bionic_arm_webots/CAD/simplified_bionic_arm.FCStd`
  CAD source for the simplified arm model.

The Webots side is currently separate from the Python simulation pipeline. It is the main place for arm/world modeling and scene iteration.

## Configuration

All runtime configuration is in `config.yaml`.

Important values include:
- camera device path
- frame size
- MediaPipe model path
- tracker confidence thresholds
- simulation timing and motor settings
- landmark-to-simulation scaling

Default camera device:
- `/dev/video2`

## Models

MediaPipe task models live in `models/`.

- `models/hand_landmarker.task`
  Required for the current tracker and pipeline scripts.

See [models/README.md](/home/shreyak/programming/gesture-controlled-arm/models/README.md) for model placement notes.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the main pipeline:

```bash
python run_pipeline.py
```

Run the tracker-only test window:

```bash
python hand_pose_detection_test.py
```

## Notes

- The Python pipeline currently uses PyBullet because it is lightweight and easy to iterate on from Python.
- MuJoCo and Genesis-based implementations can be added later without changing the tracker stage.
- The repository is still evolving, so interfaces and file layout may continue to shift as the simulator backends mature.
