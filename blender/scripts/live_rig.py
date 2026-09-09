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
        self.interaction = None
        self.collision = None
        if bpy.context.scene.get('peg_transfer_config'):
            from peg_interaction import PegInteraction
            self.interaction = PegInteraction()
            from lapsim_ai.simulator.collision import CollisionConstraint, CollisionSettings
            from config import TROCARS, SHAFT_RADIUS
            from peg_config import BOARD_TOP, RING_THICKNESS
            self.collision = CollisionConstraint(TROCARS,LIMITS,CollisionSettings(
                board_height=BOARD_TOP,shaft_radius=SHAFT_RADIUS,jaw_length=JAW_LENGTH,
                jaw_half_angle=LIVE_JAW_HALF_ANGLE_DEGREES,ring_thickness=RING_THICKNESS))
        elif bpy.context.scene.get('phase3_interactions', False):
            from phase3_interaction import Phase3Interaction
            self.interaction = Phase3Interaction()

    def update(self, commands, dt):
        previous = self.controller.poses
        self._apply_proposal(previous,self.controller.update(commands, dt))
        if self.interaction and not self.controller.paused:
            self._update_interaction(dt)

    def _apply_proposal(self, previous, proposed):
        if self.collision and not self.controller.paused:
            world = self.interaction.world
            held = {side:world.offsets[name] for name,side in world.owners.items() if side}
            proposed = self.controller.accept_constrained_poses(self.collision.resolve(previous,proposed,held))
        self.rig.apply(proposed)

    def _update_interaction(self, dt):
        if bpy.context.scene.get('peg_transfer_config'):
            self.interaction.update(self.controller.poses, dt)
        else:
            self.interaction.update(self.controller.poses)

    def reset(self):
        self.controller.reset()
        if self.collision:
            self.collision.reset()
        self.rig.apply(self.controller.poses)
        if self.interaction:
            self.interaction.reset()

    def update_targets(self, targets, dt):
        previous = self.controller.poses
        self._apply_proposal(previous,self.controller.update_targets(targets, dt))
        if self.interaction and not self.controller.paused:
            self._update_interaction(dt)
