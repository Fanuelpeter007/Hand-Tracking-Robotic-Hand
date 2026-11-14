"""Tests for vision/hand_geometry.py. Run with: python -m pytest tests"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "vision"))

from hand_geometry import (FINGER_NAMES, bend_percent, encode_command,  # noqa: E402
                           finger_bend_deg, hand_bends, joint_bend_deg)


FINGER_SPREAD = {1: -0.6, 5: -0.2, 9: 0.0, 13: 0.2, 17: 0.4}  # x slope of each finger ray


def finger_direction(base):
    d = np.array([FINGER_SPREAD[base], 1.0, 0.0])
    return d / np.linalg.norm(d)


def straight_hand():
    """21 landmarks with every finger straight: a ray out from the wrist at the origin."""
    pts = np.zeros((21, 3))
    for base in FINGER_SPREAD:
        d = finger_direction(base)
        for k in range(4):
            pts[base + k] = d * (0.06 + 0.025 * k)
    return pts


def bend_finger(pts, base, deg_per_joint):
    """Curl one finger (not the thumb) by the same angle at MCP, PIP and DIP, towards -z."""
    pts = pts.copy()
    d = finger_direction(base)
    down = np.array([0.0, 0.0, -1.0])
    angle = 0.0
    pos = pts[base].copy()
    for k in range(1, 4):
        angle += np.radians(deg_per_joint)
        pos = pos + 0.025 * (np.cos(angle) * d + np.sin(angle) * down)
        pts[base + k] = pos
    return pts


def test_joint_bend_straight_is_zero():
    assert joint_bend_deg([0, 0, 0], [0, 1, 0], [0, 2, 0]) == pytest.approx(0.0, abs=1e-6)


def test_joint_bend_right_angle():
    assert joint_bend_deg([0, 0, 0], [0, 1, 0], [1, 1, 0]) == pytest.approx(90.0)


def test_joint_bend_degenerate_points():
    assert joint_bend_deg([0, 0, 0], [0, 0, 0], [1, 0, 0]) == 0.0


def test_straight_hand_is_open():
    assert hand_bends(straight_hand()) == [0, 0, 0, 0, 0]


def test_curled_index_is_closed_others_open():
    pts = bend_finger(straight_hand(), 5, 80.0)
    assert finger_bend_deg(pts, "index") == pytest.approx(240.0, abs=1e-6)
    bends = dict(zip(FINGER_NAMES, hand_bends(pts)))
    assert bends["index"] == 100
    assert bends["middle"] == 0


def test_bend_percent_clamps_and_scales():
    assert bend_percent(10, 20, 220) == 0
    assert bend_percent(120, 20, 220) == 50
    assert bend_percent(300, 20, 220) == 100


def test_encode_command():
    assert encode_command([0, 25, 50, 75, 100]) == b"0,25,50,75,100\n"
    assert encode_command([-5, 120, 0, 0, 0]) == b"0,100,0,0,0\n"
    with pytest.raises(ValueError):
        encode_command([1, 2, 3])
