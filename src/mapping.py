import math

HAND_LANDMARKS = {
    "wrist": 0,
    "thumb": (1, 2, 3, 4),
    "index": (5, 6, 7, 8),
    "middle": (9, 10, 11, 12),
    "ring": (13, 14, 15, 16),
    "pinky": (17, 18, 19, 20),
}


def _vec(a, b):
    return (b[0] - a[0], b[1] - a[1], b[2] - a[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(v):
    return math.sqrt(_dot(v, v))


def _angle(a, b, c):
    ab = _vec(b, a)
    cb = _vec(b, c)
    denom = _norm(ab) * _norm(cb)
    if denom == 0:
        return math.pi
    cosv = max(-1.0, min(1.0, _dot(ab, cb) / denom))
    return math.acos(cosv)


def _curl_from_angles(angles):
    # Straight finger => ~pi. Bent finger => smaller angle.
    curls = [(math.pi - ang) / math.pi for ang in angles]
    return max(0.0, min(1.0, sum(curls) / len(curls)))


def landmarks_to_points(landmarks):
    return [(lm.x, lm.y, lm.z) for lm in landmarks]


def to_sim_space(points, scale=2.0, offset=(0.0, 0.0, 0.0)):
    # MediaPipe world landmarks are in meters in camera space.
    # Map camera space to sim space with a simple scale and offset.
    ox, oy, oz = offset
    sim_points = []
    for x, y, z in points:
        sim_points.append((x * scale + ox, -y * scale + oy, -z * scale + oz))
    return sim_points


def finger_curls_from_landmarks(landmarks):
    points = landmarks_to_points(landmarks)

    curls = {}
    for name in ["thumb", "index", "middle", "ring", "pinky"]:
        mcp, pip, dip, tip = HAND_LANDMARKS[name]
        angle1 = _angle(points[mcp], points[pip], points[dip])
        angle2 = _angle(points[pip], points[dip], points[tip])
        curls[name] = _curl_from_angles([angle1, angle2])

    return curls


def finger_joint_targets(curls, joint_scale=None):
    # Simple joint targets (radians) for MCP, PIP, DIP
    targets = {}
    for name, curl in curls.items():
        if joint_scale and name in joint_scale:
            mcp_scale, pip_scale, dip_scale = joint_scale[name]
        elif name == "thumb":
            mcp_scale, pip_scale, dip_scale = (1.2, 1.0, 0.8)
        else:
            mcp_scale, pip_scale, dip_scale = (1.4, 1.7, 1.2)

        mcp = mcp_scale * curl
        pip = pip_scale * curl
        dip = dip_scale * curl
        targets[name] = (mcp, pip, dip)
    return targets
