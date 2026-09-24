"""Map MediaPipe's 21 hand landmarks to the DG-5F's twenty joint targets."""

import math


JOINT_NAMES = tuple(f'rj_dg_{finger}_{joint}'
                    for finger in range(1, 6) for joint in range(1, 5))
FINGERS = ((0, 1, 2, 3, 4), (0, 5, 6, 7, 8), (0, 9, 10, 11, 12),
           (0, 13, 14, 15, 16), (0, 17, 18, 19, 20))


def clamp(value, low, high):
    return max(low, min(high, value))


def joint_targets(landmarks):
    """Return targets ordered thumb, index, middle, ring, little; four joints each."""
    if len(landmarks) != 63 or not all(math.isfinite(value) for value in landmarks):
        raise ValueError('Expected 21 finite XYZ hand landmarks')

    def point(index):
        return landmarks[3 * index:3 * index + 3]

    def bend(a, b, c):
        u = [x - y for x, y in zip(point(a), point(b))]
        v = [x - y for x, y in zip(point(c), point(b))]
        length = math.sqrt(sum(x * x for x in u) * sum(x * x for x in v))
        if length < 1e-9:
            raise ValueError('Degenerate finger segment')
        cosine = clamp(sum(x * y for x, y in zip(u, v)) / length, -1.0, 1.0)
        return math.pi - math.acos(cosine)

    result = []
    for finger, (wrist, mcp, pip, dip, tip) in enumerate(FINGERS, start=1):
        base = bend(wrist, mcp, pip)
        middle = bend(mcp, pip, dip)
        distal = bend(pip, dip, tip)
        if finger == 1:  # Thumb: opposing base and three flexion joints.
            result.extend((clamp(base * 0.8, 0.0, 0.89),
                           clamp(-base * 1.2, -2.0, 0.0),
                           clamp(middle * 1.1, 0.0, 1.45),
                           clamp(distal * 1.1, 0.0, 1.45)))
        elif finger == 5:  # Palm fold, spread, then only two flexion joints.
            result.extend((clamp(base * 0.3, 0.0, 1.0), 0.0,
                           clamp(base * 1.3, 0.0, 1.57),
                           clamp((middle + distal) * 0.7, 0.0, 1.57)))
        else:
            result.extend((0.0, clamp(base * 1.3, 0.0, 1.85),
                           clamp(middle * 1.2, 0.0, 1.45),
                           clamp(distal * 1.2, 0.0, 1.45)))
    return result



PALM = (0, 5, 9, 13, 17)


def palm_position(landmarks):
    """Palm centre as (horizontal, vertical) in [-1, 1] from raw camera landmarks.

    The camera faces the user, so the user's right (small image x) gives +1,
    which moves the robot hand to the right as seen from the Gazebo camera.
    Vertical is +1 at the top of the image.
    """
    if len(landmarks) != 63 or not all(math.isfinite(value) for value in landmarks):
        raise ValueError('Expected 21 finite XYZ hand landmarks')
    x = sum(landmarks[3 * index] for index in PALM) / len(PALM)
    y = sum(landmarks[3 * index + 1] for index in PALM) / len(PALM)
    # The outer 15% of the frame is hard to reach while staying tracked, so
    # full travel is reached before the edge.
    return (clamp((0.5 - x) / 0.35, -1.0, 1.0), clamp((0.5 - y) / 0.35, -1.0, 1.0))
