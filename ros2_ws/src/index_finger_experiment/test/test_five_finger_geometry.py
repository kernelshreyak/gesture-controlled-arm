"""Bending one synthetic finger must change only that finger's joint targets."""

import math

import pytest

from index_finger_experiment.five_finger_geometry import (
    FINGERS, PALM, joint_targets, palm_position)


def straight_hand():
    """Five colinear finger chains fanned out from a wrist at the origin."""
    points = [[0.0, 0.0, 0.0] for _ in range(21)]
    for finger, chain in enumerate(FINGERS):
        angle = math.radians(-60 + 30 * finger)
        direction = (math.sin(angle), -math.cos(angle), 0.0)
        for step, landmark in enumerate(chain[1:], start=1):
            points[landmark] = [0.1 * step * value for value in direction]
    return points


def bend_finger(points, finger, angle=0.6):
    """Rotate each distal landmark about the previous joint, curling in -z."""
    points = [list(point) for point in points]
    chain = FINGERS[finger]
    for joint in range(1, 4):
        pivot = points[chain[joint]]
        cos, sin = math.cos(angle), math.sin(angle)
        for landmark in chain[joint + 1:]:
            x, y, z = (points[landmark][i] - pivot[i] for i in range(3))
            # Rotate about an axis perpendicular to the finger within the palm plane.
            dx, dy, _ = (points[chain[joint]][i] - points[chain[joint - 1]][i] for i in range(3))
            norm = math.hypot(dx, dy)
            ax, ay = -dy / norm, dx / norm
            along = x * ax + y * ay
            px, py = x - along * ax, y - along * ay
            points[landmark] = [pivot[0] + along * ax + px * cos,
                                pivot[1] + along * ay + py * cos,
                                pivot[2] + z - math.hypot(px, py) * sin]
    return points


def flatten(points):
    return [value for point in points for value in point]


def test_straight_hand_is_open():
    targets = joint_targets(flatten(straight_hand()))
    assert len(targets) == 20
    assert all(abs(value) < 1e-6 for value in targets)


@pytest.mark.parametrize('finger', range(5))
def test_bending_one_finger_moves_only_that_finger(finger):
    open_targets = joint_targets(flatten(straight_hand()))
    bent_targets = joint_targets(flatten(bend_finger(straight_hand(), finger)))
    changed = {index // 4 for index, (a, b) in enumerate(zip(open_targets, bent_targets))
               if abs(a - b) > 1e-6}
    assert changed == {finger}


def test_rejects_bad_input():
    with pytest.raises(ValueError):
        joint_targets([0.0] * 62)
    with pytest.raises(ValueError):
        joint_targets([math.nan] * 63)


def hand_at(x, y):
    """Straight hand translated so its palm centre sits at image (x, y)."""
    points = straight_hand()
    cx = sum(points[index][0] for index in PALM) / len(PALM)
    cy = sum(points[index][1] for index in PALM) / len(PALM)
    return flatten([[px + x - cx, py + y - cy, pz] for px, py, pz in points])


def test_centred_hand_is_neutral():
    assert palm_position(hand_at(0.5, 0.5)) == pytest.approx((0.0, 0.0))


def test_palm_position_directions_and_bounds():
    assert palm_position(hand_at(0.2, 0.5))[0] > 0      # User's right is small raw x.
    assert palm_position(hand_at(0.5, 0.2))[1] > 0      # Top of the image is up.
    assert palm_position(hand_at(-3.0, 3.0)) == pytest.approx((1.0, -1.0))
