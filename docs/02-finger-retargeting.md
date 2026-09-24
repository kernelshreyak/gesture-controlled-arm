# 2 · Finger retargeting

The robot hand is a **Tesollo DG-5F**: five fingers, four joints each, 20 in total. `five_finger_geometry.joint_targets()` converts one frame of landmarks into those 20 angles.

## Bend at each knuckle

For three consecutive landmarks *a → b → c*, the bend at *b* is how far the finger turns away from straight:

```
bend(a, b, c) = π − angle between (a − b) and (c − b)
```

A straight finger gives 0. Each finger chain yields three bends:

| Bend | Landmarks (index finger example) | Human joint |
| --- | --- | --- |
| base | wrist 0 → 5 → 6 | knuckle (MCP) |
| middle | 5 → 6 → 7 | middle joint (PIP) |
| distal | 6 → 7 → 8 | fingertip joint (DIP) |

Because the bends are angles between the hand's own segments, they don't depend on where your hand is, how far it is from the camera, or how it's rotated.

## Mapping bends to robot joints

The DG-5F's joints don't line up exactly with human joints, so each finger has its own gain and limits (radians):

| Finger | Joint 1 | Joint 2 | Joint 3 | Joint 4 |
| --- | --- | --- | --- | --- |
| Thumb | opposition: 0.8 × base, 0…0.89 | rotation: −1.2 × base, −2…0 | 1.1 × middle, 0…1.45 | 1.1 × distal, 0…1.45 |
| Index, middle, ring | spread: held at 0 | 1.3 × base, 0…1.85 | 1.2 × middle, 0…1.45 | 1.2 × distal, 0…1.45 |
| Little | palm fold: 0.3 × base, 0…1.0 | spread: held at 0 | 1.3 × base, 0…1.57 | 0.7 × (middle + distal), 0…1.57 |

The little finger has one extra joint in the palm and only two joints in the finger itself, so its middle and distal bends are combined into one.

## Independence

Each finger reads only its own landmark chain, so bending one finger moves only that finger's four joints. The unit test `test_bending_one_finger_moves_only_that_finger` checks this for all five fingers.

## Smoothing

`five_finger_retarget_node` applies an exponential moving average to the 20 angles (`filter_alpha: 0.5` in `config/experiment.yaml`; lower is smoother but lags more). It then publishes them on `/hand/desired_joint_states` at 20 Hz. If no landmarks arrive for 0.5 s, it stops publishing and the hand holds its pose.

→ Next: [Arm following](03-arm-following.md)
