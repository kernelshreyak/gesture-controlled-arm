"""The arm IK must reach every hand target across the tracked range, smoothly."""

import math

import numpy as np
import pytest

from index_finger_experiment.arm_ik import LOWER, READY, UPPER, forward, hand_target, solve


def test_ready_pose_is_raised_palm_forward():
    transform = forward(READY)
    position, rotation = hand_target(0.0, 1.0)
    assert np.allclose(transform[:3, 3], position, atol=1e-3)
    assert np.allclose(transform[:3, :3], rotation, atol=1e-3)
    assert transform[2, 2] > 0.99      # Fingers point up.
    assert transform[0, 0] > 0.99      # Palm faces +x, towards the viewer.


def test_view_mode_keeps_palm_to_viewer():
    for vertical in (-1.0, 0.0, 1.0):
        _, rotation = hand_target(1.0, vertical)
        assert np.allclose(rotation, np.eye(3))


def test_grab_reach_turns_palm_down():
    _, rotation = hand_target(0.0, -1.0, grab_reach=True)
    assert rotation[2, 0] < -0.99      # Palm normal points down.


@pytest.mark.parametrize('grab_reach', (False, True))
def test_tracks_a_sweep_of_the_whole_range(grab_reach):
    q = np.array(READY)
    path = ([(h, 1.0) for h in np.linspace(0, 1, 10)] + [(1.0, v) for v in np.linspace(1, -1, 20)]
            + [(h, -1.0) for h in np.linspace(1, -1, 20)] + [(-1.0, v) for v in np.linspace(-1, 1, 20)]
            + [(h, 1.0) for h in np.linspace(-1, 0, 10)] + [(0.0, v) for v in np.linspace(1, -1, 20)])
    for horizontal, vertical in path:
        position, rotation = hand_target(horizontal, vertical, grab_reach)
        new_q, error = solve(position, rotation, q, rest=READY, iterations=40)
        assert error < 0.01
        assert np.linalg.norm(forward(new_q)[:3, :3] - rotation) < 0.2
        assert np.max(np.abs(new_q - q)) < 0.25     # No sudden flips between configurations.
        assert np.all(new_q >= LOWER) and np.all(new_q <= UPPER)
        q = new_q
