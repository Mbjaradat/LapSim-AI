"""Reproducible live scene; does not modify the Phase 1A scene file."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent)]

import bpy
from scene import build_scene
from live_rig import add_live_jaws, LiveSession
from config import LIVE_CAMERA_LENS_MM


def build_live_scene():
    scene = build_scene()
    add_live_jaws()
    LiveSession()
    scene["prototype"] = "LapSim-AI Phase 1B | live controls | unvalidated engineering prototype"
    scene["control_mode"] = "Keyboard (start via LapSim panel)"
    scene.render.engine = "CYCLES"
    scene.camera.data.lens = LIVE_CAMERA_LENS_MM
    scene.camera.data.passepartout_alpha = 1.0
    # Viewport-only diffuse colors brighten primitives without changing render nodes.
    bpy.data.materials["Cavity charcoal"].diffuse_color = (.075, .095, .12, 1)
    bpy.data.materials["Grid muted blue"].diffuse_color = (.18, .26, .30, 1)
    bpy.data.materials["Shaft brushed steel"].diffuse_color = (.75, .82, .9, 1)
    # Use material colors in the solid viewport: predictable, inexpensive interaction.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.shading.type = "SOLID"
                space.shading.color_type = "MATERIAL"
                space.shading.light = "STUDIO"
                space.shading.show_shadows = True
                space.shading.show_cavity = True
                space.shading.background_type = "WORLD"
                space.overlay.show_overlays = False
                space.show_region_toolbar = False
                space.region_3d.view_camera_zoom = 12
    note = bpy.data.texts.new("START_HERE.txt")
    note.write("LapSim-AI Phase 1B\n\nRun blender/scripts/start_live.py in Blender's Text Editor, "
               "then hover the 3D Viewport and F3 > LapSim: Start Keyboard Control.\n"
               "Or use the documented command-line launcher. No auto-run setting is needed.\n"
               "Space pause/resume; R reset; Tab sensitivity; Esc stop.\n"
               "See docs/phase1b.md for all keys. No webcam, anatomy, or clinical validation.\n")
    return scene


def main():
    scene = build_live_scene()
    target = ROOT / "blender/scenes/lapsim_ai_phase1b.blend"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    print(f"PHASE1B_SCENE_SAVED: {target}")
    if "--render" in sys.argv:
        out = ROOT / "outputs/phase1b"
        out.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(out / "preview.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
