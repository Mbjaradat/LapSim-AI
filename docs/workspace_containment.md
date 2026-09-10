# Phase 4 pre-validation patch — trainer containment

The existing peg scene is unchanged. Restart control mode with updated scripts;
no scene regeneration, camera change, visible walls, telemetry change or new
metric is introduced. Trocar positions, joint limits and input sensitivities stay
unchanged.

## Geometry and constrained region

The previous system constrained the board floor and instrument intersections,
but had no lateral or camera envelope. Existing joint limits permit working tips
to travel outside the small trainer/camera frame.

The new convex region is the intersection of:

* Board footprint: x **[-0.053, +0.053] m**, y **[-0.001, +0.085] m**, derived
  from board centre (0, 0.042) and dimensions 0.106 × 0.086 m.
* Floor **z = -0.112 m**, the existing board collision plane.
* Ceiling **z ≈ -0.030055 m**: the highest neutral distal shaft reference plus
  two jaw lengths (36 mm). This gives lifting room above neutral while stopping
  retraction from carrying the working geometry out of view.
* Four planes from the actual scene camera's view frame, inset **4% on each
  image edge**. The camera remains at (0,-0.105,0.025), aimed at (0,0.042,-0.099),
  with its existing 48 mm lens, 36 mm sensor and 960×720 frame. These planes can
  stop movement before a physical board-side limit at shallow depths.

All thirteen required seat/handoff points retain the existing 10% joint-range
reach margin. The full controller-driven six-ring trial tests actual grasp and
placement poses with containment enabled; a reachable mathematical seat is not
assumed to imply that jaws may penetrate the board.

Contained proxies: the last **18 mm of shaft** (3 mm radius), both articulated
jaws (18 mm long, 2.5 mm radius), the shaft-tip/grasp-contact references, and each
held horizontal ring (outer radius **7.1 mm**, vertical half-thickness **1.6 mm**).
Plane tests use full capsule/ring support extents, not just their centres. Existing
0.1 mm clearance is retained. The proximal shaft, handles and fixed trocars are
intentionally not inside this small distal working envelope.

## Boundary behavior

The existing joint-space substeps now test all containment planes alongside
board/tool collisions. When possible, a bounded insertion correction along the
same shaft preserves movement parallel to a plane. Invalid joint components are
limited to a valid fraction. Insertion correction is capped to 0.75 mm per
substep; no pivot or distal point is independently translated. Other valid joint
components and inward movement remain available. Corners, jaw opening and
simultaneous tool contact may restrict several components at once.

Accepted poses are committed to the controller before rig and telemetry updates.
Repeated rejected outward intent does not add fake path. The existing ownership,
handoff, placement, task and telemetry implementations remain unchanged. Reset
clears contact state as before.

## Manual stress test

1. Restart Blender to clear cached modules. Open
   `blender/scenes/lapsim_ai_peg_transfer.blend`; run
   `blender/scripts/start_webcam.py` with Alt+P, then F3 →
   **LapSim: Start Webcam Control** in the viewport. Calibrate both hands with
   1/2 and N/O/C, finish the countdown, and resume with Space if needed.
2. Move the left grasper toward the left image/board edge until it stops.
   Continue outward for several seconds: no escape or visible oscillation.
   Move parallel to the edge in both directions where clearance permits, then
   return inward. Verify recovery immediately.
3. Repeat at the right, front (near-camera), back, floor and upper/retraction
   limits. Repeat with the right instrument. Camera planes may be the first
   limit reached; do not expect every joint motion to reach a board edge.
4. Open/close and roll the jaws near a limit: the complete working geometry must
   stay inside. Back away slightly if opening requires more room.
5. Grasp a ring and repeat each boundary stress test. Its outer edge must remain
   inside, including the floor. Move inward and release near a valid peg.
6. Bring both tools near one side and toward each other. Verify neither crosses
   the other or the workspace boundary; separate and retract normally.
7. Complete all six rings including a handoff beside the donor jaws. Check the
   normal COMPLETE result. Holding stationary against a boundary should not
   noticeably grow path; accepted sliding or collision corrections legitimately do.
8. R in Blender resets; confirm neutral tools and source rings. Space resumes.

## Validation and limitations

Pure tests isolate each plane direction for both tools, open/rolled jaw and
held-ring extents, contact stability, sliding, escape, near-edge grasp/release
and accepted-pose telemetry. The headless peg trial additionally checks every
accepted working proxy against all ten planes, projects reference/jaw endpoints
into the camera inset, and verifies six transfers, handoffs, metrics, reset,
reproducibility and pivots. Existing Phase 3.1 and Phase 4 tests remain in the
complete suite. No GUI automation is used.

This is a conservative invisible mathematical envelope, not rigid-body physics.
Frustum inclusion guarantees framing, not freedom from occlusion by the other
instrument, rings or HUD. Full proximal shafts may leave the image. Loose dropped
rings retain the existing settling rules; this patch constrains held rings, not
all free objects. Capsule clearances can stop slightly early. At corners or
combined tool contact, repositioning may be necessary. Manually editing board or
camera geometry is unsupported without rebuilding/revalidating the configuration.
Manual feel and visibility remain to be tested by the user. No commit or push.
