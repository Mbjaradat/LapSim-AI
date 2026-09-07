"""Device-independent live rates. Angles: degrees; lengths: metres; time: seconds."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Sensitivity:
    angular: float = 22.0
    insertion: float = 0.035
    rotation: float = 90.0
    jaw: float = 1.5
    max_dt: float = 0.05
    profiles: tuple[tuple[str, float], ...] = (("Fine", 0.35), ("Normal", 1.0), ("Fast", 2.0))

    def __post_init__(self):
        for value in (self.angular, self.insertion, self.rotation, self.jaw, self.max_dt):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Rates and timestep cap must be finite and positive")
        if not self.profiles or any(not name or not math.isfinite(value) or value <= 0
                                    for name, value in self.profiles):
            raise ValueError("Invalid sensitivity profiles")


SENSITIVITY = Sensitivity()
TIMER_INTERVAL = 1 / 60
WHEEL_DT = 0.05
KEY_TAP_DT = 1 / 60
