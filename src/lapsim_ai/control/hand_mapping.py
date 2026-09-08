"""Absolute hand targets, deliberately distinct from keyboard rate commands."""
from dataclasses import dataclass
from math import atan2, hypot, isfinite, pi
from .instrument import InstrumentControl, InstrumentLimits


def clamp(value, low=-1.0, high=1.0):
    return min(high, max(low, value))


@dataclass(frozen=True)
class MappingSettings:
    wrist_range: float = 0.20
    scale_range: float = 0.50
    roll_range: float = pi / 3
    minimum_palm: float = 0.02
    image_aspect: float = 1.0

    def __post_init__(self):
        if not all(isfinite(v) and v > 0 for v in vars(self).values()):
            raise ValueError("Mapping settings must be finite and positive")


@dataclass(frozen=True)
class InstrumentTarget:
    """Absolute offsets [-1,1] around neutral; jaw is absolute [0,1].

    Invalid targets contain no pose. Do not feed these into the rate controller.
    """
    side: str
    valid: bool = False
    yaw: float | None = None
    pitch: float | None = None
    insertion: float | None = None
    rotation: float | None = None
    jaw: float | None = None

    def to_control(self, neutral=None, limits=None):
        """Pure conversion to the existing pose contract; no controller mutation."""
        if not self.valid:
            return None
        limits = limits or InstrumentLimits()
        neutral = (neutral or InstrumentControl()).limited(limits)
        values = {}
        for name in ("yaw", "pitch", "insertion", "rotation"):
            value = getattr(self, name)
            if value is None or not isfinite(value):
                raise ValueError("Nonfinite target")
            value = clamp(value)
            base = getattr(neutral, name)
            low, high = getattr(limits, name)
            values[name] = base + value * (high - base if value >= 0 else base - low)
        return InstrumentControl(**values, jaw=self.jaw).limited(limits)


class HandMapper:
    def __init__(self, settings=None):
        self.settings = settings or MappingSettings()

    def map(self, state):
        if state.handedness not in ("Left", "Right"):
            raise ValueError("Unknown physical handedness")
        invalid = InstrumentTarget(state.handedness.upper())
        cal = state.calibration
        if (not state.tracked or not state.valid or not cal.ready
                or state.wrist is None or state.middle_mcp is None
                or cal.neutral_palm is None or state.normalized_pinch is None):
            return invalid
        cfg = self.settings
        wx, wy = state.wrist
        nx, ny = cal.neutral_wrist
        px = (state.middle_mcp[0] - wx) * cfg.image_aspect
        py = state.middle_mcp[1] - wy
        bx, by = cal.neutral_palm
        bx *= cfg.image_aspect
        if not all(isfinite(v) for v in (wx, wy, nx, ny, px, py, bx, by, state.normalized_pinch)):
            return invalid
        scale, baseline = hypot(px, py), hypot(bx, by)
        if min(scale, baseline) < cfg.minimum_palm:
            return invalid
        angle = (atan2(py, px) - atan2(by, bx) + pi) % (2 * pi) - pi
        # Mirrored image: +x right, +y down; rig external handle lies at +Z.
        # +yaw moves handle +X/tip -X; +pitch moves handle -Y/tip +Y.
        # Thus right/down hand displacement uses +yaw/+pitch, with no extra inversion.
        return InstrumentTarget(
            state.handedness.upper(), True,
            clamp((wx - nx) / cfg.wrist_range),
            clamp((wy - ny) / cfg.wrist_range),
            clamp((1 - scale / baseline) / cfg.scale_range),
            clamp(-angle / cfg.roll_range),  # Preview clockwise -> negative rig Z rotation.
            clamp(state.normalized_pinch, 0, 1))
