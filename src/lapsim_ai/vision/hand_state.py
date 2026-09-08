"""Pure extraction; coordinates refer to the image supplied to the detector."""

from dataclasses import dataclass
from math import hypot, isfinite


@dataclass(frozen=True)
class HandState:
    handedness: str
    wrist: tuple[float, float]
    index_fingertip: tuple[float, float]
    thumb_tip: tuple[float, float]
    pinch_distance: float
    middle_mcp: tuple[float, float] | None = None


def extract_hand_state(landmarks, handedness, *, mirrored_input: bool):
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
    return HandState(handedness, wrist, index_tip, thumb_tip, pinch, xy(9))
