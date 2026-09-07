"""Run with Blender --background --python this_file -- [--render]."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent)]

import bpy
from scene import build_scene
from demo import animate_demo


def main():
    scene = build_scene()
    animate_demo()
    target = ROOT / "blender/scenes/lapsim_ai_phase1a.blend"
    target.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    print(f"PHASE1A_SCENE_SAVED: {target}")
    if "--render" in sys.argv:
        out = ROOT / "outputs/phase1a"
        out.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(out / "preview.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
