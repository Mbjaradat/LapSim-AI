"""Absolute hand targets, deliberately distinct from keyboard rate commands."""
from dataclasses import dataclass
from math import atan2, hypot, isfinite, pi
from .instrument import InstrumentControl, InstrumentLimits


def clamp(value, low=-1.0, high=1.0):
    return min(high, max(low, value))


@dataclass(frozen=True)
class MappingSettings:
    yaw_range: float = 0.08  # Full command at 8% image width from neutral.
    pitch_range: float = 0.08  # Full command at 8% image height from neutral.
    wrist_dead_zone: float = 0.003
    depth_range: float = 0.15  # Full command at +/-15% palm scale from neutral.
    depth_dead_zone: float = 0.02  # Ignore +/-2% neutral-relative scale changes.
    roll_range: float = 25 * pi / 180
    minimum_palm: float = 0.02
    image_aspect: float = 1.0

    def __post_init__(self):
        if not all(isfinite(v) and v > 0 for v in vars(self).values()):
            raise ValueError("Mapping settings must be finite and positive")
        if self.wrist_dead_zone >= min(self.yaw_range, self.pitch_range) or self.depth_dead_zone >= self.depth_range:
            raise ValueError("Dead zones must be smaller than movement ranges")


def relative_command(delta, full_range, dead_zone):
    return clamp(max(0, abs(delta) - dead_zone) / (full_range - dead_zone)) * (1 if delta >= 0 else -1)


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
                or state.wrist is None or state.knuckle_line is None
                or cal.neutral_knuckles is None or state.normalized_pinch is None
                or state.palm_depth_scale is None or cal.neutral_depth_scale is None):
            return invalid
        cfg = self.settings
        wx, wy = state.wrist
        nx, ny = cal.neutral_wrist
        px, py = state.knuckle_line
        px *= cfg.image_aspect
        bx, by = cal.neutral_knuckles
        bx *= cfg.image_aspect
        if not all(isfinite(v) for v in (wx, wy, nx, ny, px, py, bx, by, state.normalized_pinch,
                                        state.palm_depth_scale, cal.neutral_depth_scale)):
            return invalid
        scale, baseline = hypot(px, py), hypot(bx, by)
        if min(scale, baseline) < cfg.minimum_palm or min(state.palm_depth_scale, cal.neutral_depth_scale) <= 1e-6:
            return invalid
        angle = (atan2(py, px) - atan2(by, bx) + pi) % (2 * pi) - pi
        # Mirrored image: +x right, +y down; rig external handle lies at +Z.
        # +yaw moves handle +X/tip -X; +pitch moves handle -Y/tip +Y.
        # Thus right/down hand displacement uses +yaw/+pitch, with no extra inversion.
        return InstrumentTarget(
            state.handedness.upper(), True,
            relative_command(wx - nx, cfg.yaw_range, cfg.wrist_dead_zone),
            relative_command(wy - ny, cfg.pitch_range, cfg.wrist_dead_zone),
            relative_command(1 - state.palm_depth_scale / cal.neutral_depth_scale, cfg.depth_range, cfg.depth_dead_zone),
            clamp(-angle / cfg.roll_range),  # Preview clockwise -> negative rig Z rotation.
            clamp(state.normalized_pinch, 0, 1))
