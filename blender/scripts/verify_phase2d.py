"""Small headless check: existing scene/rig, no webcam, save, render or GUI."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent)]
import bpy
from live_rig import LiveSession
from config import DEFAULTS
from lapsim_ai.control.hand_mapping import InstrumentTarget
from lapsim_ai.control.controller import CHANNELS
import verify_phase1a as baseline
from verify_phase1b import check_jaws, check_modal_events
import webcam_ui
import live_ui

bpy.ops.wm.open_mainfile(filepath=str(ROOT / "blender/scenes/lapsim_ai_phase1b.blend"))
session = LiveSession()
pivots = {side: baseline.evaluated(f"{side}_INSTRUMENT").matrix_world.translation.copy() for side in DEFAULTS}
for side in DEFAULTS:
    other = "RIGHT" if side == "LEFT" else "LEFT"
    before = session.controller.poses[other]
    target = InstrumentTarget(side, True, .2,-.3,.4,-.1,.8)
    for _ in range(100):
        session.update_targets([target], .05)
    expected = target.to_control(DEFAULTS[side], session.controller.limits)
    for name in CHANNELS:
        assert abs(bpy.data.objects[f"{side}_INSTRUMENT"][name] - getattr(expected,name)) < 1e-7
    assert session.controller.poses[other] == before
    baseline.check_instrument(side)
    check_jaws(side)
    held = session.controller.poses
    session.update_targets([InstrumentTarget(side)], .05)
    assert session.controller.poses == held
    assert baseline.evaluated(f"{side}_INSTRUMENT").matrix_world.translation == pivots[side]
webcam_ui.register()
webcam_ui.register()
assert hasattr(live_ui.LAPSIM_OT_live, "draw_hud")
assert hasattr(live_ui.LAPSIM_OT_live, "select_instrument")
keys = check_modal_events()
print(f"PHASE2D PASS: both sides/all fields, jaws, loss hold, fixed pivots, {keys} keyboard bindings, UI registration; no webcam or GUI")
print(f"Pivot error {baseline.maximum_pivot_error} m; tolerance {baseline.PIVOT_TOLERANCE} m")
