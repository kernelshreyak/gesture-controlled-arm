# Gesture-controlled five-finger robot hand

A webcam tracks your hand with MediaPipe, and a five-finger [Tesollo DG-5F](https://github.com/tesollodelto/dg5f_ros2) hand on a [Franka Panda arm](https://github.com/pmh5050/panda_ign) copies it in Gazebo Sim over ROS 2. Each simulated finger bends with the matching finger of yours, and the arm moves the raised hand left/right and up/down as your hand moves around the camera frame.

📖 **[How the tracking works → docs/](docs/README.md)**

**Status.** With the synthetic input, run without the Gazebo window: all 20 finger joints track their targets to within 0.01 rad, and the arm follows the palm position. The live webcam + GUI run is being tuned. Finger mapping gains are approximate and not calibrated per user. The cube grab is experimental and **disabled**.

## Install and build

Developed with ROS 2 Lyrical, Gazebo Sim 10.5, Python 3.14, `ros_gz_bridge`, a USB C270 webcam and MediaPipe 0.10.35. From the repository root:

```bash
source /opt/ros/lyrical/setup.bash
uv venv --python /usr/bin/python3.14 --system-site-packages ros2_ws/.venv
uv pip install --python ros2_ws/.venv/bin/python -r requirements.txt
curl -fL -o models/hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

The camera node runs in this `uv` environment, which can also import the system ROS Python modules. The MediaPipe model is ignored by Git.

## Run

```bash
./run_live.sh              # auto-selects a USB camera
./run_live.sh /dev/video0  # or choose one
```

This regenerates the robot model, builds the ROS package, and opens the camera preview and the Gazebo GUI. Stop with Ctrl+C.

Without a webcam, use the synthetic hand (from `ros2_ws/`, after `source install/setup.bash`):

```bash
ros2 launch index_finger_experiment experiment.launch.py input:=fake gui:=true
```

Useful topics: `/human_hand/landmarks`, `/hand/desired_joint_states` (targets) and `/hand/joint_states` (actual Gazebo state).

## Repository layout

| Path | Contents |
| --- | --- |
| `run_live.sh` | One-command live demo |
| `docs/` | Presentable explanation of the tracking pipeline |
| `scripts/build_panda_five_model.py` | Builds the Panda + DG-5F Gazebo model and its controllers |
| `ros2_ws/src/index_finger_experiment/` | ROS 2 package: nodes, launch file, world, config, tests, vendored models |
| `models/` | MediaPipe model (downloaded) |
| `AGENTS.md`, `DEVLOG.md` | Handoff notes and development log |

Package nodes: `mediapipe_hand_node` (camera), `fake_hand_node` (synthetic input), `five_finger_retarget_node` (landmarks → 20 finger + 7 arm targets), `five_finger_command_node` (targets → Gazebo), and `grasp_assist_node` (experimental, not launched by default).

## Tuning

- `config/experiment.yaml`: `filter_alpha` (finger smoothing), `arm_filter_alpha` (arm smoothing), `landmark_timeout`.
- `five_finger_geometry.py`: per-finger gains and limits; the palm-to-arm mapping.
- `arm_ik.py`: hand travel (`SIDEWAYS`, `HIGH`, `VIEW_LOW_Z`) and the raised resting pose.
- `scripts/build_panda_five_model.py`: controller gains. Rerun it and rebuild after changes (`run_live.sh` does this).

## Tests

```bash
cd ros2_ws/src/index_finger_experiment && python3 -m pytest test
```

The tests check that bending one finger moves only that finger's joints, that the palm position maps in the right directions, and that the arm IK reaches the whole input range without sudden jumps.

## Experimental cube grab (disabled)

The world has a table and a red cube. Grab mode pitches the palm down over the cube when you lower your hand, and a Gazebo detachable joint locks the cube to the palm while your fist is closed around it. It isn't reliable yet. To try it, set `GRASP_ASSIST = True` in `scripts/build_panda_five_model.py`, regenerate the model, and launch with `grasp_assist:=true`.

## Licenses

Panda model: BSD ([provenance](ros2_ws/src/index_finger_experiment/models/panda/UPSTREAM.md)). DG-5F model: BSD 3-Clause, commit `9e9af12` ([provenance](ros2_ws/src/index_finger_experiment/models/panda_five/UPSTREAM.md)).
