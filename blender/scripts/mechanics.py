"""Rigid hierarchy and bounded native drivers; no frame handlers needed."""

import math
import bpy
from lapsim_ai.control.instrument import InstrumentControl
from config import LIMITS, TROCARS, DEFAULTS

CONTROL_NAMES = ("yaw", "pitch", "insertion", "rotation")


def empty(name, parent=None, location=(0, 0, 0)):
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    obj.empty_display_size = .012
    return obj


def bounded_driver(target, path, index, controller, control, multiplier=1):
    curve = target.driver_add(path, index)
    driver = curve.driver
    variable = driver.variables.new()
    variable.name = "v"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id = controller
    variable.targets[0].data_path = f'["{control}"]'
    low, high = getattr(LIMITS, control)
    driver.expression = f"min({high}, max({low}, v)) * {multiplier!r}"


def create_rig(side):
    root = empty(f"{side}_INSTRUMENT", location=TROCARS[side])
    root.rotation_mode = "XYZ"
    root.lock_location = (True, True, True)
    root.lock_rotation = (True, True, True)
    root.lock_scale = (True, True, True)
    for name in CONTROL_NAMES:
        low, high = getattr(LIMITS, name)
        root[name] = float(getattr(DEFAULTS[side], name))
        root.id_properties_ui(name).update(
            min=low, max=high, soft_min=low, soft_max=high,
            description="metres" if name == "insertion" else "degrees",
        )
    bounded_driver(root, "rotation_euler", 0, root, "pitch", math.pi / 180)
    bounded_driver(root, "rotation_euler", 1, root, "yaw", math.pi / 180)
    slider = empty(f"{side}_INSERTION", root)
    bounded_driver(slider, "location", 2, root, "insertion", -1)
    axial = empty(f"{side}_AXIAL", slider)
    bounded_driver(axial, "rotation_euler", 2, root, "rotation", math.pi / 180)
    return root, axial


def apply_control(side, control: InstrumentControl):
    """Clamp finite input before storing it; animation may override on frame change."""
    control = control.limited(LIMITS)
    root = bpy.data.objects[f"{side}_INSTRUMENT"]
    for name in CONTROL_NAMES:
        root[name] = float(getattr(control, name))
    root.update_tag()
    bpy.context.view_layer.update()
    return control
