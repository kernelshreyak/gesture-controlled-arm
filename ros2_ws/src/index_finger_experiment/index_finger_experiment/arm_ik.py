"""Panda kinematics for placing the DG-5F hand: forward kinematics and a small IK solver.

The hand frame is the DG-5F mount: +z points along the fingers and +x out of
the palm. Transforms use Craig's modified DH parameters for the Panda, followed
by the flange offset, the Panda hand's -45 degree yaw and the 3 cm hand mount.
"""

import math

import numpy as np


DH = ((0.0, 0.333, 0.0), (0.0, 0.0, -math.pi / 2), (0.0, 0.316, math.pi / 2),
      (0.0825, 0.0, math.pi / 2), (-0.0825, 0.384, -math.pi / 2),
      (0.0, 0.0, math.pi / 2), (0.088, 0.0, math.pi / 2))
LOWER = np.array((-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973))
UPPER = np.array((2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973))
MARGIN = 0.05


def _dh(a, d, alpha, theta):
    ca, sa, ct, st = math.cos(alpha), math.sin(alpha), math.cos(theta), math.sin(theta)
    return np.array(((ct, -st, 0.0, a), (st * ca, ct * ca, -sa, -d * sa),
                     (st * sa, ct * sa, ca, d * ca), (0.0, 0.0, 0.0, 1.0)))


_TOOL = _dh(0.0, 0.107, 0.0, -math.pi / 4) @ np.array(
    ((1.0, 0, 0, 0), (0, 1.0, 0, 0), (0, 0, 1.0, 0.03), (0, 0, 0, 1.0)))


def forward(q):
    """Return the 4x4 world transform of the hand mount for seven joint angles."""
    transform = np.eye(4)
    for (a, d, alpha), theta in zip(DH, q):
        transform = transform @ _dh(a, d, alpha, theta)
    return transform @ _TOOL


def hand_rotation(pitch):
    """Fingers up and palm facing +x at pitch 0; fingers +x and palm down at pi/2."""
    c, s = math.cos(pitch), math.sin(pitch)
    return np.array(((c, 0.0, s), (0.0, 1.0, 0.0), (-s, 0.0, c)))


def _error(q, position, rotation, orientation_weight):
    transform = forward(q)
    rotation_now = transform[:3, :3]
    angular = 0.5 * sum(np.cross(rotation_now[:, i], rotation[:, i]) for i in range(3))
    return np.concatenate((position - transform[:3, 3], orientation_weight * angular))


def solve(position, rotation, seed, rest=None, iterations=40, orientation_weight=0.5):
    """Damped least-squares IK from ``seed``; returns (joints, position error in m)."""
    q = np.clip(np.asarray(seed, dtype=float), LOWER + MARGIN, UPPER - MARGIN)
    rest = q.copy() if rest is None else np.asarray(rest, dtype=float)
    position = np.asarray(position, dtype=float)
    for _ in range(iterations):
        error = _error(q, position, rotation, orientation_weight)
        jacobian = np.empty((6, 7))
        for joint in range(7):
            nudged = q.copy()
            nudged[joint] += 1e-6
            jacobian[:, joint] = (error - _error(nudged, position, rotation,
                                                 orientation_weight)) / 1e-6
        damping = 0.02
        inverse = jacobian.T @ np.linalg.inv(jacobian @ jacobian.T + damping * np.eye(6))
        step = inverse @ error + 0.05 * (np.eye(7) - inverse @ jacobian) @ (rest - q)
        largest = np.max(np.abs(step))
        if largest > 0.2:
            step *= 0.2 / largest
        q = np.clip(q + step, LOWER + MARGIN, UPPER - MARGIN)
        if np.linalg.norm(error) < 1e-4:
            break
    return q, float(np.linalg.norm(forward(q)[:3, 3] - position))


ARM_JOINT_NAMES = tuple(f'panda_joint{index}' for index in range(1, 8))
# Raised pose: hand at (0.42, 0, 0.62), fingers up, palm +x. Of the IK solutions
# found, this one leaves the most room before any joint limit.
READY = (1.4491, -1.2222, -1.2183, -2.4595, 2.0579, 1.5102, -0.0292)
HIGH = (0.42, 0.62)       # Hand x and z with the user's hand at the top of the image.
LOW = (0.56, 0.17)        # ...and at the bottom, palm down over the cube.
VIEW_LOW_Z = 0.46         # Lowest hand height when not reaching for the cube.
SIDEWAYS = 0.25           # Hand y travel at the image's left/right edges, in metres.


def hand_target(horizontal, vertical, grab_reach=False):
    """Hand position and rotation for inputs in [-1, 1]; vertical 1 is the top.

    By default the palm always faces the viewer so the fingers stay visible.
    With ``grab_reach``, lowering the hand also pitches it palm-down over the cube.
    """
    horizontal = max(-1.0, min(1.0, horizontal))
    down = (1.0 - max(-1.0, min(1.0, vertical))) / 2.0
    if not grab_reach:
        return ((HIGH[0], SIDEWAYS * horizontal, HIGH[1] + (VIEW_LOW_Z - HIGH[1]) * down),
                hand_rotation(0.0))
    position = (HIGH[0] + (LOW[0] - HIGH[0]) * down, SIDEWAYS * horizontal,
                HIGH[1] + (LOW[1] - HIGH[1]) * down)
    return position, hand_rotation(math.pi / 2 * down)
