HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),  # thumb
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),  # index
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),  # middle
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),  # ring
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),  # pinky
]


def draw_hand_skeleton(image, landmarks, line_color=(66, 230, 245), point_color=(245, 117, 66), radius=2):
    import cv2

    height, width = image.shape[:2]
    points = []
    for landmark in landmarks:
        x_px = int(landmark.x * width)
        y_px = int(landmark.y * height)
        points.append((x_px, y_px))
        cv2.circle(image, (x_px, y_px), radius, point_color, -1)

    for start_idx, end_idx in HAND_CONNECTIONS:
        cv2.line(image, points[start_idx], points[end_idx], line_color, 2)
