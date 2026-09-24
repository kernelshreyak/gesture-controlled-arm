# 3 · Arm following

The arm keeps the hand **raised with the palm facing you**. Moving your hand around the camera frame moves the robot hand the same way.

## Palm position → hand target

1. **Palm centre.** Average of the wrist and the four knuckles (landmarks 0, 5, 9, 13, 17), which stays steady while the fingers move.
2. **Normalise.** Map the palm centre to `horizontal, vertical ∈ [−1, 1]`. The middle of the frame is 0. Full travel is reached 15% before the edge, so you don't have to leave the frame to reach the limits.
3. **Smooth.** Apply an exponential moving average with `arm_filter_alpha: 0.15`, so the arm glides instead of jittering.
4. **Target.** Convert to a hand pose in the world:

| Your hand | Robot hand |
| --- | --- |
| Left ↔ right | Moves sideways ±25 cm |
| Up ↕ down | Moves between 62 cm and 46 cm high |
| Anywhere | Fingers up, palm toward the viewer (+x) |

The camera faces you, so your right is the robot's right as seen in the Gazebo view, like a mirror.

## Inverse kinematics

`arm_ik.py` turns the target hand pose into seven Panda joint angles:

- **Forward kinematics:** the Panda's standard (modified DH) parameters, then the flange, the 45° hand rotation and the 3 cm mount. Checked against Gazebo to the millimetre.
- **Solver:** damped least squares on position plus orientation error. Each 50 ms tick it runs 15 iterations, starting from the previous solution, so the motion stays continuous.
- **Null-space pull:** the Panda has one joint more than it needs. That spare freedom gently pulls the arm back toward its resting pose, so it doesn't drift into odd postures.
- **Resting pose:** of the IK solutions for "hand raised, palm forward", the one with the most room before any joint limit. A sweep across the whole input range stays within 5 mm of target without sudden jumps (`test_tracks_a_sweep_of_the_whole_range`).

## Grab mode (disabled)

An experimental mode (`grasp_assist:=true`) lets you lower your hand to pitch the palm down over the cube on the table and grab it. It's switched off for now; see the main README for how to enable it.

→ Next: [Simulation and ROS graph](04-simulation.md)
