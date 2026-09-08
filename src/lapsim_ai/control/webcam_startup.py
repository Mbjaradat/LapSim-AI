"""One-shot webcam startup gate; no Blender, camera or background timers."""
from math import ceil
from .webcam_bridge import STALE_SECONDS

COUNTDOWN_SECONDS = 5.0


class WebcamStartup:
    def __init__(self):
        self.started = False
        self.closed = False
        self.deadline = None
        self.last_update = None
        self.waiting = "WAITING FOR CALIBRATION"
        self.remaining = 5

    def update(self, targets, timestamp, calibration, now):
        """Return True exactly once, when initial LIVE may begin.

        Targets come from the existing validated transport. A missed freshness
        window (including a stalled Blender timer) restarts the full countdown.
        Calibration is explicit persistent metadata, independent of visibility.
        """
        if self.started or self.closed:
            return False
        if self.last_update is not None and now - self.last_update > STALE_SECONDS:
            self.deadline = None
        self.last_update = now
        fresh = timestamp is not None and 0 <= now - timestamp <= STALE_SECONDS
        calibrated = all(calibration.get(side) is True for side in ("LEFT", "RIGHT"))
        ready = (calibrated and fresh and len(targets) == 2 and {t.side for t in targets} == {"LEFT", "RIGHT"}
                 and all(t.valid for t in targets))
        if not ready:
            self.deadline = None
            self.remaining = 5
            self.waiting = "WAITING FOR BOTH HANDS" if calibrated else "WAITING FOR CALIBRATION"
            return False
        if self.deadline is None:
            self.deadline = now + COUNTDOWN_SECONDS
        self.remaining = max(1, ceil(self.deadline - now))
        if now >= self.deadline:
            self.started = True
            self.deadline = None
            return True
        return False

    def label(self, paused):
        if self.started or self.closed:
            return "PAUSED" if paused or self.closed else "LIVE"
        if self.deadline is not None:
            return f"BOTH HANDS READY — STARTING IN {self.remaining}..."
        return self.waiting

    def cancel_countdown(self):
        self.deadline = None
        self.remaining = 5
        self.waiting = "WAITING FOR BOTH HANDS"

    def stop(self):
        self.closed = True
        self.cancel_countdown()
