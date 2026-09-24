# 1 · Camera and landmarks

`mediapipe_hand_node` opens the webcam and runs Google's **MediaPipe HandLandmarker** on every frame.

| Setting | Value |
| --- | --- |
| Capture | 640 × 480, polled at 30 Hz |
| Model | `models/hand_landmarker.task`, video mode (tracks between frames) |
| Hands | 1 (the first detected) |
| Confidence thresholds | 0.5 detection / presence / tracking |

## The 21 landmarks

Each landmark is `(x, y, z)`: `x` and `y` are normalised image coordinates (0–1, origin top-left), and `z` is relative depth.

```
                 8   12  16  20        ← tips
                 7   11  15  19        ← DIP
         4       6   10  14  18        ← PIP
          3      5    9  13  17        ← MCP (knuckles)
           2
            1
                    0                  ← wrist
       thumb  index middle ring little
```

Every finger is a chain of five points starting at the wrist:

| Finger | Chain |
| --- | --- |
| Thumb | 0 → 1 → 2 → 3 → 4 |
| Index | 0 → 5 → 6 → 7 → 8 |
| Middle | 0 → 9 → 10 → 11 → 12 |
| Ring | 0 → 13 → 14 → 15 → 16 |
| Little | 0 → 17 → 18 → 19 → 20 |

## What gets published

When a hand is visible, the node publishes all 63 numbers as a `std_msgs/Float32MultiArray` on `/human_hand/landmarks`. When no hand is visible, it publishes nothing, and the rest of the pipeline holds its last pose.

The preview window draws each finger in its own colour and shows `TRACKING 5 FINGERS` or `NO HAND DETECTED`. The preview is **mirrored** so it behaves like a mirror, but the published landmarks stay in raw camera coordinates.

No webcam? `input:=fake` swaps in `fake_hand_node`, which publishes a synthetic hand that curls each finger in turn and drifts around the frame.

→ Next: [Finger retargeting](02-finger-retargeting.md)
