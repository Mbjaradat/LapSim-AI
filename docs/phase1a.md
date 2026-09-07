# Phase 1A: rigid instrument mechanics

An original primitive-only engineering demonstration, without physical, biomechanical, or clinical validation. No anatomy, webcam, AI, cutting, clipping, tissue deformation, or surgical scoring is implemented.

## Generate and verify

Run in PowerShell from the repository root:

```powershell
$blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
& $blender --background --factory-startup --python-exit-code 1 --python blender/scripts/build_phase1a.py -- --render
& $blender --background --factory-startup --python-exit-code 1 --python blender/scripts/verify_phase1a.py
```

The builder replaces `blender/scenes/lapsim_ai_phase1a.blend`. It resets Blender's in-memory scene, not any other project files. Omit `--render` to skip the preview. The main `.blend` is intentionally trackable; local `outputs/phase1a/preview.png` and `validation.json` are ignored. No packages or external assets are required. No embedded scripts, registered handlers, or custom driver namespace are needed for playback; drivers use native simple arithmetic expressions.

## Coordinates, units and controls

One Blender unit is one metre. World +X is right, +Y is deeper into the box, +Z is up. The neutral instrument points along local -Z into the workspace. The camera looks predominantly toward +Y and downward, so screen directions do not equal world axes.

| Parameter | Configuration |
| --- | --- |
| LEFT_TROCAR | (-0.085, 0, 0.12) m |
| RIGHT_TROCAR | (0.085, 0, 0.12) m |
| Shaft length / radius | 0.42 m / 0.003 m |
| Jaw length | 0.018 m; static open geometry |
| Yaw | -35 to +35 degrees; rotation about Y |
| Pitch | -25 to +25 degrees; rotation about X |
| Insertion | 0.12 to 0.28 m from pivot to distal shaft reference |
| Axial rotation | -180 to +180 degrees around the shaft's local +Z |
| Pivot tolerance | 1e-6 m (1 micrometre), a numerical tolerance only |

`blender/scripts/config.py` centralizes limits, trocar positions, shaft dimensions, camera, lighting and demonstration poses. The `InstrumentLimits` defaults and finite/clamping control contract live in `src/lapsim_ai/control/instrument.py`; config imports that contract. Limits are engineering choices, not anatomical or ergonomic recommendations. Keep insertion below shaft length when changing geometry.

Angles use Blender XYZ Euler order, with zero root Z rotation: orientation `R = Ry(yaw) Rx(pitch)`. Positive pitch moves the internal shaft toward +Y at zero yaw; positive yaw moves it toward -X at zero pitch. Axial rotation occurs on a child after translation and does not change the shaft centreline. Angles are bounded, not wrapped continuously; +180 to -180 traverses the available range.

## Fulcrum model

Let `P` be the fixed trocar, `u = R (0, 0, -1)` the internal unit direction, `d` insertion, and `L` shaft length. The distal shaft reference is `T = P + d u`; the external shaft reference is `H = P - (L-d) u`. Thus `(T-P)/d = -(H-P)/(L-d)`. With insertion held constant, angular changes give opposite handle/tip displacement with lever ratio `d/(L-d)`.

The rigid parent hierarchy enforces this geometrically: a rotation root remains at P; a child translates by -d along local Z; its child supplies axial rotation; shaft geometry extends from local Z=0 to Z=L. The jaws project beyond the distal shaft reference. Insertion is measured to that reference, not the jaw ends. There is no external handle-position solver or force model yet.

Native drivers clamp all four channels, and `apply_control()` additionally rejects nonfinite values and clamps before storage. UI transform locks discourage accidental pivot edits; they are not protection against arbitrary scripts or hierarchy edits. Do not move the rig with G/R/S: use its four properties.

## Camera and workspace

`LAPAROSCOPIC_CAMERA` is a perspective camera at (0, -0.42, 0.29) m, aimed at (0, 0.035, -0.045) m. It uses a 24 mm lens, 36 mm horizontal sensor (about 73.7 degrees horizontal field of view), 960×720 output, and 0.005–10 m clipping. There is no calibrated lens distortion, endoscope optical model, or depth-of-field simulation.

The dark training box has a 5 cm floor grid. Fixed cyan/amber ring crosshairs identify the left/right trocar centres. Shafts, asymmetric jaws, coloured stripes and external handle references are original primitives. Scope-adjacent area lighting and soft fill illuminate the workspace. The monitor view prioritizes internal shafts/tips and pivot markers; external handles may be outside the camera frame. Orbit the viewport to inspect them.

## Manual viewing and controls

1. Open `blender/scenes/lapsim_ai_phase1a.blend` in Blender 5.2.1.
2. Hover over the 3D viewport and press **Numpad 0**, or choose **View → Cameras → Active Camera**. The file is saved in camera view.
3. Press **Space** to play/pause. Frames 1–241 run at 30 fps with seven marked poses; the first and last poses match. Scrub the timeline to inspect intermediate motion. Playback speed depends on viewport performance.
4. Use **Z → Material Preview** for responsive inspection or **F12** for the lit camera render. Material Preview uses its own lighting; the render is the intended dark workspace appearance.
5. Orbit with middle mouse, or the navigation gizmo, to inspect external handles and the opposite tip motion. Numpad 0 returns to the camera.
6. For independent property testing, pause and select `LEFT_INSTRUMENT` or `RIGHT_INSTRUMENT` in the Outliner. In **Object Properties → Custom Properties**, inspect yaw, pitch, insertion and rotation. The saved animation owns these values on frame changes.

To temporarily detach both demonstration actions for manual editing, switch a panel to **Python Console** (Shift+F4), execute the following, then return to the 3D viewport with Shift+F5:

```python
for side in ('LEFT', 'RIGHT'): bpy.data.objects[side + '_INSTRUMENT'].animation_data.action = None
```

Now edit the four custom properties through Object Properties. Change one side at a time and observe that the other stays still. Reopen the original file without saving manual edits to restore the animation. No auto-run permission is needed for native simple-expression drivers.

## Verification design

`verify_phase1a.py` runs four standard-library control tests, opens the actual saved scene, and checks evaluated transforms at every one of 241 frames. It checks the fixed marker/root positions, distance of the pivot from the actual shaft centreline, insertion distance, all angular channels, and the opposite lever relation.

It then detaches animation in memory and exercises 200 seeded randomized controls, including out-of-range values, checking left/right independence in both directions. Four raw-property boundary cases bypass the API to test driver clamping. Finally it regenerates the scene from scratch and compares a semantic SHA-256 of mesh geometry/topology, hierarchy, materials, camera/light settings, and all object transforms across all animation frames against the saved scene. This checks deterministic content, not byte-identical .blend serialization. See validation_phase1a.md for the recorded run.

## Limitations and next gate

This is rigid kinematics, not a physics solver. Instruments can intersect each other or the box. There is no collision response, tissue, port friction, haptics, jaw actuation, lens calibration, or medical fidelity. The finite pivot tolerance describes numerical accuracy, not mechanical realism. Material appearance and frame rate can vary by hardware.

Licensing remains pending: local implementation was authorized, but no public license grant has been finalized for code or generated scenes. No commit/push is performed by the scripts. Recommended Phase 1B is a small keyboard/manual-control usability pass with reset/pause and sensitivity settings, only after explicit authorization.
