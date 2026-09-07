"""Integration checks against evaluated Blender transforms and saved animation."""

from pathlib import Path
import hashlib
import json
import math
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent)]

import bpy
from mathutils import Vector, Matrix
from config import LIMITS, TROCARS, SHAFT_LENGTH, PIVOT_TOLERANCE, FRAME_START, FRAME_END
from mechanics import apply_control, CONTROL_NAMES
from lapsim_ai.control.instrument import InstrumentControl
from scene import build_scene
from demo import animate_demo

maximum_pivot_error = 0.0


def evaluated(name):
    return bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get())


def close(a, b, tolerance=PIVOT_TOLERANCE):
    assert (Vector(a) - Vector(b)).length <= tolerance, (tuple(a), tuple(b))


def check_instrument(side):
    global maximum_pivot_error
    root = bpy.data.objects[f"{side}_INSTRUMENT"]
    controls = InstrumentControl(**{name: root[name] for name in CONTROL_NAMES}).limited(LIMITS)
    pivot = Vector(TROCARS[side])
    tip = evaluated(f"{side}_TIP_REFERENCE").matrix_world.translation
    handle = evaluated(f"{side}_HANDLE_REFERENCE_POINT").matrix_world.translation
    root_position = evaluated(root.name).matrix_world.translation
    marker = evaluated(f"{side}_TROCAR").matrix_world.translation
    axis = (tip - handle).normalized()
    # Distance from fixed pivot to the actual evaluated shaft line.
    line_error = (pivot - handle).cross(axis).length
    maximum_pivot_error = max(maximum_pivot_error, line_error, (root_position - pivot).length,
                              (marker - pivot).length)
    assert line_error <= PIVOT_TOLERANCE, line_error
    close(root_position, pivot)
    close(marker, pivot)
    assert LIMITS.insertion[0] - 1e-7 <= (tip - pivot).length <= LIMITS.insertion[1] + 1e-7
    orientation = Matrix.Rotation(math.radians(controls.yaw), 3, "Y") @ Matrix.Rotation(math.radians(controls.pitch), 3, "X")
    expected_axis = orientation @ Vector((0, 0, -1))
    close(tip, pivot + expected_axis * controls.insertion)
    close(handle, pivot - expected_axis * (SHAFT_LENGTH - controls.insertion))
    # The fulcrum relation: opposite vectors, scaled by internal/external lever lengths.
    close((tip - pivot) / controls.insertion,
          -(handle - pivot) / (SHAFT_LENGTH - controls.insertion))
    for channel, index in (("pitch", 0), ("yaw", 1)):
        angle = math.degrees(evaluated(root.name).rotation_euler[index])
        assert abs(angle - getattr(controls, channel)) < 1e-4, (channel, angle)
    roll = math.degrees(evaluated(f"{side}_AXIAL").rotation_euler.z)
    assert LIMITS.rotation[0] - 1e-4 <= roll <= LIMITS.rotation[1] + 1e-4
    assert abs(roll - controls.rotation) < 1e-4
    for name in (root.name, f"{side}_INSERTION", f"{side}_AXIAL"):
        for curve in bpy.data.objects[name].animation_data.drivers:
            assert curve.driver.is_valid, (name, curve.data_path)


def signature():
    """Semantic reproducibility; .blend bytes may contain save-specific metadata."""
    data = {"objects": [], "frames": []}
    for obj in sorted(bpy.data.objects, key=lambda item: item.name):
        row = {"name": obj.name, "type": obj.type,
               "parent": obj.parent.name if obj.parent else None,
               "scale": list(obj.scale)}
        if obj.type == "MESH":
            row["vertices"] = [list(v.co) for v in obj.data.vertices]
            row["faces"] = [list(p.vertices) for p in obj.data.polygons]
            row["materials"] = [m.name for m in obj.data.materials]
        if obj.type == "CAMERA":
            row["camera"] = [obj.data.lens, obj.data.sensor_width, obj.data.clip_start, obj.data.clip_end]
        if obj.type == "LIGHT":
            row["light"] = [obj.data.type, obj.data.energy, obj.data.size]
        data["objects"].append(row)
    for frame in range(FRAME_START, FRAME_END + 1):
        bpy.context.scene.frame_set(frame)
        data["frames"].append([
            [obj.name, [list(row) for row in evaluated(obj.name).matrix_world]]
            for obj in sorted(bpy.data.objects, key=lambda item: item.name)
        ])
    data["materials"] = [[m.name, list(m.diffuse_color)] for m in sorted(bpy.data.materials, key=lambda m: m.name)]
    scene = bpy.context.scene
    data["settings"] = [scene.render.engine, scene.render.resolution_x, scene.render.resolution_y,
                        scene.render.fps, scene.unit_settings.scale_length, scene.cycles.seed]
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def main():
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_instrument_control.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    path = ROOT / "blender/scenes/lapsim_ai_phase1a.blend"
    bpy.ops.wm.open_mainfile(filepath=str(path))
    initial_signature = signature()
    for frame in range(FRAME_START, FRAME_END + 1):
        bpy.context.scene.frame_set(frame)
        for side in TROCARS:
            check_instrument(side)
    # Remove animation only in this disposable process, leaving driver rigs intact.
    for side in TROCARS:
        bpy.data.objects[f"{side}_INSTRUMENT"].animation_data.action = None
    rng = random.Random(731)
    for iteration in range(100):
        for side in TROCARS:
            other = "RIGHT" if side == "LEFT" else "LEFT"
            before = evaluated(f"{other}_AXIAL").matrix_world.copy()
            raw = InstrumentControl(rng.uniform(-100, 100), rng.uniform(-100, 100),
                                    rng.uniform(-.1, .5), rng.uniform(-500, 500))
            apply_control(side, raw)
            check_instrument(side)
            assert evaluated(f"{other}_AXIAL").matrix_world == before, "Cross-instrument coupling"
    # Bypass the API to verify native drivers also clamp raw custom-property input.
    for side in TROCARS:
        for value in (-1000., 1000.):
            root = bpy.data.objects[f"{side}_INSTRUMENT"]
            for name in CONTROL_NAMES:
                root[name] = value
            root.update_tag()
            bpy.context.view_layer.update()
            check_instrument(side)
    build_scene()
    animate_demo()
    regenerated_signature = signature()
    assert initial_signature == regenerated_signature, "Regenerated scene differs semantically"
    report = {
        "status": "PASS", "blender": bpy.app.version_string,
        "unit_tests": result.testsRun, "animation_frames_checked": FRAME_END - FRAME_START + 1,
        "random_control_cases": 200, "raw_driver_boundary_cases": 4,
        "pivot_tolerance_metres": PIVOT_TOLERANCE,
        "maximum_pivot_error_metres": maximum_pivot_error,
        "independence": "PASS (both directions)", "fulcrum_relation": "PASS",
        "limits": "PASS (all four channels)", "saved_scene_regeneration": "PASS",
        "semantic_sha256": initial_signature,
    }
    out = ROOT / "outputs/phase1a"
    out.mkdir(parents=True, exist_ok=True)
    (out / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PHASE1A_VALIDATION " + json.dumps(report))


if __name__ == "__main__":
    main()
