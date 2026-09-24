# Project handoff instructions

Read [DEVLOG.md](DEVLOG.md) before editing. It records the current five-finger migration, verified behavior, and remaining work.

The user's current goal is a visually convincing five-finger hand mounted on the Franka Panda in ROS 2/Gazebo, driven independently by all five MediaPipe fingers, with the hand raised and its palm facing the viewer. The arm follows the palm's position in the camera (horizontal and vertical only). Keep the Panda arm present. A cube grab exists but is deliberately disabled (`GRASP_ASSIST = False`, launch `grasp_assist:=false`); keep its code for a later fix. The single `run_live.sh` command should start camera tracking, ROS 2, and the Gazebo GUI. User-facing docs live in `docs/`; keep them in sync with behaviour changes.

The working tree contains pre-existing uncommitted migration work. Preserve it. The active five-finger model is generated from the Panda SDF and the vendored Tesollo DG-5F URDF by `scripts/build_panda_five_model.py`; rerun that script after changing its inputs or controller settings, then rebuild the ROS package.

Do not claim the live visual result is verified until the camera and GUI have actually been tested. The headless synthetic path has been verified; see the devlog for its measurements. Keep the root README and `docs/` accurate when behaviour changes.
