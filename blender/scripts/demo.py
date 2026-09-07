"""Deterministic looping control animation, stored natively in the blend file."""

import math
import bpy
from config import DEMO_POSES
from mechanics import apply_control, CONTROL_NAMES
from lapsim_ai.control.instrument import InstrumentControl


def animate_demo():
    for first, last in zip(DEMO_POSES, DEMO_POSES[1:]):
        for frame in range(first[0], last[0] + 1):
            t = (frame - first[0]) / (last[0] - first[0])
            weight = (1 - math.cos(math.pi * t)) / 2
            for i, side in enumerate(("LEFT", "RIGHT"), 1):
                values = [a + (b - a) * weight for a, b in zip(first[i], last[i])]
                apply_control(side, InstrumentControl(*values))
                root = bpy.data.objects[f"{side}_INSTRUMENT"]
                for name in CONTROL_NAMES:
                    root.keyframe_insert(data_path=f'["{name}"]', frame=frame, group="Instrument controls")
    # Linear interpolation between dense samples avoids curve overshoot.
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation = "LINEAR"
    for pose in DEMO_POSES:
        bpy.context.scene.timeline_markers.new(f"Pose {pose[0]}", frame=pose[0])
    bpy.context.scene.frame_set(1)
