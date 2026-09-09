# Phase 3 engineering checkpoint — manual validation pending

This is an experimental educational/research simulator prototype. It is not
clinically validated, does not certify surgical competency, does not replace
supervised surgical training, and is not anatomically exact surgical simulation.
Phase 3 is **not complete** until the user evaluates the environment and controls.

## Build and open

From the repository root, in PowerShell:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/build_phase3.py
```

Open `blender/scenes/lapsim_ai_phase3.blend`. No auto-run setting or add-on install
is needed. The build reuses Phase 1B scene/rig functions in memory and saves only
the Phase 3 path; it does not overwrite the Phase 1A/1B files. All environment
geometry is reproducible from original repository scripts. No camera is opened
by building, opening or validating this scene.

## Workspace-first placement

Units are metres, +Z up, +X right. Existing trocar positions remain
LEFT=(-0.085,0,0.12), RIGHT=(0.085,0,0.12). Existing limits remain yaw +/-35 degrees,
pitch +/-25 degrees, insertion 0.12–0.28 m, roll +/-180 degrees and jaw 0–1.
No input sensitivities, webcam mapping, calibration or timing were changed.

`simulator/workspace.py` samples 11 values each for yaw/pitch/insertion: 1,331
contact positions per side. It models the same Ry(yaw) Rx(pitch) orientation and
uses a closed-jaw midline point 12.6 mm beyond the distal shaft reference.
The open-jaw midline differs slightly; runtime grasping uses evaluated jaw hinges.

The sampled bounding-box intersection seeds a 10 mm grid; inverse kinematics
checks every point against limits with a 10% margin. This yields **711 useful
shared points**, not a continuous collision-free volume. The design centre is
the midpoint of the two neutral contact positions: **(0, 44.20, -77.78) mm**.
Comfort margins mean yaw +/-28 degrees, pitch +/-20 degrees, insertion
0.136–0.264 m. No lateral extreme or far-retraction target is required.

| Target | World position (mm) | Required yaw magnitude | Pitch | Insertion |
| --- | --- | --- | --- | --- |
| Central design point | (0,44.20,-77.78) | 23.26 degrees | 11.60 degrees | 207.16 mm |
| Left bead | (-12,29.20,-77.78) | 20.26 / 26.13 degrees | 7.89 / 7.55 degrees | 200.23 / 209.61 mm |
| Right bead | (12,29.20,-77.78) | 26.13 / 20.26 degrees | 7.55 / 7.89 degrees | 209.61 / 200.23 mm |
| Gallbladder front target | (0,54.20,-92.78) | 21.78 degrees | 13.31 degrees | 222.85 mm |

Targets are inside both comfortable regions. Liver mass and the posterior
gallbladder neck provide context; they are not all designated manipulation
surfaces. Numerical reach does not establish ergonomic comfort or collision-free
approach. Full workspace bounds and target controls are saved in the scene's
`phase3_workspace` property and generated `outputs/phase3/workspace.json`.

Optional debug: in the Outliner enable the monitor/viewport restriction toggle
for `LAPSIM_DEBUG` (disabled by default). Toggle individual LEFT_REACH (cyan),
RIGHT_REACH (amber), and SHARED_COMFORTABLE_REACH (green) meshes. These small
octahedral point clouds are hidden from renders; disable again for training.

## Scene and anatomy

- `LAPSIM_ENVIRONMENT`: existing dark cavity surfaces, lights and perspective camera;
  the grid is removed and the camera is aimed toward the new operative field.
  Camera position, lens and sensor remain inherited from Phase 1B.
- `LAPSIM_ANATOMY`: an original deformed primitive liver mass; an original pear
  profile with fundus, body and narrow gallbladder neck; a short duct-like
  continuation and named `GALLBLADDER_ANCHOR`. All are **static**.
- `LAPSIM_INTERACTABLES`: two ivory 8 mm diameter spherical training beads.
- `LAPSIM_INSTRUMENTS`: unchanged instrument/trocar hierarchy and drivers.
- `LAPSIM_DEBUG`: optional reach clouds and the designated gallbladder target.

The liver/gallbladder relationship is illustrative, without anatomical precision
or a detailed biliary tree. Colors use simple materials, with no textures,
particles or physics. The scene retains the inexpensive solid/material-color
viewport used by Phase 1B. Geometry/provenance is recorded in
`assets/original/phase3/PROVENANCE.json`.

## Interaction foundation

`simulator/grasp.py` is pure input-independent logic. `phase3_interaction.py`
reads evaluated jaw contact positions on Blender's main thread and updates bead
positions. `LiveSession` enables this optional adapter only when the scene has
`phase3_interactions=True`; Phase 1 scenes continue without it. Both keyboard
and webcam use the same controller/rig and optional interaction adapter.

Bring open jaws within **9 mm of a bead centre**, then cross the closing threshold
**jaw <= 0.25**. A bead acquires one owner; an instrument owns at most one bead.
Nearest eligible pairs win; exact ties resolve by object name then side (LEFT
before RIGHT). Opening to **jaw >= 0.65** releases. Capture preserves the original
contact-to-object offset, avoiding a snap. The spherical bead follows translation,
not rotation; released beads stay at their release position (no gravity).

Holding closed jaws while approaching does not acquire: reopen and close nearby.
Simultaneous conflicting ownership is prevented; no handoff is inferred from
touching an already-owned bead. Tracking loss retains the controller's safe pose
and thus the held object's pose. Pause freezes interaction. **R in Blender**
resets both instruments and bead homes/ownership. Restarting a control mode also
resets them. Stop leaves the displayed scene frozen; the next session resets it.

There is no collision response, grasp force, tissue deformation or retraction.
Beads can pass through anatomy after capture because physical collision handling
is outside this checkpoint. Gallbladder retraction is intentionally deferred
until workspace and generic grasp behavior pass manual evaluation.

## Manual evaluation

1. Restart Blender to clear cached modules. Open the Phase 3 blend; use Numpad 0
   for camera view if needed. Check liver, green gallbladder and both ivory beads.
2. Run `blender/scripts/start_webcam.py` in the Text Editor (Alt+P). In a 3D
   Viewport use F3 → **LapSim: Start Webcam Control**.
3. In the preview select each hand with 1/2, capture N/O/C as before, and keep both
   visible. Confirm the five-second countdown, stationary instruments until LIVE,
   and correct physical Left/Right routing. Existing Space pause/resume applies.
4. Approach each bead with each instrument in turn. Open jaws, align near the
   bead, pinch closed, move gently, then open. Check offset-preserving pickup,
   stable following and release. If missed, reopen and approach again.
5. Grasp separate beads with both instruments. Try competing for one bead and
   confirm one owner only. Hide one hand briefly; confirm its instrument/bead hold.
6. Press R in Blender: verify neutral instruments and both beads back at home.
   Resume with Space. Approach the gallbladder's front region with each tip, but
   do not expect gallbladder pickup/retraction yet.
7. Evaluate camera composition, clearance, central comfort, lateral limitations,
   depth readability and frame responsiveness. Note any required awkward hand
   travel rather than increasing control limits.
8. Esc stops. Optionally use F3 → **LapSim: Start Keyboard Control** for comparison.
   Existing bindings remain: left WASD/QE/ZX/FG; right arrows/PgUp-PgDn/NM/JK;
   Space pause, R reset, Tab sensitivity, Esc stop. Do not save test positions
   over the generated baseline; regenerate if needed.

## Verification and provenance

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/verify_phase3.py
```

The headless check verifies saved-scene reach and target camera rays, initial
mesh intersections/trocar clearance, both sides' grasp/follow/release/reset,
existing pivot/fulcrum/jaw drivers, keyboard events, and semantic regeneration.
Face order and hidden-collection evaluated matrices are not stable save metadata;
the semantic comparison uses sorted topology and authored local transforms.
Reports in `outputs/phase3/` are generated intermediates, not runtime dependencies.
No visual/ergonomic or performance acceptance is claimed by these tests.

All **new Phase 3 geometry/materials are original procedural work**. No external
anatomy, textures, fonts or images were downloaded, traced or copied. The existing
Google MediaPipe model is unchanged and retains its separate Apache-2.0 record
under `assets/third_party/mediapipe_hand_landmarker/`. Original source licensing
and generated-scene licensing remain pending maintainer decisions; this addition
does not finalize or grant a public-release license. See THIRD_PARTY_LICENSES.md.
