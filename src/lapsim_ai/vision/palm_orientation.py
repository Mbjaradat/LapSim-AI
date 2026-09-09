"""Monocular palm-frame twist proxy; not biomechanical wrist measurement.

No image-angle fallback: missing/degenerate geometry cannot issue a roll target.
The pure relative estimator is separate from its temporal filter for future inputs.
"""
from dataclasses import dataclass
from math import atan2, exp, isfinite, pi, sqrt
from statistics import median


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def unit(v):
    length = sqrt(dot(v, v))
    return tuple(x/length for x in v) if isfinite(length) and length > 1e-6 else None


@dataclass(frozen=True)
class PalmFrame:
    longitudinal: tuple[float, float, float]
    transverse: tuple[float, float, float]


def frame_from_axes(longitudinal, transverse):
    axis = unit(longitudinal)
    if axis is None:
        return None
    projection = dot(axis, transverse)
    lateral = unit(tuple(x-projection*y for x, y in zip(transverse, axis)))
    return PalmFrame(axis, lateral) if lateral is not None else None


def palm_frame(points):
    """Aspect-corrected x/y and wrist-relative Z from wrist + MCPs 5/9/13/17.

    Four-knuckle least-squares lateral direction suppresses any one point's noise.
    Translation and uniform scale cancel. Fingertip articulation is excluded.
    """
    if not all(isfinite(v) for point in points for v in point):
        return None
    wrist, *knuckles = points
    longitudinal = tuple(sum(p[i] for p in knuckles)/4-wrist[i] for i in range(3))
    transverse = tuple(sum(w*p[i] for w, p in zip((-1.5, -.5, .5, 1.5), knuckles))/5 for i in range(3))
    return frame_from_axes(longitudinal, transverse)


def neutral_frame(frames):
    if not frames or any(frame is None for frame in frames):
        return None
    return frame_from_axes(
        tuple(median(f.longitudinal[i] for f in frames) for i in range(3)),
        tuple(median(f.transverse[i] for f in frames) for i in range(3)))


def relative_twist(neutral, current):
    """Remove shortest-arc swing of the palm axis, then measure signed twist.

    The calibrated lateral axis is parallel-transported onto the current palm
    plane. An approximately reversed palm axis is ambiguous and rejected.
    """
    if neutral is None or current is None:
        return None
    a, b = neutral.longitudinal, current.longitudinal
    cosine = max(-1., min(1., dot(a, b)))
    if cosine < -.95:
        return None
    v = cross(a, b)
    first = cross(v, neutral.transverse)
    second = cross(v, first)
    reference = tuple(x+y+z/(1+cosine) for x, y, z in zip(neutral.transverse, first, second))
    return atan2(dot(b, cross(reference, current.transverse)), dot(reference, current.transverse))


def wrap(angle):
    return (angle+pi) % (2*pi)-pi


class TwistFilter:
    def __init__(self):
        self.angle = None

    def update(self, angle, dt, seconds):
        if angle is None:
            return None  # Hold internal history; never extrapolate missing observations.
        alpha = 1 if seconds == 0 else 1-exp(-dt/seconds)
        self.angle = angle if self.angle is None else wrap(self.angle+alpha*wrap(angle-self.angle))
        return self.angle
