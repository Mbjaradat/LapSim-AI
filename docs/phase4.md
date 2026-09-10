# Phase 4 — objective session telemetry

The existing peg scene, controls, collisions and task are unchanged. Restart
control mode to load the new scripts; no scene regeneration is needed. Results
describe simulator behavior only, not surgical proficiency, FLS performance,
clinical competence or certification. No AI coaching or efficiency score is added.

## Architecture and definitions

`src/lapsim_ai/telemetry/session.py` observes plain task state, owners, placements,
accepted tool reference positions, elapsed seconds and pause state. It has no
MediaPipe, transport or Blender dependency. The peg adapter collects these inputs
after constrained rig updates and task updates. Ownership/placement logic is not
modified. Event observations occur once per simulator update.

| Metric | Exact definition |
| --- | --- |
| Active completion time | Sum of unpaused observed monotonic-clock intervals from first successful grasp through COMPLETE; seconds |
| Objects completed / total | Final count of correctly seated rings / required rings |
| Successful grasps | Ownership transitions into a hand, including a receiving hand in a handoff |
| Releases | Ownership transitions out of a hand, including the donor in a handoff |
| Successful handoffs | One update changes an object's owner directly from one hand to the other |
| Drops | Held → unowned with task placement status DROPPED |
| Incorrect placements | Held → unowned with status INCORRECT |
| Successful placements | Held → unowned with status CORRECT; repeated successful placements count again after a regrasp |
| Left/right path | Sum of threshold-accepted distances between that tool's world-space TIP_REFERENCE positions, metres |
| Total path | Left path + right path |
| Paused seconds | Sum of observed pause intervals inside the session, seconds |

Event counts can exceed six because recovery/regrasp/replacement events are real
additional actions. Failed grasp attempts are omitted: closing empty jaws does
not reliably establish grasp intent. Movement efficiency is omitted because no
defensible reference trajectory or task-adjusted denominator is defined.

## Timing, pauses and path noise

First grasp uses the existing READY → RUNNING boundary. Pre-grasp movement and
calibration/countdown time are excluded. The starting update interval is counted;
event timing precision is one simulator update. The Blender adapter uses
`time.perf_counter()` differences, not keyboard tap/wheel movement dt. Therefore
synthetic keyboard step sizes cannot inflate session time. The original task's
internal movement-dt timer is retained for compatibility; result time is the new
monotonic active-time measurement.

Paused updates record pause intervals and refresh tip anchors without adding
time/path. The first resumed sample also reanchors, excluding any displacement
across the paused interval. Space and focus-loss pause behavior are unchanged.
Tracking loss itself does not pause the existing task: active time continues,
missing instruments hold and produce no path, and a valid other instrument may
continue. This follows the existing task session state.

Paths use the existing `LEFT_TIP_REFERENCE` and `RIGHT_TIP_REFERENCE`, located at
the distal shaft/jaw-base reference. They are independent of jaw opening and
are not webcam coordinates or moving jaw-tip vertices. Small jaw-related
collision corrections that actually move the shaft are real tool motion.

Each side retains a distance anchor. Displacement below **0.0005 m (0.5 mm)** is
ignored until net displacement reaches the threshold, at which point the full
anchor-to-current chord is added and the anchor advances. This suppresses small
stationary jitter while allowing slow deliberate translation to accumulate.
Subthreshold loops and between-update curvature are undercounted; larger jitter
can still count. This is a documented filtered path estimate, not an exact curve
integral. No additional control smoothing is applied.

## Result model and storage

Version 1 is a JSON-compatible dictionary with:

```text
schema_version, task, outcome (COMPLETE or STOPPED)
start_seconds, end_seconds, active_seconds, paused_seconds
objects_completed, objects_total
counts: grasps, releases, handoffs, drops,
        incorrect_placements, successful_placements
path_metres: LEFT, RIGHT, TOTAL
path_threshold_metres
pause_intervals: [{start_seconds, end_seconds}]
events: [{type, time_seconds, object?, side?, previous_owner?, owner?, ...}]
tip_samples: [{time_seconds, active_seconds, tips_metres: {LEFT, RIGHT}}]
truncated: {events, samples, pauses}
```

Times are relative to the current observer, not UTC or account identity. Active
time/counts/path are exact according to the definitions above even if diagnostic
history is truncated. Storage is bounded: latest 4,096 events, 1,024 pause intervals,
and 600 tip samples (at most about 10 Hz). Truncation flags identify incomplete
histories. There is no per-frame video/landmark recording, database or cloud.

Completion freezes a detached result snapshot. Esc/stop freezes an incomplete
STOPPED snapshot at the last observed update if a session had started. Repeated
stop calls do not overwrite a COMPLETE result. The adapter keeps the JSON string
in the in-memory scene custom property `peg_session_result`; nothing is written
automatically to disk. Saving the Blender scene manually would include this
property. R/reset or a new control session clears it, all samples, counters,
paths, timing and pause history. Prior history is not retained automatically.

The existing HUD shows a restrained completion summary: active mm:ss (floored
whole seconds), objects, grasps, drops, handoffs, incorrect/successful placements,
and left/right/total path to three decimal metres. JSON preserves full precision.

## Exact manual validation

1. Restart Blender, open `blender/scenes/lapsim_ai_peg_transfer.blend`, run
   `blender/scripts/start_webcam.py` (Alt+P), then hover the viewport and use
   F3 → **LapSim: Start Webcam Control**.
2. Select each hand with 1/2 in the preview, complete N/O/C and the five-second
   countdown. Resume with Space if returning focus paused an already-LIVE mode.
3. Move the left tool excessively **before grasping**. READY motion intentionally
   does not count. Grasp ring 1 to start the measured session, then repeat a
   deliberate safe left-tool detour so left path should increase.
4. Hand ring 1 to the right instrument: approach beside the donor, close receiver,
   then open donor. This adds one handoff, one donor release and one receiver grasp.
5. Release it onto the wrong numbered target (for example target 2). Regrasp and
   recover to target 1. This should add exactly one incorrect placement.
6. Grasp another ring and release away from a peg to deliberately drop it once.
   Regrasp it and place it correctly. Avoid an occupied target or a high release
   over a peg during the rest of the trial, which can create additional drops.
7. Pause for several seconds with Space; resume with both hands visible. Paused
   time and any paused displacement must not enter time/path results.
8. Complete all six rings. Inspect COMPLETE: 6/6; drops 1; incorrect placements 1;
   handoffs equal your successful handoffs; positive left/right/total paths with
   total equal to their sum (allow rounding). Time excludes the deliberate pause.
9. Press R **in Blender's viewport**. Confirm READY, 0/6, original rings/poses and
   cleared result. Space resumes webcam mode. Start a second session with a grasp
   and complete a clean trial: prior drop/incorrect-placement counts must be zero.
10. For exact JSON inspection, stop control with Esc, switch an area to Blender's
    Python Console and evaluate `bpy.context.scene.get('peg_session_result')`.
    After reset this must return `None`; after completion it contains the snapshot.

## Automated verification

Run the complete suite with `.\.venv\Scripts\python.exe -B -m unittest discover
-s tests`. Headless scripts: `verify_peg_transfer.py`, `verify_phase2d.py`, and
`verify_phase3.py`, using Blender `--background --factory-startup --python-exit-code 1`.
The full peg trial additionally asserts 12 grasps, 12 releases, six handoffs,
six successful placements, zero drops/incorrect placements, positive paths,
JSON/result agreement and reset isolation. No GUI automation is required.
