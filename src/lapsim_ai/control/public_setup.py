"""Camera/Blender-free guided calibration. No task or telemetry ownership.

Coordinates and HOME directions use the already mirrored detector image.
Apparent scale is a framing heuristic, never a metric distance estimate.
"""
from dataclasses import dataclass
from math import ceil, dist, isfinite

SIDES = ("Left", "Right")
HOME_RADIUS = .065
CAMERA_GUIDANCE = (
    "Face the camera toward you and your working hand area.",
    "Start around 0.8-1.2 m away; adjust to fit your camera.",
    "Show both full hands with room to move.",
    "Use even front/side light; avoid backlight and harsh shadows.",
    "Keep hands distinct from the background.",
)


def home_direction(position, home):
    if position is None or home is None:
        return "RETURN TO CAMERA"
    if dist(position, home) <= HOME_RADIUS:
        return "HOME"
    dx, dy = home[0] - position[0], home[1] - position[1]
    return ("RIGHT" if dx > 0 else "LEFT") if abs(dx) >= abs(dy) else ("DOWN" if dy > 0 else "UP")


@dataclass(frozen=True)
class SetupStatus:
    state: str
    message: str
    remaining: int | None
    ready: bool
    near_home: bool


class GuidedSetup:
    def __init__(self):
        self.stage = "neutral"
        self.state = "CAMERA_SETUP"
        self.message = "CAMERA SETUP"
        self.home = {}
        self.anchor = None
        self.since = self.last = self.completed_at = None
        self.samples = []
        self.remaining = None
        self.near_home = False

    @property
    def ready(self):
        return self.stage is None

    def status(self):
        return SetupStatus(self.state, self.message, self.remaining, self.ready, self.near_home)

    def recenter(self, *, paused, manipulating):
        """Explicit UI hook only. Caller must pause and check object ownership.

        No HOME crossing/hold calls this method. Existing calibration survives
        until a new pair of neutral references is successfully captured.
        """
        if not paused or manipulating:
            return False
        self.stage, self.state = "neutral", "HOME_SETUP"
        self._restart("PLACE BOTH HANDS COMFORTABLY")
        return True

    def _restart(self, message):
        self.anchor = self.since = self.remaining = None
        self.samples = []
        self.message = message

    def update(self, states, bounds, now, stabilizer):
        if not isfinite(now) or (self.last is not None and now <= self.last):
            raise ValueError("Time must increase")
        if self.last is not None and now - self.last > .5:
            self._restart("HOLD STILL")
        first = self.last is None
        self.last = now
        hands = {s: [h for h in states if h.handedness == s] for s in SIDES}
        self.near_home = False
        reason = None
        for side in SIDES:
            if len(hands[side]) != 1:
                reason = f"{side.upper()} HAND LOST - SHOW BOTH HANDS"
                break
            h = hands[side][0]
            box = bounds.get(side)
            values = (*h.palm_center, h.palm_depth_scale, h.pinch_distance) if h.palm_center else ()
            if (len(values) != 4 or any(v is None or not isfinite(v) for v in values)
                    or h.palm_orientation is None or box is None
                    or len(box) != 4 or not all(isfinite(v) for v in box)):
                reason = "RETRY - SHOW PALMS TO CAMERA"
                break
            if not all(isfinite(v) for v in (*h.palm_orientation.longitudinal, *h.palm_orientation.transverse)):
                reason = "RETRY - SHOW PALMS TO CAMERA"
                break
            if h.palm_depth_scale < .045:
                reason = "MOVE CLOSER"
            elif h.palm_depth_scale > .30:
                reason = "MOVE BACK SLIGHTLY"
            elif min(box[:2]) < .06 or max(box[2:]) > .94:
                reason = "KEEP HANDS INSIDE FRAME"
            if reason:
                break
        pair = {s: hands[s][0] for s in SIDES} if all(len(hands[s]) == 1 for s in SIDES) else {}
        if pair and self.home:
            self.near_home = all(home_direction(pair[s].palm_center, self.home.get(s)) == "HOME" for s in SIDES)
        if self.ready:
            # Read-only after completion: never recalibrate due to drift or loss.
            self.state = "CALIBRATION_COMPLETE" if now - self.completed_at < 1.5 else "WAITING_FOR_LIVE"
            self.message = reason or ("CALIBRATION COMPLETE" if self.state == "CALIBRATION_COMPLETE" else "GET READY - RETURN TO HOME")
            self.near_home = self.near_home and reason is None
            return self.status()
        prefix = {"neutral": "HOME", "open": "OPEN", "closed": "PINCH"}[self.stage]
        self.state = prefix + "_SETUP"
        if first:
            self.state = "CAMERA_SETUP"
            return self.status()
        if reason:
            if not pair:
                self.state = "WAITING_FOR_HANDS"
            self._restart(reason)
            return self.status()
        if self.stage != "neutral" and not self.near_home:
            self._restart("MOVE TO HOME")
            return self.status()
        for side, h in pair.items():
            ratio = h.pinch_distance / h.palm_depth_scale
            if self.stage == "open" and ratio < .65:
                reason = "OPEN MORE - OPEN BOTH THUMB + INDEX"
            if self.stage == "closed":
                opening = stabilizer.hands[side].calibration.pinch_open
                if ratio > .22:
                    reason = "PINCH MORE - PINCH THUMB + INDEX"
                elif opening is None or opening - h.pinch_distance < max(.005, .35 * h.palm_depth_scale):
                    reason = "RETRY - OPEN AND PINCH TOO SIMILAR"
        if reason:
            self._restart(reason)
            return self.status()
        if self.anchor is not None:
            for s, h in pair.items():
                a = self.anchor[s]
                if (dist(h.palm_center, a.palm_center) > .015
                        or abs(h.palm_depth_scale / a.palm_depth_scale - 1) > .08
                        or abs(h.pinch_distance - a.pinch_distance) / a.palm_depth_scale > .12
                        or dist(h.palm_orientation.longitudinal, a.palm_orientation.longitudinal) > .15
                        or dist(h.palm_orientation.transverse, a.palm_orientation.transverse) > .15):
                    self._restart("HOLD STILL")
                    return self.status()
        if self.anchor is None:
            self.anchor, self.since = pair, now
        self.samples.append(list(pair.values()))
        self.samples = self.samples[-120:]
        elapsed = now - self.since
        self.message = {"neutral": "PLACE BOTH HANDS COMFORTABLY - HOLD STILL", "open": "OPEN THUMB + INDEX - HOLD STILL", "closed": "PINCH THUMB + INDEX - HOLD STILL"}[self.stage]
        if elapsed >= .75:
            self.state = prefix + "_COUNTDOWN"
            self.remaining = max(1, ceil(3.75 - elapsed))
        if elapsed >= 3.75 and len(self.samples) >= stabilizer.settings.calibration_samples:
            if not stabilizer.capture_pair(self.stage, self.samples):
                self._restart("RETRY - SHOW PALMS AND USE A CLEAR OPEN/PINCH RANGE")
                return self.status()
            if self.stage == "neutral":
                self.home = {s: stabilizer.hands[s].calibration.neutral_palm_center for s in SIDES}
            self.stage = {"neutral": "open", "open": "closed", "closed": None}[self.stage]
            self._restart("CALIBRATION COMPLETE" if self.ready else "OPEN HANDS" if self.stage == "open" else "PINCH THUMB + INDEX")
            self.state = "CALIBRATION_COMPLETE" if self.ready else "OPEN_SETUP" if self.stage == "open" else "PINCH_SETUP"
            if self.ready:
                self.completed_at = now
        return self.status()
