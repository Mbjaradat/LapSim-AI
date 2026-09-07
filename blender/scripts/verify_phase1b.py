"""Saved-scene live controller integration checks; no UI or camera hardware needed."""

from pathlib import Path
import json
import math
import random
import sys
import unittest
from types import SimpleNamespace
from functools import partial

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent)]

import bpy
from mathutils import Vector
from config import DEFAULTS, JAW_LENGTH
from live_rig import LiveSession, JAW_HALF_ANGLE_DEGREES
from lapsim_ai.control.controller import CHANNELS, NormalizedCommand
from lapsim_ai.control.keyboard import KeyboardInput
from lapsim_ai.control.keyboard import KEY_BINDINGS
from build_phase1b import build_live_scene
from demo import animate_demo
import verify_phase1a as baseline
import live_ui


def check_jaws(side):
    root = bpy.data.objects[f"{side}_INSTRUMENT"]
    state = min(1, max(0, root["jaw"]))
    tips = []
    for sign in (-1, 1):
        name = f"{side}_JAW_HINGE_{sign}"
        hinge = baseline.evaluated(name)
        angle = math.degrees(hinge.rotation_euler.y)
        assert abs(angle + sign * state * JAW_HALF_ANGLE_DEGREES) < 1e-4
        assert abs(angle) <= JAW_HALF_ANGLE_DEGREES + 1e-4
        assert bpy.data.objects[name].animation_data.drivers[0].driver.is_valid
        tips.append(hinge.matrix_world @ Vector((0, 0, -JAW_LENGTH)))
    gap = (tips[1] - tips[0]).length
    expected = .003 + 2 * JAW_LENGTH * math.sin(math.radians(state * JAW_HALF_ANGLE_DEGREES))
    assert abs(gap - expected) < 1e-6, (gap, expected)
    return gap


def assert_neutral(session):
    assert session.controller.poses == DEFAULTS
    for side, pose in DEFAULTS.items():
        for name in CHANNELS:
            assert abs(bpy.data.objects[f"{side}_INSTRUMENT"][name] - getattr(pose, name)) < 1e-8
        baseline.check_instrument(side)
        check_jaws(side)


def check_modal_events():
    """Exercise real event-routing code with synthetic events; no GPU draw required."""
    window = bpy.context.window_manager.windows[0]
    area = next(area for area in window.screen.areas if area.type == "VIEW_3D")
    region = next(region for region in area.regions if region.type == "WINDOW")
    operator = SimpleNamespace(session=LiveSession(), provider=KeyboardInput(), selected="LEFT",
                               _window=window, _area=area, _closed=False)
    operator.pause = partial(live_ui.LAPSIM_OT_live.pause, operator)
    operator.select_instrument = partial(live_ui.LAPSIM_OT_live.select_instrument, operator)
    operator.finish = lambda: setattr(operator, "_closed", True)

    def send(token, value="PRESS", **overrides):
        params = dict(type=token, value=value, mouse_x=region.x + 10, mouse_y=region.y + 10,
                      shift=False, ctrl=False, alt=False, is_repeat=False)
        params.update(overrides)
        return live_ui.LAPSIM_OT_live.handle_event(operator, bpy.context, SimpleNamespace(**params))

    with bpy.context.temp_override(window=window, area=area, region=region):
        for key, (side, channel, direction) in KEY_BINDINGS.items():
            operator.session.reset()
            before = operator.session.controller.poses
            send(key)
            after = operator.session.controller.poses
            assert direction * (getattr(after[side], channel) - getattr(before[side], channel)) > 0
            other = "RIGHT" if side == "LEFT" else "LEFT"
            assert after[other] == before[other]
            send(key, is_repeat=True)
            assert operator.session.controller.poses == after, "Auto-repeat added a tap impulse"
            send(key, "RELEASE")
            assert not operator.provider.held
        send("SPACE")
        paused = operator.session.controller.poses
        send("W")
        send("WHEELUPMOUSE")
        assert operator.session.controller.poses == paused
        send("SPACE")
        send("TWO")
        before = operator.session.controller.poses
        send("WHEELUPMOUSE", shift=True)
        assert operator.session.controller.poses["RIGHT"].rotation > before["RIGHT"].rotation
        assert operator.session.controller.poses["LEFT"] == before["LEFT"]
        send("TAB")
        assert operator.session.controller.profile[0] == "Fast"
        send("W")
        send("WINDOW_DEACTIVATE")
        assert operator.session.controller.paused and not operator.provider.held
        send("R")
        assert_neutral(operator.session)
        send("ESC")
        assert operator._closed
    return len(KEY_BINDINGS)


def main():
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "blender/scenes/lapsim_ai_phase1b.blend"))
    initial_signature = baseline.signature()
    session = LiveSession()
    assert_neutral(session)
    original_pivots = {side: baseline.evaluated(f"{side}_INSTRUMENT").matrix_world.translation.copy()
                       for side in DEFAULTS}
    rng = random.Random(20260907)
    for step in range(2000):
        side = "LEFT" if step % 2 else "RIGHT"
        other = "RIGHT" if side == "LEFT" else "LEFT"
        before = baseline.evaluated(f"{other}_AXIAL").matrix_world.copy()
        before_jaw = bpy.data.objects[f"{other}_INSTRUMENT"]["jaw"]
        command = NormalizedCommand(side, **{name: rng.uniform(-4, 4) for name in CHANNELS})
        session.update([command], .05)
        baseline.check_instrument(side)
        check_jaws(side)
        assert baseline.evaluated(f"{other}_AXIAL").matrix_world == before
        assert bpy.data.objects[f"{other}_INSTRUMENT"]["jaw"] == before_jaw
    for side in DEFAULTS:
        assert baseline.evaluated(f"{side}_INSTRUMENT").matrix_world.translation == original_pivots[side]
        for value in (-1000, 1000):
            root = bpy.data.objects[f"{side}_INSTRUMENT"]
            root["jaw"] = float(value)
            root.update_tag()
            bpy.context.view_layer.update()
            check_jaws(side)
    session.reset()
    assert_neutral(session)
    # Introduce the Phase 1A demo deliberately; live start must remove its ownership.
    animate_demo()
    for side in DEFAULTS:
        bpy.data.objects[f"{side}_INSTRUMENT"].animation_data.nla_tracks.new()
    session = LiveSession()
    provider = KeyboardInput()
    provider.key("W", True)
    provider.key("J", True)
    session.update(provider.commands(), .05)
    expected = session.controller.poses
    for frame in (1, 41, 121, 241):
        bpy.context.scene.frame_set(frame)
        for side, pose in expected.items():
            root = bpy.data.objects[f"{side}_INSTRUMENT"]
            assert root.animation_data.action is None
            assert all(track.mute for track in root.animation_data.nla_tracks)
            for name in CHANNELS:
                assert abs(root[name] - getattr(pose, name)) < 1e-8
            baseline.check_instrument(side)
            check_jaws(side)
    session.controller.paused = True
    session.update(provider.commands(), 5)
    assert session.controller.poses == expected
    session.reset()
    assert_neutral(session)
    live_ui.register()
    live_ui.register()  # rerunning the entry script is safe
    assert len(live_ui.hud_lines(session, "LEFT")) == 5
    modal_keys = check_modal_events()
    live_ui.unregister()
    build_live_scene()
    assert baseline.signature() == initial_signature, "Live scene regeneration differs"
    report = {
        "status": "PASS", "blender": bpy.app.version_string,
        "unit_tests": result.testsRun, "repeated_live_updates": 2000,
        "maximum_pivot_error_metres": baseline.maximum_pivot_error,
        "pivot_tolerance_metres": baseline.PIVOT_TOLERANCE,
        "pivot_translation_drift_metres": 0.0,
        "jaw_driver_boundary_cases": 4,
        "reset_all_five_channels": "PASS", "independence": "PASS",
        "animation_and_nla_isolation": "PASS", "pause": "PASS",
        "jaw_angles_and_tip_separation": "PASS", "ui_registration_rerun": "PASS",
        "modal_short_tap_bindings_checked": modal_keys,
        "modal_repeat_pause_reset_focus_wheel": "PASS (synthetic events)",
        "saved_scene_regeneration": "PASS", "semantic_sha256": initial_signature,
        "scope": "Background controller/rig checks; interactive UI recorded separately",
    }
    out = ROOT / "outputs/phase1b"
    out.mkdir(parents=True, exist_ok=True)
    (out / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PHASE1B_VALIDATION " + json.dumps(report))


if __name__ == "__main__":
    main()
