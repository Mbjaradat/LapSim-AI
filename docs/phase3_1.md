# Phase 3.1 — release stability and collision safety

This checkpoint keeps the existing peg scene and input mappings. No scene rebuild
is needed. All changes take effect when control mode starts from the updated scripts.
Manual validation is required; this is an educational engineering prototype.

## Steering

Previously yaw/pitch used the stabilized wrist's neutral-relative image position.
They now use a weighted palm centre: wrist landmark 0 contributes 40%, and MCPs
5/9/13/17 contribute 15% each. No thumb or fingertip coordinates enter steering.
N captures a separate median neutral palm centre; recalibrate after restarting.
Wrist coordinates remain available for debug, and palm scale, orientation and pinch
continue to drive depth, roll and jaws respectively.

Sensitivity and filtering are unchanged: full yaw/pitch command at 0.08 normalized
image displacement; command deadzone 0.003; 60 ms EMA; output deadband 0.002;
maximum normalized positional step 0.03 per frame. Jaw/depth/roll filters, gains,
handedness, loss behavior, startup countdown and transport protocol are unchanged.

Synthetic evidence: with fixed palm landmarks, fingertip opening/closing changes
the jaw command by over 0.95 while yaw/pitch stay zero. A separate 0.012 normalized
wrist-only bias is attenuated by 60% geometrically; after the existing filters and
deadbands the example produces 0 versus 0.090909 with wrist steering. That example
is not a measured real-camera improvement. Whole-palm movement still steers, and
correlated errors across all landmarks can still move the estimate.

## Collision contract

Input → existing controller → proposed pose → `CollisionConstraint` → accepted
controller pose → Blender rig → existing peg interaction. Both keyboard and webcam
use this path only in peg scenes. Other scene modes retain their previous behavior.
No mesh query runs in the live constraint code and no collision modifier is required.

All settings are centralized in `simulator/collision.py`, with existing rig dimensions
supplied by `live_rig.py`:

| Proxy/constraint | Value |
| --- | --- |
| Board support plane | z = -0.112 m |
| Internal shaft capsule | trocar to shaft distal reference, radius 3 mm |
| Two articulated jaw capsules | length 18 mm, radius 2.5 mm, hinges ±1.5 mm |
| Jaw/roll orientation | Same Ry(yaw) Rx(pitch) Rz(roll) and ±30° jaw articulation as rig |
| Held ring lower extent | contact + existing grasp offset − 1.6 mm |
| Clearance | 0.1 mm |
| Maximum nominal endpoint sweep step | 0.75 mm |
| Large-request budget | 64 substeps; excess motion is left unapplied |
| Pair-contact refinement | Nine binary-search iterations |

Board penetration is resolved by retracting along the instrument's own shaft,
preserving its fixed trocar and orientation. Angular motion can slide at contact
with a small insertion correction. Inter-instrument overlap rejects the penetrating
joint component, accepting a safe fraction when possible. Joint order is jaw, roll,
yaw, pitch, insertion; side order is deterministic Left then Right. Accepted poses
are committed back into the controller, avoiding hidden movement accumulation.
There is no persistent collision lock; movement away is evaluated immediately.
Reset clears diagnostic contacts and restores neutral poses and task state.

Existing capture radius (9 mm), thresholds (close ≤0.25 / open ≥0.65), exclusive
ownership, controlled handoff, matching targets and reset behavior are unchanged.
Handoff must now occur beside the donor jaws, not through their occupied volume.

## Manual validation

1. Stop existing control mode with Esc and restart Blender to clear cached modules.
   Open `blender/scenes/lapsim_ai_peg_transfer.blend`.
2. Open `blender/scripts/start_webcam.py` in the Text Editor, Alt+P; hover the 3D
   Viewport, F3 → **LapSim: Start Webcam Control**.
3. In the preview select each hand using 1/2, complete N/O/C captures, then keep
   both hands visible through the five-second countdown. If focus loss pauses
   LIVE, return to the viewport and use Space with both hands visible.
4. **Release stability:** hold the palm still and repeatedly open/close pinch.
   Confirm substantial jaw movement with minimal steering. Grasp a ring, move
   above its numbered target and release with the palm still. Check for any kick.
5. **Board contact, each instrument:** insert deliberately toward the board, both
   with closed and open jaws. The jaws should stop above the surface. Try lateral
   movement in both directions, then retract. Neither tool should remain stuck.
6. Repeat board contact while holding a ring. Its lower surface must stay above
   the board. Move sideways, lift, lower and release near the correct target.
7. **Bimanual contact:** at safe height bring the tools together, try crossing
   shafts/jaws and opening/rolling at contact. Further penetration should stop;
   separating either hand or retracting should work immediately.
8. **Task regression:** finish all six rings, including a handoff. Lift a ring to
   the central area, approach the receiver from beside/slightly nearer the camera
   than the donor, close within reach, then open donor. If blocked, reposition;
   do not force the jaws through each other. Confirm 6/6 COMPLETE.
9. Press R in the Blender viewport. Confirm 0/6 READY, all source rings restored,
   no ownership, neutral instruments and paused webcam mode. Space resumes.
10. Optionally repeat board/contact/escape with `start_live.py` and keyboard mode
    to verify the same physical constraints. Existing keys are in `peg_transfer.md`.

## Verification and limits

Run `.\.venv\Scripts\python.exe -B -m unittest discover -s tests` from the repository
root, then Blender background scripts `verify_peg_transfer.py`, `verify_phase2d.py`
and `verify_phase3.py` with `--python-exit-code 1`. The peg trial checks constrained
grasp/handoff/placement, clearance at every update, evaluated tool vertices, reset,
pivots, existing keyboard events, reproducibility and previous scene hashes.

A local 240-frame-per-case Python benchmark at controller-limited 30 Hz measured
board constraint mean 1.52 ms / p95 1.93 ms and bimanual constraint mean 2.41 ms /
p95 2.85 ms. These measure the constraint only, not MediaPipe, Blender drawing or
end-to-end FPS. No new dependency, texture, scene geometry or physics engine is added.

These are conservative mathematical proxies, not full collision physics. The
support plane extends beyond the visible board. Capsule ends can stop slightly
early; cosmetic stripes are not independently modeled. Pegs and loose rings do not
have general collision response, and held-ring versus the other instrument is not
solved beyond the tool capsules/controlled ownership interaction. Drops still use
the existing deterministic settling rule. Rings do not rotate/deform. Substepping
is bounded, not exact continuous mesh collision detection; very large requests
may be only partly accepted. Contact can change insertion slightly or restrict jaw
opening until clearance is restored. No telemetry, scoring or clinical claims.
