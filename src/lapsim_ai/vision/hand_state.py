"""Pure extraction; coordinates refer to the image supplied to the detector."""

from dataclasses import dataclass
from math import hypot, isfinite, dist
from statistics import median
try:
    from .palm_orientation import PalmFrame, palm_frame
except ImportError:  # Existing direct webcam_demo.py entry point.
    from palm_orientation import PalmFrame, palm_frame


@dataclass(frozen=True)
class HandState:
    handedness: str
    wrist: tuple[float, float]
    index_fingertip: tuple[float, float]
    thumb_tip: tuple[float, float]
    pinch_distance: float
    middle_mcp: tuple[float, float] | None = None
    palm_depth_scale: float | None = None
    knuckle_line: tuple[float, float] | None = None
    palm_orientation: PalmFrame | None = None
    palm_center: tuple[float, float] | None = None


def extract_hand_state(landmarks, handedness, *, mirrored_input: bool, image_aspect=1.0):
    """Correct physical identity for mirrored input; never guess missing identity.

    x/y are clamped to [0, 1]. Pinch is 2D Euclidean distance in these
    normalized image axes (0 to sqrt(2)), not a physical length or gesture.
    """
    if handedness not in ("Left", "Right"):
        return None
    if mirrored_input:
        handedness = {"Left": "Right", "Right": "Left"}[handedness]

    def xy(index):
        point = landmarks[index]
        if not (isfinite(point.x) and isfinite(point.y)):
            raise ValueError("Hand landmark coordinates must be finite")
        return (min(1.0, max(0.0, point.x)), min(1.0, max(0.0, point.y)))

    wrist, index_tip, thumb_tip = xy(0), xy(8), xy(4)
    pinch = hypot(index_tip[0] - thumb_tip[0], index_tip[1] - thumb_tip[1])
    # Z is wrist-relative, NOT whole-hand camera distance. Combine apparent palm
    # size with relative Z to compensate foreshortening; never use fingertips.
    # This remains an inferred nonmetric scale proxy, not measured 3D depth.
    points = {i: (landmarks[i].x * image_aspect, landmarks[i].y,
                  getattr(landmarks[i], "z", 0.0) * image_aspect) for i in (0, 5, 9, 13, 17)}
    pairs = ((0, 5), (0, 9), (0, 13), (0, 17), (5, 17), (5, 13), (9, 17))
    depth_scale = (median(dist(points[a], points[b]) for a, b in pairs)
                   if all(isfinite(v) for p in points.values() for v in p) else None)
    if depth_scale is not None and depth_scale <= 1e-6:
        depth_scale = None
    index_knuckle, pinky_knuckle = xy(5), xy(17)
    line = (pinky_knuckle[0] - index_knuckle[0], pinky_knuckle[1] - index_knuckle[1])
    orientation = (palm_frame(list(points.values()))
                   if all(hasattr(landmarks[i], 'z') for i in points) else None)
    # Translation steering: distribute influence across the stable palm skeleton.
    # Wrist 40%, each MCP 15%; thumb/fingertips never enter this estimate.
    palm = [xy(i) for i in (0,5,9,13,17)]
    center = tuple(sum(w*p[axis] for w,p in zip((.4,.15,.15,.15,.15),palm)) for axis in (0,1))
    return HandState(handedness, wrist, index_tip, thumb_tip, pinch, xy(9), depth_scale, line, orientation, center)
