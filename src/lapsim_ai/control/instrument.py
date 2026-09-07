"""Blender-independent control contract for the Phase 1A rigid instrument."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class InstrumentLimits:
    yaw: tuple[float, float] = (-35.0, 35.0)
    pitch: tuple[float, float] = (-25.0, 25.0)
    insertion: tuple[float, float] = (0.12, 0.28)
    rotation: tuple[float, float] = (-180.0, 180.0)
    jaw: tuple[float, float] = (0.0, 1.0)

    def __post_init__(self):
        for name in ("yaw", "pitch", "insertion", "rotation", "jaw"):
            low, high = getattr(self, name)
            if not (math.isfinite(low) and math.isfinite(high) and low < high):
                raise ValueError(f"Invalid {name} limits")
        if self.insertion[0] <= 0:
            raise ValueError("Insertion must remain positive")
        if self.jaw != (0.0, 1.0):
            raise ValueError("Jaw state uses normalized range [0, 1]")


@dataclass(frozen=True)
class InstrumentControl:
    """Angles in degrees; insertion in metres to the distal shaft reference."""

    yaw: float = 0.0
    pitch: float = 0.0
    insertion: float = 0.20
    rotation: float = 0.0
    jaw: float = 0.5

    def limited(self, limits: InstrumentLimits) -> "InstrumentControl":
        values = {}
        for name in ("yaw", "pitch", "insertion", "rotation", "jaw"):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
            low, high = getattr(limits, name)
            values[name] = min(high, max(low, value))
        return InstrumentControl(**values)
