"""Blender adapter for live poses; preserves Phase 1A scene generation."""

import math
import bpy
from config import DEFAULTS, LIMITS, JAW_LENGTH, LIVE_JAW_HALF_ANGLE_DEGREES
from mechanics import empty, bounded_driver
from lapsim_ai.control.controller import CHANNELS, SIDES, InstrumentController

JAW_HALF_ANGLE_DEGREES = LIVE_JAW_HALF_ANGLE_DEGREES


def add_live_jaws():
    for side in SIDES:
        root = bpy.data.objects[f"{side}_INSTRUMENT"]
        axial = bpy.data.objects[f"{side}_AXIAL"]
        root["jaw"] = DEFAULTS[side].jaw
        root.id_properties_ui("jaw").update(min=0.0, max=1.0,
                                             description="0 closed; 1 fully open")
        for sign in (-1, 1):
            jaw = bpy.data.objects[f"{side}_JAW_{sign}"]
            hinge = empty(f"{side}_JAW_HINGE_{sign}", axial, (sign * .0015, 0, 0))
            jaw.parent = hinge
            jaw.location = (0, 0, -JAW_LENGTH / 2)
            jaw.rotation_euler = (0, 0, 0)
            bounded_driver(hinge, "rotation_euler", 1, root, "jaw",
                           -sign * math.radians(JAW_HALF_ANGLE_DEGREES))


class BlenderRig:
    def __init__(self):
        for side in SIDES:
            for suffix in ("INSTRUMENT", "AXIAL", "JAW_HINGE_-1", "JAW_HINGE_1"):
                if f"{side}_{suffix}" not in bpy.data.objects:
                    raise ValueError("Open the Phase 1B scene before starting live controls")
        self.detach_animation()

    def detach_animation(self):
        # Live mode owns control properties. Detach actions and mute NLA, retain drivers.
        for side in SIDES:
            root = bpy.data.objects[f"{side}_INSTRUMENT"]
            for obj in (root, *root.children_recursive):
                if obj.animation_data:
                    obj.animation_data.action = None
                    for track in obj.animation_data.nla_tracks:
                        track.mute = True

    def apply(self, poses):
        for side, pose in poses.items():
            pose = pose.limited(LIMITS)
            root = bpy.data.objects[f"{side}_INSTRUMENT"]
            for name in CHANNELS:
                root[name] = float(getattr(pose, name))
            root.update_tag()
        bpy.context.view_layer.update()


class LiveSession:
    """Controller + output adapter; any future input provider can call update()."""

    def __init__(self):
        self.rig = BlenderRig()
        self.controller = InstrumentController(DEFAULTS, LIMITS)
        self.rig.apply(self.controller.poses)

    def update(self, commands, dt):
        self.rig.apply(self.controller.update(commands, dt))

    def reset(self):
        self.controller.reset()
        self.rig.apply(self.controller.poses)

    def update_targets(self, targets, dt):
        self.rig.apply(self.controller.update_targets(targets, dt))
