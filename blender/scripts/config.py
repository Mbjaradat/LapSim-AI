"""Central parameters for original, primitive-only Phase 1A geometry."""

from lapsim_ai.control.instrument import InstrumentControl, InstrumentLimits

LIMITS = InstrumentLimits()
TROCARS = {"LEFT": (-0.085, 0.0, 0.12), "RIGHT": (0.085, 0.0, 0.12)}
SHAFT_LENGTH = 0.42
SHAFT_RADIUS = 0.003
JAW_LENGTH = 0.018
PIVOT_TOLERANCE = 1e-6  # metres
CAMERA_POSITION = (0.0, -0.42, 0.29)
CAMERA_TARGET = (0.0, 0.035, -0.045)
CAMERA_LENS_MM = 24.0
CAMERA_SENSOR_MM = 36.0
RESOLUTION = (960, 720)
LIGHTS = (
    ("Scope light", (0, -.20, .24), 4.0, .20),
    ("Soft fill", (.18, .12, .18), 2.0, .18),
)
FPS = 30
FRAME_START = 1
FRAME_END = 241
DEFAULTS = {
    "LEFT": InstrumentControl(yaw=-18, pitch=12),
    "RIGHT": InstrumentControl(yaw=18, pitch=12),
}
# frame, left (yaw, pitch, insertion, axial rotation), right controls
DEMO_POSES = (
    (1, (-18, 12, .20, 0), (18, 12, .20, 0)),
    (41, (-32, -15, .25, 90), (8, 20, .16, -70)),
    (81, (-5, 22, .14, -130), (32, -18, .26, 140)),
    (121, (20, 0, .23, 180), (-20, 0, .23, -180)),
    (161, (-25, -22, .28, 30), (25, 22, .12, 100)),
    (201, (0, 20, .17, -90), (5, -20, .25, 45)),
    (241, (-18, 12, .20, 0), (18, 12, .20, 0)),
)
