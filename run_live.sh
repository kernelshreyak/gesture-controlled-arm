#!/usr/bin/env bash
set -eo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
workspace="$repo_root/ros2_ws"
mediapipe_model="$repo_root/models/hand_landmarker.task"
hand_model_dir="$workspace/src/index_finger_experiment/models/panda_five"
camera_device="${1:-auto}"

if [[ "$camera_device" == "--help" || "$camera_device" == "-h" ]]; then
  echo "Usage: ./run_live.sh [camera_device]"
  echo "camera_device defaults to auto; pass /dev/videoN or a /dev/v4l/by-id/ path to choose one."
  exit 0
fi

if [[ $# -gt 1 ]]; then
  echo "Usage: ./run_live.sh [camera_device]" >&2
  exit 2
fi

if [[ ! -f /opt/ros/lyrical/setup.bash ]]; then
  echo "ROS 2 Lyrical is required at /opt/ros/lyrical." >&2
  exit 1
fi
if [[ ! -x "$workspace/.venv/bin/python" ]]; then
  echo "Camera Python environment is missing at $workspace/.venv." >&2
  echo "Create it with: uv venv --python /usr/bin/python3.14 --system-site-packages ros2_ws/.venv" >&2
  exit 1
fi
if [[ ! -f "$mediapipe_model" ]]; then
  echo "MediaPipe model is missing at $mediapipe_model." >&2
  echo "Download it using the command in README.md under Install and build." >&2
  exit 1
fi
if [[ ! -f "$hand_model_dir/dg5f_right.urdf" || ! -d "$hand_model_dir/meshes/dg5f_right/visual" ]]; then
  echo "Vendored five-finger DG-5F model is missing from $hand_model_dir." >&2
  exit 1
fi
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  echo "A desktop display is required for the camera preview and Gazebo GUI." >&2
  exit 1
fi

# ROS environment setup scripts may use variables before assigning them.
source /opt/ros/lyrical/setup.bash
if ! command -v gz >/dev/null; then
  echo "Gazebo Sim is required to generate and display the five-finger model." >&2
  exit 1
fi
"$workspace/.venv/bin/python" -c 'import cv2, mediapipe, rclpy' || {
  echo "Install MediaPipe in ros2_ws/.venv as described in README.md." >&2
  exit 1
}

python3 "$repo_root/scripts/build_panda_five_model.py"
cd "$workspace"
colcon build --symlink-install --packages-select index_finger_experiment
source install/setup.bash

echo "Starting MediaPipe five-finger preview and Gazebo Panda hand. Press Ctrl+C to stop."
exec ros2 launch index_finger_experiment experiment.launch.py \
  input:=camera gui:=true "camera_device:=$camera_device" show_preview:=true \
  "model_path:=$mediapipe_model"
