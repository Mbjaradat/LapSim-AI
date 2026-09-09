"""Input-independent state controller; no Blender or keyboard imports."""

from dataclasses import dataclass
import math
from .instrument import InstrumentControl, InstrumentLimits
from .settings import SENSITIVITY, WEBCAM_JAW_RATE

CHANNELS = ("yaw", "pitch", "insertion", "rotation", "jaw")
SIDES = ("LEFT", "RIGHT")


@dataclass(frozen=True)
class NormalizedCommand:
    """Signed rates in [-1, 1]; zero means hold. Side identities are explicit."""

    side: str
    yaw: float = 0.0
    pitch: float = 0.0
    insertion: float = 0.0
    rotation: float = 0.0
    jaw: float = 0.0

    def bounded(self):
        if self.side not in SIDES:
            raise ValueError("Unknown instrument side")
        values = {}
        for name in CHANNELS:
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(f"Nonfinite {name} command")
            values[name] = min(1.0, max(-1.0, value))
        return NormalizedCommand(self.side, **values)


class InstrumentController:
    def __init__(self, neutral, limits=None, sensitivity=SENSITIVITY):
        self.limits = limits or InstrumentLimits()
        if set(neutral) != set(SIDES):
            raise ValueError("Neutral pose must define both instruments")
        self.neutral = {side: pose.limited(self.limits) for side, pose in neutral.items()}
        self.sensitivity = sensitivity
        self.profile_index = next((i for i, (name, _) in enumerate(sensitivity.profiles)
                                   if name == "Normal"), 0)
        self.paused = False
        self.reset()

    @property
    def poses(self):
        return dict(self._poses)

    @property
    def profile(self):
        return self.sensitivity.profiles[self.profile_index]

    def cycle_sensitivity(self):
        self.profile_index = (self.profile_index + 1) % len(self.sensitivity.profiles)

    def reset(self):
        """Reset all five channels; retain pause and sensitivity preferences."""
        self._poses = dict(self.neutral)

    def accept_constrained_poses(self, poses):
        """Commit accepted output poses; subsequent updates start at contact, not inside geometry."""
        if set(poses) != set(SIDES):
            raise ValueError('Both constrained instrument poses are required')
        self._poses = {side:pose.limited(self.limits) for side,pose in poses.items()}
        return self.poses

    def update(self, commands, dt):
        if not math.isfinite(dt) or dt < 0:
            raise ValueError("dt must be finite and nonnegative")
        commands = [command.bounded() for command in commands]
        if len({command.side for command in commands}) != len(commands):
            raise ValueError("At most one command per instrument per tick")
        if self.paused:
            return self.poses
        dt = min(dt, self.sensitivity.max_dt)
        scale = self.profile[1]
        rates = {"yaw": self.sensitivity.angular, "pitch": self.sensitivity.angular,
                 "insertion": self.sensitivity.insertion, "rotation": self.sensitivity.rotation,
                 "jaw": self.sensitivity.jaw}
        for command in commands:
            old = self._poses[command.side]
            new = {name: getattr(old, name) + getattr(command, name) * rates[name] * scale * dt
                   for name in CHANNELS}
            self._poses[command.side] = InstrumentControl(**new).limited(self.limits)
        return self.poses

    def update_targets(self, targets, dt):
        """Absolute webcam targets, approached at existing safe channel rates.

        Invalid/missing sides hold. This shares the keyboard controller state and
        limits, but does not interpret absolute targets as keyboard velocities.
        """
        if not math.isfinite(dt) or dt < 0:
            raise ValueError("dt must be finite and nonnegative")
        targets = list(targets)
        if len({t.side for t in targets}) != len(targets):
            raise ValueError("Duplicate target side")
        desired = {}
        for target in targets:
            if target.side not in SIDES:
                raise ValueError("Unknown instrument side")
            pose = target.to_control(self.neutral[target.side], self.limits)
            if pose is not None:
                desired[target.side] = pose
        if self.paused:
            return self.poses
        dt = min(dt, self.sensitivity.max_dt)
        rates = dict(yaw=self.sensitivity.angular, pitch=self.sensitivity.angular,
                     insertion=self.sensitivity.insertion, rotation=self.sensitivity.rotation,
                     jaw=WEBCAM_JAW_RATE)
        for side, pose in desired.items():
            old = self._poses[side]
            values = {}
            for name in CHANNELS:
                delta = getattr(pose, name) - getattr(old, name)
                step = rates[name] * dt
                values[name] = getattr(old, name) + min(step, max(-step, delta))
            self._poses[side] = InstrumentControl(**values).limited(self.limits)
        return self.poses
