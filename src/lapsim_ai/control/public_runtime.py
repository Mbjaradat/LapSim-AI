"""Public runtime presentation over the existing one-shot LIVE gate."""
from .webcam_startup import WebcamStartup
from .webcam_bridge import STALE_SECONDS


class PublicRuntime:
    def __init__(self):
        self.startup = WebcamStartup()
        self.state, self.message = "CAMERA_SETUP", "CAMERA SETUP"

    def retry(self):
        """Caller resets task/results separately; calibration remains in worker."""
        self.__init__()

    def update(self, targets, timestamp, calibration, setup, now, *, paused, complete=False):
        fresh = timestamp is not None and 0 <= now - timestamp <= STALE_SECONDS
        if complete:
            self.state, self.message = "COMPLETE", "PEG TRANSFER COMPLETE - R TO RETRY"
            return False
        if not self.startup.started:
            eligible = fresh and setup.get("ready") is True and setup.get("near_home") is True
            eligible = eligible and setup.get("state") != "CALIBRATION_COMPLETE"
            entered = self.startup.update(targets if eligible else [], timestamp, calibration, now)
            self.state = "LIVE" if entered else "LIVE_COUNTDOWN" if self.startup.deadline else setup.get("state", "CAMERA_SETUP")
            self.message = ("LIVE" if entered else f"GET READY - {self.startup.remaining}"
                            if self.startup.deadline else setup.get("message", "SHOW BOTH HANDS"))
            if not fresh:
                self.message = "SHOW BOTH HANDS - WAITING FOR CAMERA"
            return entered
        missing = [s for s in ("LEFT", "RIGHT") if not fresh or not any(t.side == s and t.valid for t in targets)]
        if paused:
            self.state, self.message = "PAUSED", "PAUSED - SPACE TO RESUME"
        elif missing:
            self.state = "TRACKING_LOST"
            self.message = " + ".join(missing) + " HAND LOST - RETURN TO CAMERA / HOME"
        else:
            self.state, self.message = "LIVE", "LIVE"
        return False
