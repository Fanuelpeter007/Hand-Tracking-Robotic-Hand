"""Finger bend from MediaPipe hand landmarks.

MediaPipe Hands returns 21 landmarks per hand:

    0 wrist
    1-4   thumb  (CMC, MCP, IP, tip)
    5-8   index  (MCP, PIP, DIP, tip)
    9-12  middle
    13-16 ring
    17-20 pinky

The bend at a joint is 180 degrees minus the angle between the two bones that
meet there, so a straight joint has 0 degrees of bend. A finger's total bend is
the sum over its joints. It is mapped to a percentage between a calibrated
"open" and "closed" value.

This module only uses NumPy, so it can be tested without a camera.
"""

import numpy as np

FINGER_NAMES = ("thumb", "index", "middle", "ring", "pinky")

# Joints whose bend is summed for each finger, as (previous, joint, next) landmark triples.
FINGER_JOINTS = {
    "thumb": ((1, 2, 3), (2, 3, 4)),
    "index": ((0, 5, 6), (5, 6, 7), (6, 7, 8)),
    "middle": ((0, 9, 10), (9, 10, 11), (10, 11, 12)),
    "ring": ((0, 13, 14), (13, 14, 15), (14, 15, 16)),
    "pinky": ((0, 17, 18), (17, 18, 19), (18, 19, 20)),
}

# Total bend in degrees for an open and a closed hand. Tune these with
# hand_tracking.py --show-degrees for your camera and hand.
DEFAULT_OPEN_DEG = {"thumb": 15.0, "index": 20.0, "middle": 20.0, "ring": 20.0, "pinky": 20.0}
DEFAULT_CLOSED_DEG = {"thumb": 110.0, "index": 230.0, "middle": 230.0, "ring": 230.0, "pinky": 220.0}


def joint_bend_deg(a, b, c):
    """Bend at point b, in degrees, for the path a -> b -> c. Straight = 0."""
    u = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    v = np.asarray(c, dtype=float) - np.asarray(b, dtype=float)
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu == 0.0 or nv == 0.0:
        return 0.0
    cos_angle = np.clip(np.dot(u, v) / (nu * nv), -1.0, 1.0)
    return 180.0 - float(np.degrees(np.arccos(cos_angle)))


def finger_bend_deg(landmarks, finger):
    """Total bend of one finger in degrees. landmarks is a (21, 3) array."""
    pts = np.asarray(landmarks, dtype=float)
    return sum(joint_bend_deg(pts[i], pts[j], pts[k]) for i, j, k in FINGER_JOINTS[finger])


def bend_percent(bend_deg, open_deg, closed_deg):
    """Map a bend in degrees to 0..100 percent between the open and closed values."""
    if closed_deg == open_deg:
        return 0
    pct = 100.0 * (bend_deg - open_deg) / (closed_deg - open_deg)
    return int(round(min(100.0, max(0.0, pct))))


def hand_bends(landmarks, open_deg=None, closed_deg=None):
    """Bend in percent for all five fingers, in FINGER_NAMES order."""
    open_deg = open_deg or DEFAULT_OPEN_DEG
    closed_deg = closed_deg or DEFAULT_CLOSED_DEG
    return [bend_percent(finger_bend_deg(landmarks, f), open_deg[f], closed_deg[f])
            for f in FINGER_NAMES]


def encode_command(bends):
    """Serial line for the Arduino: 'thumb,index,middle,ring,pinky\\n'."""
    if len(bends) != len(FINGER_NAMES):
        raise ValueError("expected 5 finger values")
    return (",".join(str(int(min(100, max(0, b)))) for b in bends) + "\n").encode("ascii")
