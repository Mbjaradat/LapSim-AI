"""Independent, camera/Blender-free filtering and per-hand calibration."""

from dataclasses import dataclass, replace
from math import exp, isfinite
from statistics import median
try:
    from .palm_orientation import PalmFrame, TwistFilter, neutral_frame, relative_twist
except ImportError:  # Existing standalone demo entry point.
    from palm_orientation import PalmFrame, TwistFilter, neutral_frame, relative_twist


@dataclass(frozen=True)
class Settings:
    smoothing_seconds: float = 0.06
    dead_zone: float = 0.002
    loss_timeout: float = 0.5
    max_step: float = 0.03  # Maximum normalized change per update, including reacquisition.
    max_pinch_step: float = 0.35  # Faster jaw, still bounded during reacquisition.
    pinch_smoothing_seconds: float = 0.04
    pinch_dead_zone: float = 0.005  # Fraction of calibrated pinch span.
    depth_smoothing_seconds: float = 0.10
    depth_filter_dead_zone: float = 0.005  # Fraction of neutral palm scale.
    depth_max_step: float = 0.03  # Fraction of neutral palm scale per update.
    calibration_samples: int = 30
    minimum_pinch_span: float = 0.005
    roll_smoothing_seconds: float = 0.06

    def __post_init__(self):
        values = (self.smoothing_seconds, self.dead_zone, self.loss_timeout,
                  self.max_step, self.max_pinch_step, self.minimum_pinch_span,
                  self.pinch_smoothing_seconds, self.pinch_dead_zone,
                  self.depth_smoothing_seconds, self.depth_filter_dead_zone, self.depth_max_step,
                  self.roll_smoothing_seconds)
        if not all(isfinite(v) for v in values) or min(values) < 0:
            raise ValueError("Settings must be finite and nonnegative")
        if self.max_step == 0 or self.max_pinch_step == 0 or self.depth_max_step == 0 or self.minimum_pinch_span == 0 or self.calibration_samples < 3:
            raise ValueError("Positive step/span and at least three samples required")


@dataclass(frozen=True)
class Calibration:
    neutral_wrist: tuple[float, float] | None = None
    pinch_open: float | None = None
    pinch_closed: float | None = None
    neutral_palm: tuple[float, float] | None = None
    neutral_depth_scale: float | None = None
    neutral_knuckles: tuple[float, float] | None = None
    neutral_orientation: PalmFrame | None = None
    neutral_palm_center: tuple[float, float] | None = None

    @property
    def ready(self):
        return (self.neutral_wrist is not None and self.pinch_open is not None
                and self.pinch_closed is not None and self.pinch_open > self.pinch_closed)


@dataclass(frozen=True)
class StableHandState:
    handedness: str
    tracked: bool
    available: bool
    valid: bool
    wrist: tuple[float, float] | None
    index_fingertip: tuple[float, float] | None
    thumb_tip: tuple[float, float] | None
    pinch_distance: float | None
    normalized_pinch: float | None
    calibration: Calibration
    status: str
    middle_mcp: tuple[float, float] | None = None
    palm_depth_scale: float | None = None
    knuckle_line: tuple[float, float] | None = None
    roll_angle: float | None = None  # Filtered, neutral-relative palm twist in radians.
    palm_center: tuple[float, float] | None = None


class _Hand:
    def __init__(self):
        self.filtered = self.output = self.last_seen = None
        self.calibration = Calibration()
        self.stage = None
        self.samples = []
        self.orientation_samples = []
        self.roll_filter = TwistFilter()
        self.message = "uncalibrated"


class HandStabilizer:
    """Call update once per frame with all raw states and monotonic seconds.

    Unknown/duplicate identities and nonfinite data are treated as missing.
    Missing data is held, never extrapolated; valid requires current detection
    and complete calibration. Calibration samples restart after any dropped frame.
    """

    def __init__(self, settings=None):
        self.settings = settings or Settings()
        self.hands = {side: _Hand() for side in ("Left", "Right")}
        self._time = None

    def reset(self, side):
        if side not in self.hands:
            raise ValueError("Expected Left or Right")
        self.hands[side] = _Hand()

    def calibrate(self, side, stage):
        if stage not in ("neutral", "open", "closed"):
            raise ValueError("Expected neutral, open or closed")
        hand = self.hands[side]
        hand.stage, hand.samples = stage, []
        hand.orientation_samples = []

    def capture_pair(self, stage, frames):
        """Atomically capture an already validated hold using the existing sampler.

        A private candidate filter prevents partial left/right commits and leaves
        live smoothing history untouched. Only calibration is installed.
        """
        candidate = HandStabilizer(self.settings)
        for side in self.hands:
            candidate.hands[side].calibration = self.hands[side].calibration
            candidate.calibrate(side, stage)
        for i, frame in enumerate(frames[-self.settings.calibration_samples:]):
            candidate.update(frame, (i + 1) / 30)
        for hand in candidate.hands.values():
            cal = hand.calibration
            if hand.stage is not None or "rejected" in hand.message:
                return False
            if (cal.neutral_palm_center is None or cal.neutral_depth_scale is None
                    or cal.neutral_orientation is None):
                return False
            values = (*cal.neutral_palm_center, *cal.neutral_wrist,
                      cal.neutral_depth_scale, *cal.neutral_orientation.longitudinal,
                      *cal.neutral_orientation.transverse)
            values += tuple(v for v in (cal.pinch_open, cal.pinch_closed) if v is not None)
            if not all(isfinite(v) for v in values) or cal.neutral_depth_scale <= 0:
                return False
            if stage == "closed" and (not cal.ready or cal.pinch_open - cal.pinch_closed < max(
                    self.settings.minimum_pinch_span, .35 * cal.neutral_depth_scale)):
                return False
        for side, hand in self.hands.items():
            hand.calibration = candidate.hands[side].calibration
            hand.stage, hand.samples, hand.orientation_samples = None, [], []
            hand.message = "ready" if hand.calibration.ready else "guided setup"
            if stage == "neutral":
                hand.roll_filter = TwistFilter()
        return True

    def _collect(self, hand, values, orientation):
        if hand.stage is None:
            return
        # Median raw samples avoid filter lag bias during calibration.
        hand.samples.append(values)
        hand.orientation_samples.append(orientation)
        if len(hand.samples) < self.settings.calibration_samples:
            return
        sampled = tuple(median(column) for column in zip(*hand.samples))
        field, value = {"neutral": ("neutral_wrist", sampled[:2]),
                        "open": ("pinch_open", sampled[6]),
                        "closed": ("pinch_closed", sampled[6])}[hand.stage]
        candidate = replace(hand.calibration, **{field: value})
        if hand.stage == "neutral":
            candidate = replace(candidate,
                                neutral_palm=(sampled[7] - sampled[0], sampled[8] - sampled[1]) if len(sampled) >= 9 else None,
                                neutral_depth_scale=sampled[9] if len(sampled) >= 12 else None,
                                neutral_knuckles=sampled[10:12] if len(sampled) >= 12 else None,
                                neutral_orientation=neutral_frame(hand.orientation_samples),
                                neutral_palm_center=sampled[12:14] if len(sampled) == 14 else None)
            hand.roll_filter = TwistFilter()
        if (candidate.pinch_open is not None and candidate.pinch_closed is not None
                and candidate.pinch_open - candidate.pinch_closed < self.settings.minimum_pinch_span):
            hand.message = "range rejected: retry O/C"
        else:
            hand.calibration = candidate
            hand.message = "ready" if candidate.ready else "needs N/O/C"
        hand.stage, hand.samples = None, []
        hand.orientation_samples = []

    def update(self, states, now):
        if not isfinite(now) or (self._time is not None and now <= self._time):
            raise ValueError("Time must be finite and strictly increasing")
        dt = 1 / 30 if self._time is None else min(now - self._time, 1 / 15)
        self._time = now
        cfg = self.settings
        alpha = 1 if cfg.smoothing_seconds == 0 else 1 - exp(-dt / cfg.smoothing_seconds)
        pinch_alpha = 1 if cfg.pinch_smoothing_seconds == 0 else 1 - exp(-dt / cfg.pinch_smoothing_seconds)
        depth_alpha = 1 if cfg.depth_smoothing_seconds == 0 else 1 - exp(-dt / cfg.depth_smoothing_seconds)
        result = {}
        states = list(states)
        for side, hand in self.hands.items():
            matches = [s for s in states if s.handedness == side]
            values = None
            if len(matches) == 1:
                raw = matches[0]
                candidate = (*raw.wrist, *raw.index_fingertip, *raw.thumb_tip, raw.pinch_distance)
                if raw.middle_mcp is not None:
                    candidate += tuple(raw.middle_mcp)
                    if raw.palm_depth_scale is not None and raw.knuckle_line is not None:
                        candidate += (raw.palm_depth_scale, *raw.knuckle_line)
                        if raw.palm_center is not None:
                            candidate += tuple(raw.palm_center)
                if (all(isfinite(v) for v in candidate)
                        and all(0 <= v <= 1 for v in candidate[:6] + candidate[7:9])
                        and (len(candidate) < 12 or candidate[9] > 0)
                        and all(-1 <= v <= 1 for v in candidate[10:12])
                        and all(0 <= v <= 1 for v in candidate[12:])
                        and 0 <= candidate[6] <= 2 ** 0.5):
                    values = candidate
            tracked = values is not None
            if tracked:
                hand.last_seen = now
                if hand.filtered is None or len(hand.filtered) != len(values):
                    hand.filtered = hand.output = values
                    hand.samples = []  # Do not mix incomplete/full geometry captures.
                    hand.orientation_samples = []
                else:
                    hand.filtered = tuple(a + (pinch_alpha if i == 6 else depth_alpha if i == 9 else alpha) * (b - a)
                                          for i, (a, b) in enumerate(zip(hand.filtered, values)))
                    # A continuous deadband allows accumulated small intentional motion.
                    output = []
                    for index, (old, target) in enumerate(zip(hand.output, hand.filtered)):
                        delta = target - old
                        movement = max(0, abs(delta) - cfg.dead_zone)
                        limit = cfg.max_step
                        if index == 9:
                            baseline = hand.calibration.neutral_depth_scale or old
                            movement = max(0, abs(delta) - cfg.depth_filter_dead_zone * baseline)
                            limit = cfg.depth_max_step * baseline
                        if index == 6 and hand.calibration.ready:
                            span = hand.calibration.pinch_open - hand.calibration.pinch_closed
                            limit = cfg.max_pinch_step * span
                            movement = max(0, abs(delta) - cfg.pinch_dead_zone * span)
                        output.append(old + min(limit, movement) * (1 if delta >= 0 else -1))
                    hand.output = tuple(output)
                self._collect(hand, values, raw.palm_orientation)
            else:
                hand.samples = []
                hand.orientation_samples = []
            roll = hand.roll_filter.update(
                relative_twist(hand.calibration.neutral_orientation, raw.palm_orientation) if tracked else None,
                dt, cfg.roll_smoothing_seconds)
            available = hand.last_seen is not None and now - hand.last_seen <= cfg.loss_timeout
            cal = hand.calibration
            out = hand.output
            pinch = None
            if cal.ready and out is not None:
                pinch = min(1.0, max(0.0, (out[6] - cal.pinch_closed) / (cal.pinch_open - cal.pinch_closed)))
            status = (f"{hand.stage} {len(hand.samples)}/{cfg.calibration_samples}"
                      if hand.stage else hand.message)
            result[side] = StableHandState(
                side, tracked, available, tracked and cal.ready and hand.stage is None,
                out[:2] if out else None, out[2:4] if out else None,
                out[4:6] if out else None, out[6] if out else None,
                pinch, cal, status, out[7:9] if out and len(out) >= 9 else None,
                out[9] if out and len(out) >= 12 else None,
                out[10:12] if out and len(out) >= 12 else None, roll,
                out[12:14] if out and len(out) == 14 else None)
        return result
