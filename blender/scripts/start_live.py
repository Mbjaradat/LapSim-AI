"""Run explicitly in Blender's Text Editor or via --python; no add-on installation."""

from pathlib import Path
import sys
import bpy

# Text Editor execution uses a synthetic "scene.blend/text_name" __file__.
script_path = Path(bpy.path.abspath(__file__)).resolve()
if not script_path.is_file():
    text = getattr(bpy.context.space_data, "text", None)
    if text and text.filepath:
        script_path = Path(bpy.path.abspath(text.filepath)).resolve()
    elif bpy.data.filepath:
        script_path = Path(bpy.data.filepath).resolve().parent.parent / "scripts" / "start_live.py"
ROOT = script_path.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(script_path.parent)]

import live_ui

live_ui.register()
print("LapSim registered. In the 3D Viewport: F3 > LapSim: Start Keyboard Control.")


def start_in_viewport():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                region = next(r for r in area.regions if r.type == "WINDOW")
                with bpy.context.temp_override(window=window, area=area, region=region):
                    bpy.ops.lapsim.live("INVOKE_DEFAULT")
                return None
    print("No 3D Viewport available. Open one and use F3 to start LapSim.")
    return None


if "--start-live" in sys.argv and not bpy.app.background:
    bpy.app.timers.register(start_in_viewport, first_interval=0.75)
