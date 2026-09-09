# Peg transfer MVP checkpoint

Phase 3.1 adds palm-centre steering and lightweight board/tool collision safety.
See [Phase 3.1 behavior and manual checks](phase3_1.md); the existing scene opens
unchanged and updated scripts activate the constraints. The original limitations
below describe the initial MVP; Phase 3.1 supersedes its board/tool pass-through behavior.

The primary MVP is now a procedural box trainer, not a cholecystectomy scene.
Previous anatomy and Phase 3A scenes remain reference checkpoints. This is an
experimental educational/research prototype, without clinical validation,
competency certification or scoring. Manual usability validation is pending.

## Start and test

1. Open `blender/scenes/lapsim_ai_peg_transfer.blend` in Blender 5.2.
2. Open `blender/scripts/start_webcam.py` in Blender's Text Editor and press Alt+P.
   Hover the 3D Viewport, press F3, choose **LapSim: Start Webcam Control**.
3. In the webcam preview, select Left with **1**, Right with **2**. For each hand,
   hold a comfortable neutral pose and press **N** until capture finishes; use
   **O** with an open pinch and **C** with a closed pinch, waiting for each capture.
   Both hands must be Ready and visible through the five-second LIVE countdown.
4. Return focus to Blender. If focus loss paused an already-LIVE session, show
   both hands and press **Space** in the viewport. The task remains READY until
   a ring is grasped. Do not press animation playback.
5. Open the left jaws, approach ring 1's centre between the jaw pads, then close
   the pinch. Capture occurs within 9 mm on a closing threshold crossing; closing
   far away and moving in will not capture. Reopen and retry if necessary.
6. Lift roughly 25 mm above the pegs, then move the ring over the central circle.
   Hand motion toward the webcam retracts/lifts; away inserts/lowers. Existing
   yaw/pitch, depth, roll and jaw mappings are unchanged by this task.
7. Approach with the right jaws open, close them near the held ring, **then open
   the left jaws**. Right takes ownership without a position jump. The receiver
   must remain close and closed while the donor opens; reopening or moving away
   cancels the pending handoff.
8. Move above the matching numbered target, lower near its seat and open the
   right jaws. Within 6 mm horizontally and 12 mm vertically the ring seats on
   a free peg. A correct target outline turns green and the counter increments.
   A wrong numbered target is recorded INCORRECT and does not increment it.
   An occupied target cannot accept another ring.
9. Repeat for all six rings. The HUD must show **Objects: 6 / 6**, **COMPLETE**.
   Completion freezes object interaction and the basic timer until reset.
10. Press **R with the pointer in Blender's viewport**: all rings, ownership,
    completion, timer and instrument poses reset. Webcam mode pauses; **Space**
    resumes once both hands are valid. R in the webcam preview instead resets
    the selected hand's calibration, as before.
11. Also release one ring away from a peg, reacquire it, and deliberately try a
    wrong target. Release away from a valid seat is a DROPPED event: it settles
    on the board-height plane, nudging beside obstructed pegs if necessary.
    Off-board/unreachable drops can be recovered with R.

Keyboard alternative: run `blender/scripts/start_live.py`, then F3 →
**LapSim: Start Keyboard Control**. Existing mappings remain:

| Action | Left instrument | Right instrument |
| --- | --- | --- |
| Pitch | W/S | Up/Down |
| Yaw | A/D | Left/Right |
| Insert/retract | Q/E | Page Up/Page Down |
| Roll | Z/X | N/M |
| Open/close jaws | F/G | J/K |

Space pauses/resumes; R resets; Tab sensitivity; 1/2 selects the mouse-controlled
instrument; wheel depth, Shift+wheel roll; Esc stops. Numpad 0 restores camera
view. Material Preview with scene lights/world provides shadows and depth cues.

## Architecture and geometry

`simulator/tasks/peg_transfer.py` composes the existing `GraspWorld`.
`peg_interaction.py` reads evaluated jaw contact points and applies task state to
the scene. `LiveSession` selects this adapter only when `peg_transfer_config`
exists. Keyboard and webcam therefore use the same task. Vision, calibration,
transport, limits and rig math are unchanged; the Phase 3A adapter remains intact.

Task states: READY → first capture → RUNNING → six correct released rings →
COMPLETE. Per-ring states are SOURCE, HELD, CORRECT, INCORRECT and DROPPED.
Ownership is exclusive; an armed handoff does not create a second owner. Timer
advances on unpaused RUNNING updates and freezes on completion. No scores,
results screen, persistent records or motion metrics are implemented.

Units are metres. Existing trocars remain at x=±0.085, y=0, z=0.12.
The 106×86 mm board has source columns x=-0.033/-0.014 and matching target
columns x=+0.033/+0.014, rows y=0.020/0.042/0.064, ring seats z=-0.110.
The central handoff is (0,0.042,-0.080). All twelve seats and the handoff pass
inverse reach checks for both instruments with 10% joint-range margins. Lift
paths use the nearby instrument and central handoff; the full free-space volume
is not asserted to satisfy that margin for both hands everywhere.

Camera: (0,-0.105,0.025), aimed at (0,0.042,-0.099), perspective 48 mm,
36 mm sensor, 960×720. Original rounded board, titanium-style pegs, numbered
ivory rings, teal source guides and amber targets use procedural materials.
Collections separate board, transfer objects, instruments and environment.
No anatomy, downloads, new dependencies or external textures are used.

## Rebuild and verify (PowerShell, repository root)

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/build_peg_transfer.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/verify_peg_transfer.py
```

The builder saves only the peg scene. Add `-- --render` for an optional headless
preview. Generated reach/validation reports live in ignored `outputs/peg_transfer/`.
Verification covers a complete six-ring controller-driven handoff trial,
placement/reset, initial intersections, camera framing, pivots, keyboard controls,
saved-scene regeneration and hashes of previous scene files.

## Limits

Rings translate without rotating or deforming. Grasp is proximity-based; there
is no continuous collision solver, realistic gravity, peg friction or enforced
lift/handoff requirement. Drops settle instantly and may be displaced beside an
occupied peg; the support plane extends beyond the visible board. Instrument and
ring geometry can intersect during motion. Paused input holds task state; tracking
loss preserves the existing safe held-pose behavior. Live viewport FPS and webcam
ergonomics require manual testing on the target laptop. No release packaging or
licensing finalization is performed in this checkpoint.
