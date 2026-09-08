"""Loopback-only latest-frame transport and nonblocking worker lifecycle.

No bpy, camera or third-party imports. Packet timestamps use perf_counter (QPC
on Windows in both Python 3.12 and 3.13), not version-dependent monotonic clocks.
Calibration metadata persists independently of command freshness.
"""
import json
import math
from pathlib import Path
import secrets
import socket
import subprocess
import time

from .hand_mapping import InstrumentTarget

STALE_SECONDS = 0.5


def decode_state(data, token):
    """Read explicit session calibration even when a command is stale/invalid."""
    try:
        frame = json.loads(data)
        stamp = frame["time"]
        if frame["token"] != token or type(stamp) not in (int, float) or not math.isfinite(stamp):
            return None
        states = frame["state"]
        for side in ("LEFT", "RIGHT"):
            if any(type(states[side][field]) is not bool for field in ("calibrated", "tracked")):
                return None
        return stamp, {side: states[side]["calibrated"] for side in ("LEFT", "RIGHT")}
    except (ValueError, KeyError, TypeError):
        return None


def decode_frame(data, token, now):
    try:
        frame = json.loads(data)
        if decode_state(data, token) is None:
            return None
        stamp = frame["time"]
        if (frame["token"] != token or not isinstance(stamp, (int, float))
                or not math.isfinite(stamp) or not 0 <= now - stamp <= STALE_SECONDS):
            return None
        targets = []
        for side in ("LEFT", "RIGHT"):
            item = frame["hands"][side]
            if type(item["valid"]) is not bool:
                return None
            if not item["valid"] or not frame["state"][side]["calibrated"] or not frame["state"][side]["tracked"]:
                targets.append(InstrumentTarget(side))
                continue
            values = {name: item[name] for name in ("yaw", "pitch", "insertion", "rotation", "jaw")}
            if any(type(v) not in (float, int) or not math.isfinite(v)
                   or not (-1 <= v <= 1) for v in values.values()) or values["jaw"] < 0:
                return None
            targets.append(InstrumentTarget(side, True, **values))
        statuses = {side: str(frame.get("status", {}).get(side, ""))[:80] for side in ("LEFT", "RIGHT")}
        return stamp, targets, statuses
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


class WebcamProcess:
    def __init__(self, root):
        root = Path(root)
        executable = root / ".venv/Scripts/python.exe"
        if not executable.is_file():
            raise ValueError(f"Missing standalone Python: {executable}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("127.0.0.1", 0))
        self.socket.setblocking(False)
        self.token = secrets.token_hex(16)
        self.frame = None
        self.calibrated = {side: False for side in ("LEFT", "RIGHT")}
        self.state_time = float("-inf")
        self.closed = False
        self.status = "Starting webcam; calibrate in preview"
        self.deadline = None
        try:
            self.process = subprocess.Popen(
                [str(executable), "-B", str(root / "src/lapsim_ai/vision/webcam_demo.py"),
                 "--bridge-port", str(self.socket.getsockname()[1]), "--bridge-token", self.token],
                cwd=str(root), stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception:
            self.socket.close()
            raise

    def poll(self, now=None):
        now = time.perf_counter() if now is None else now
        if self.closed:
            return []
        if self.process.poll() is not None:
            self.status = f"Webcam exited ({self.process.returncode}); stop and restart"
            self.frame = None
            return []
        for _ in range(32):
            try:
                data, address = self.socket.recvfrom(8192)
            except BlockingIOError:
                break
            if address[0] != "127.0.0.1":
                continue
            state = decode_state(data, self.token)
            if state and self.state_time < state[0] <= now:
                self.state_time, self.calibrated = state
            frame = decode_frame(data, self.token, now)
            if frame and (self.frame is None or frame[0] > self.frame[0]):
                self.frame = frame
        if self.frame is None or now - self.frame[0] > STALE_SECONDS:
            self.status = "Waiting/stale: holding poses"
            return []
        self.status = " | ".join(f"{side}: {status}" for side, status in self.frame[2].items())
        return self.frame[1]

    def stop(self):
        """Request graceful exit (stdin EOF); no wait on Blender's main thread."""
        if self.closed:
            return
        self.closed = True
        self.frame = None
        self.socket.close()
        self.process.stdin.close()
        self.deadline = time.monotonic() + 1.5

    def reap(self):
        """Poll from a Blender timer until exit; terminate a stuck camera read."""
        if self.process.poll() is not None:
            return None
        if self.closed and time.monotonic() >= self.deadline:
            self.process.kill()
        return 0.1

    def shutdown(self):
        """Process-exit fallback when Blender timers are no longer running."""
        self.stop()
        if self.process.poll() is None:
            self.process.kill()
