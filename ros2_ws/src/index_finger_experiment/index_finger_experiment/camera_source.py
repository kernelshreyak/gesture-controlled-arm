"""Choose an image-producing V4L2 camera, preferring stable USB device links."""

from glob import glob
import os


def camera_candidates(requested):
    if requested != 'auto':
        return [requested]

    paths = (sorted(glob('/dev/v4l/by-id/usb-*-video-index0')) +
             sorted(glob('/dev/v4l/by-path/*usb*-video-index0')) +
             sorted(glob('/dev/video[0-9]*'), key=lambda p: int(p.split('video')[-1])))
    # by-id and by-path often point to the same /dev/videoN device.
    candidates = []
    seen = set()
    for path in paths:
        resolved = os.path.realpath(path)
        if resolved not in seen:
            candidates.append(path)
            seen.add(resolved)
    return candidates


def open_camera(cv2, requested, width, height):
    candidates = camera_candidates(requested)
    for path in candidates:
        source = int(path) if str(path).isdecimal() else path
        cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            ok, _ = cap.read()
            if ok:
                return cap, path
        cap.release()
    raise RuntimeError(
        f'No image-producing camera found for {requested!r}. Tried: {candidates}. '
        'Set camera_device to a /dev/v4l/by-id/...-video-index0 link or /dev/videoN.'
    )
