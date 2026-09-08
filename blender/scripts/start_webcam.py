"""Run in the Phase 1B scene's Text Editor, then F3 in a 3D Viewport."""
from pathlib import Path
import sys
import bpy

script_path = Path(bpy.path.abspath(__file__)).resolve()
if not script_path.is_file():
    text = getattr(bpy.context.space_data, "text", None)
    if text and text.filepath:
        script_path = Path(bpy.path.abspath(text.filepath)).resolve()
    elif bpy.data.filepath:
        script_path = Path(bpy.data.filepath).resolve().parent.parent / "scripts/start_webcam.py"
ROOT = script_path.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(script_path.parent)]
import webcam_ui
# Refresh edited source on Text Editor reruns, without replacing an active modal.
if webcam_ui.live_ui.ACTIVE is None:
    import importlib
    if hasattr(webcam_ui, "view_menu"):
        bpy.types.VIEW3D_MT_view.remove(webcam_ui.view_menu)
    importlib.reload(webcam_ui)
webcam_ui.register()
print("In a 3D Viewport: F3 > LapSim: Start Webcam Control. Calibrate both hands; LIVE starts after a valid 5-second countdown.")
