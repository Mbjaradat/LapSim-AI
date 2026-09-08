"""Independent, camera/Blender-free filtering and per-hand calibration."""

from dataclasses import dataclass, replace
from math import exp, isfinite
from statistics import median


@dataclass(frozen=True)
class Settings:
    smoothing_seconds: float = 0.06
    dead_zone: float = 0.002
    loss_timeout: float = 0.5
    max_step: float = 0.03  # Maximum normalized change per update, including reacquisition.
    max_pinch_step: float = 0.1  # Maximum calibrated pinch change per update.
    calibration_samples: int = 30
    minimum_pinch_span: float = 0.005

    def __post_init__(self):
        values = (self.smoothing_seconds, self.dead_zone, self.loss_timeout,
                  self.max_step, self.max_pinch_step, self.minimum_pinch_span)
        if not all(isfinite(v) for v in values) or min(values) < 0:
            raise ValueError("Settings must be finite and nonnegative")
        if self.max_step == 0 or self.max_pinch_step == 0 or self.minimum_pinch_span == 0 or self.calibration_samples < 3:
            raise ValueError("Positive step/span and at least three samples required")


@dataclass(frozen=True)
class Calibration:
    neutral_wrist: tuple[float, float] | None = None
    pinch_open: float | None = None
    pinch_closed: float | None = None

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


class _Hand:
    def __init__(self):
        self.filtered = self.output = self.last_seen = None
        self.calibration = Calibration()
        self.stage = None
        self.samples = []
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

    def _collect(self, hand, values):
        if hand.stage is None:
            return
        # Median raw samples avoid filter lag bias during calibration.
        hand.samples.append(values)
        if len(hand.samples) < self.settings.calibration_samples:
            return
        sampled = tuple(median(column) for column in zip(*hand.samples))
        field, value = {"neutral": ("neutral_wrist", sampled[:2]),
                        "open": ("pinch_open", sampled[6]),
                        "closed": ("pinch_closed", sampled[6])}[hand.stage]
        candidate = replace(hand.calibration, **{field: value})
        if (candidate.pinch_open is not None and candidate.pinch_closed is not None
                and candidate.pinch_open - candidate.pinch_closed < self.settings.minimum_pinch_span):
            hand.message = "range rejected: retry O/C"
        else:
            hand.calibration = candidate
            hand.message = "ready" if candidate.ready else "needs N/O/C"
        hand.stage, hand.samples = None, []

    def update(self, states, now):
        if not isfinite(now) or (self._time is not None and now <= self._time):
            raise ValueError("Time must be finite and strictly increasing")
        dt = 1 / 30 if self._time is None else min(now - self._time, 1 / 15)
        self._time = now
        cfg = self.settings
        alpha = 1 if cfg.smoothing_seconds == 0 else 1 - exp(-dt / cfg.smoothing_seconds)
        result = {}
        states = list(states)
        for side, hand in self.hands.items():
            matches = [s for s in states if s.handedness == side]
            values = None
            if len(matches) == 1:
                raw = matches[0]
                candidate = (*raw.wrist, *raw.index_fingertip, *raw.thumb_tip, raw.pinch_distance)
                if (all(isfinite(v) for v in candidate)
                        and all(0 <= v <= 1 for v in candidate[:6])
                        and 0 <= candidate[6] <= 2 ** 0.5):
                    values = candidate
            tracked = values is not None
            if tracked:
                hand.last_seen = now
                if hand.filtered is None:
                    hand.filtered = hand.output = values
                else:
                    hand.filtered = tuple(a + alpha * (b - a) for a, b in zip(hand.filtered, values))
                    # A continuous deadband allows accumulated small intentional motion.
                    output = []
                    for index, (old, target) in enumerate(zip(hand.output, hand.filtered)):
                        delta = target - old
                        movement = max(0, abs(delta) - cfg.dead_zone)
                        limit = cfg.max_step
                        if index == 6 and hand.calibration.ready:
                            span = hand.calibration.pinch_open - hand.calibration.pinch_closed
                            limit = min(limit, cfg.max_pinch_step * span)
                        output.append(old + min(limit, movement) * (1 if delta >= 0 else -1))
                    hand.output = tuple(output)
                self._collect(hand, values)
            else:
                hand.samples = []
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
                pinch, cal, status)
        return result
