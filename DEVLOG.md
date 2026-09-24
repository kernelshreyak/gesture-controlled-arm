# Development log — 2026-09-24

## User goal and current stopping point

The user rejected the former two-finger Panda gripper demo and requested a realistic five-finger hand that tracks each human finger. The Franka Panda arm must remain in Gazebo. The user explicitly removed the object-grasp requirement, so the cube and tactile path are out of scope for this stage. They asked to stop at a reasonable point and hand the work to Claude because Codex credits are nearly exhausted.

The current **headless synthetic-input pipeline works**: a combined Panda + five-finger hand model loads in Gazebo, publishes 20 hand joint states, and all five fingers visibly change joint state in response to independent fake landmark motion. The live webcam and Gazebo GUI combination has **not** been verified after this migration. Do not overstate its status.

## Model and license

- Selected the [Tesollo DG-5F ROS 2/Gazebo hand](https://github.com/tesollodelto/dg5f_ros2), commit `9e9af1221cc82e4613a6f18210288f7782b53011`, BSD 3-Clause. It has five fingers and 20 actuated joints. Its right-hand URDF, 56 visual/collision mesh files, license, and provenance are vendored under `ros2_ws/src/index_finger_experiment/models/panda_five/`.
- `scripts/build_panda_five_model.py` converts the vendored DG-5F URDF with `gz sdf -p`, combines it with the existing Panda arm model, removes the old two-finger gripper, attaches the DG-5F by a fixed joint, and adds 20 Gazebo position controllers. It writes `models/panda_five/model.sdf`.
- The generated SDF uses `model://panda/meshes/...` for Panda arm meshes and `model://panda_five/meshes/...` for hand meshes. The experiment launch configures `GZ_SIM_RESOURCE_PATH` to the package's models directory. The hand's collision elements are intentionally removed by the generator for this motion-only stage; visual meshes and inertial data remain.
- The world `ros2_ws/src/index_finger_experiment/worlds/panda_world.sdf` now includes `model://panda_five` and has no cube. Its Gazebo camera pose was moved closer to the hand, but this GUI framing is unverified.

## ROS path and source files

- `experiment.launch.py` starts Gazebo, a bridge for 20 finger target topics and Panda joint state, a fake or MediaPipe landmark source, `five_finger_retarget_node`, and `five_finger_command_node`. The old grasp/tactile nodes are no longer launched.
- `five_finger_geometry.py` maps MediaPipe's 21 normalized XYZ landmarks to 20 DG-5F joint targets: thumb, index, middle, ring, little; four joints each. Each finger uses its own landmark chain. The index/middle/ring spreading joints are held at zero, while their flexion joints are tracked. This mapping is approximate and uncalibrated.
- `five_finger_retarget_node.py` smooths and publishes `/hand/desired_joint_states`; `five_finger_command_node.py` publishes 20 Float64 targets to `/panda_five/rj_dg_X_Y/target`. `/hand/joint_states` is actual Gazebo state.
- `fake_hand_node.py` now synthesizes five independently phased finger motions. `mediapipe_hand_node.py` has a five-color overlay and says `TRACKING 5 FINGERS`.
- `run_live.sh` now checks both model assets, regenerates the combined Panda + DG-5F SDF, builds the ROS package, and launches `experiment.launch.py input:=camera gui:=true` with the camera preview and MediaPipe task model. It has not been run against the new five-finger model.

## Verification done

From `ros2_ws/`, `source /opt/ros/lyrical/setup.bash && colcon build --symlink-install --packages-select index_finger_experiment` succeeded. A headless launch with `ros2 launch index_finger_experiment experiment.launch.py input:=fake gui:=false` loaded the combined model. `/hand/joint_states` contained the Panda arm plus `rj_dg_1_1` through `rj_dg_5_4` (all 20 hand joints). A 12-second ROS probe observed movement in all five representative joints:

| Finger joint | Desired range (rad) | Actual range (rad) |
| --- | ---: | ---: |
| Thumb `rj_dg_1_1` | 0.00–0.52 | -0.27–0.33 |
| Index `rj_dg_2_2` | 0.00–0.84 | 0.13–1.17 |
| Middle `rj_dg_3_2` | 0.00–0.84 | 0.14–1.02 |
| Ring `rj_dg_4_2` | 0.00–0.84 | 0.12–1.00 |
| Little `rj_dg_5_1` | 0.00–0.52 | 0.07–0.51 |

The actual motion is rough and overshoots targets, especially at the thumb and index. The Gazebo position controller currently uses `p_gain=20`, `d_gain=1.5`, and effort limits ±7.5. This requires visual inspection and tuning. No long-running simulator process was intended to remain after the handoff; check before launching again.

## Remaining work for Claude

1. ~~**Fix the root README.**~~ Done (Claude, 2026-09-24): README now describes the DG-5F demo, its verified headless status, and its unverified live status. It still describes the obsolete two-finger gripper, cube, tactile control, and index-only mapping. A patch to replace it was attempted but failed validation, so none of that documentation update applied. Describe the DG-5F demo and its present limits honestly.
2. Run `./run_live.sh` in a desktop session and verify the MediaPipe camera preview plus the Gazebo GUI. Confirm the 5-finger mesh is visible, mounted on the Panda, and that moving each human finger drives the matching simulated finger. The local model file exists at `models/hand_landmarker.task`, and the webcam is `/dev/video0` with a by-id link under `/dev/v4l/by-id/`.
3. Tune the hand controller gains and visual camera pose based on the GUI result. The headless probe shows joint overshoot. If the hand's physical orientation or mount placement looks wrong, change `scripts/build_panda_five_model.py`, regenerate `model.sdf`, and rebuild.
4. ~~Add a meaningful automated check~~ Done (Claude, 2026-09-24): `test/test_five_finger_geometry.py` bends each synthetic finger alone and asserts only its four targets change; run `python3 -m pytest test` in the package (7 passed). Original item: add a meaningful automated check that bending only one synthetic finger changes only that finger's target joints. Current code has no new test for the five-finger mapping.
5. Optionally clean up obsolete legacy gripper entry points/configuration after the new live demo is proven. The old files are unused in `experiment.launch.py` but intentionally retained so prior migration work is not lost.

## Useful commands

```bash
source /opt/ros/lyrical/setup.bash
python3 scripts/build_panda_five_model.py
cd ros2_ws
colcon build --symlink-install --packages-select index_finger_experiment
source install/setup.bash
ros2 launch index_finger_experiment experiment.launch.py input:=fake gui:=false
```

For the intended GUI and webcam run, from the repository root: `./run_live.sh` (or `./run_live.sh /dev/video0`). Stop launches with Ctrl+C. `gz sdf -k` on the world alone reports unresolved `model://panda_five` because it does not use the launch's Gazebo resource callback; the actual Gazebo launch loaded the model successfully.

## Fix: hand spawned at the Panda base (Claude, 2026-09-24)

The first live GUI run showed only the Panda arm, slumped. Cause: the converted DG-5F root link `rl_dg_mount` had no `<pose>`, so it spawned at the model origin; the fixed joint's pose only moves the joint frame, so the hand stayed rigidly ~1 m from the flange and its weight dragged the arm down. `build_panda_five_model.py` now gives `rl_dg_mount` the pose `0 0 0.03 0 0 0` relative to `panda_hand`. A headless check afterwards put `rl_dg_mount` 3 cm from `panda_hand` with the arm upright. Visual confirmation in the GUI is still pending, and so is the hand's roll about the flange.

## Arm yaw/pitch tracking, lighting, finger controller (Claude, 2026-09-24)

The user asked to keep the Panda and the hand, but make the arm follow simple horizontal and vertical hand movement, and to improve the lighting. (They briefly asked to remove the Panda, then withdrew that request.)

- `five_finger_geometry.arm_targets()` maps the palm centre (landmarks 0, 5, 9, 13, 17) to `panda_joint1` (yaw) and `panda_joint2` (pitch around −0.785). A probe confirmed that a more negative joint2 raises the hand and a positive joint1 swings it towards +y (right in the default GUI view). The retarget node smooths these separately (`arm_filter_alpha` 0.15), and the command node publishes them to `/arm/joint1_target` and `/arm/joint2_target`.
- The world previously had no lights (ambient only). It now has a shadow-casting directional key light, a directional fill light, a point rim light, and a floor material.
- Finger controllers switched to `use_velocity_commands` (p 12, ±4 rad/s). Headless fake run: index/middle/ring reach exactly the 0.84 rad target (previously overshot to 1.17). Remaining: a brief once-per-cycle blip near fully open, likely at a joint limit.
- Fake hand now drifts across the frame to exercise the arm. Tests: 10 pass. The GUI result (lighting, arm direction, hand orientation) is still unverified.

## Raised pose, arm IK, grab parked, cleanup, docs (Claude, 2026-09-24)

- **Raised, palm-to-viewer pose.** The user chose "fingers up, palm facing the viewer". `arm_ik.py` has Panda FK (modified DH + flange + −45° hand yaw + 3 cm mount; matches Gazebo to 1 mm) and damped-least-squares IK with a null-space pull to `READY`. `READY` is the IK solution for hand (0.42, 0, 0.62), fingers up, palm +x, that leaves the most room before any joint limit. The first solution hit the joint-5 limit and was off by 2 cm at the edge of the range.
- **Arm following.** The palm centre (landmarks 0, 5, 9, 13, 17) maps to hand y ±0.25 m and z 0.62→0.46 m, with the palm always facing +x. The retarget node solves IK each tick and publishes 7 arm and 20 finger targets. All arm joints now use velocity-command control (p 6, ±2 rad/s); torque control had sagged 0.16–0.24 rad under the hand's weight.
- **Grab (disabled).** The world has a table and a 4 cm cube, and the hand collisions are back on, with friction. Raw finger contact did not lift the cube: it slid and fell in a scripted headless test. `grasp_assist_node` locks it with a Gazebo DetachableJoint when the fist closes near the cube. The user asked to park this: `GRASP_ASSIST = False` in the generator (with it on, the cube starts attached and the world must start paused), and the launch arg `grasp_assist` defaults to false. The node was never verified end-to-end; the `/world/poses` pose bridge and its frame names were untested when work stopped.
- **Little finger.** The mapping now uses DG-5F joint 5_1 as a palm fold, 5_2 as spread (held at 0) and 5_3/5_4 as flexion, matching the URDF axes.
- **GUI camera** moved close to the raised hand: `1.12 -0.2 0.66 0 0.04 2.86`.
- **Cleanup.** Removed the legacy gripper nodes, the old index-only `geometry.py`, `control_test.launch.py`, `cad/`, and the standalone tracker (`hand_pose_detection_test.py`, `src/`, `config.yaml`). The tracked ones are recoverable from git; a tarball of everything removed was also written to that session's scratchpad.
- **Docs.** `docs/` has an overview plus pages on landmarks, finger retargeting, arm following and the simulation, linked from the README.
- **Verification.** 14 unit tests pass. Headless fake run: the hand orientation stayed identity (palm +x, fingers up) while moving in y/z, arm joints matched their targets, and finger joints were within 0.01 rad after settling. The live camera + GUI view of this version has not been checked.
