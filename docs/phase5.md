# Phase 5 — guided hands-free native UX

Implemented, with automated regression checks passing. **Physical webcam and
solo hands-free acceptance remain pending.** No scene rebuild is required.
Restart Blender to load the updated scripts. No commit, push or release was made.

## Architecture and state ownership

`control/public_setup.py` contains `GuidedSetup`, `SetupStatus`, persistent HOME
references, framing/pose validation and directional guidance. It imports no
Blender, OpenCV, MediaPipe, task or telemetry modules. Its only calibration
adapter is `HandStabilizer.capture_pair(stage, raw_frames)`.

`capture_pair` runs the existing median calibration sampler in a candidate
stabilizer, validates both results, then installs both calibrations together.
A failure changes neither hand. Live filtering history, mapping and controller
rates are preserved; neutral capture resets the existing roll filter as before.
There is no second jaw mapping or replacement neutral estimator.

`control/public_runtime.py` contains `PublicRuntime`. It wraps the existing
`WebcamStartup` five-second gate, rather than implementing another LIVE timer.
It exposes setup, countdown, LIVE, tracking loss, pause and completion status.
Blender continues to own task state, controller pause and session reset. The
worker owns calibration. UDP carries the small setup status alongside existing
commands; a bounded stdin-message queue carries runtime presentation/recenter
requests back to the preview. No images are transmitted, saved or uploaded.

State progression:

```text
CAMERA_SETUP -> HOME_SETUP (or WAITING_FOR_HANDS)
HOME_SETUP -> HOME_COUNTDOWN -> OPEN_SETUP
OPEN_SETUP -> OPEN_COUNTDOWN -> PINCH_SETUP
PINCH_SETUP -> PINCH_COUNTDOWN -> CALIBRATION_COMPLETE
CALIBRATION_COMPLETE -> WAITING_FOR_LIVE -> LIVE_COUNTDOWN -> LIVE
LIVE <-> TRACKING_LOST
LIVE <-> PAUSED
LIVE -> COMPLETE
COMPLETE --explicit Retry--> WAITING_FOR_LIVE -> LIVE_COUNTDOWN -> LIVE
```

Each setup countdown returns to its setup state after invalid data, movement,
loss or a frame gap longer than 0.5 s. A completed calibration is read-only until
an explicit recenter action or a new worker session. Runtime tracking loss is a
presentation state over existing per-hand hold/reacquisition semantics, not a
new controller pause. There is no automatic recalibration or gesture trigger.

## Hands-free calibration and quality rules

Both uniquely identified physical Left and Right hands are required in every
accepted frame. Existing mirrored-input handedness correction is unchanged.
Raw full-landmark bounds provide framing checks; raw palm geometry provides
stability checks, so smoothing cannot hide movement during capture.

| Check | Current rule |
| --- | --- |
| Framing | Every detected landmark must fit inside the central 88% of the image (6% margin on each edge) |
| Apparent palm scale | 0.045–0.30 in the existing nonmetric palm-scale units |
| Geometry | Finite coordinates, pinch and palm scale; valid finite palm orientation; nondegenerate neutral references |
| HOME zone | Radius 0.065 in mirrored normalized image coordinates around each captured neutral palm center |
| Position hold | At most 0.015 image units from the initial hold anchor |
| Scale hold | At most 8% relative change from anchor |
| Pinch hold | At most 0.12 palm scales from anchor |
| Orientation hold | Each palm-frame axis remains within Euclidean distance 0.15 of its anchor |
| Hold duration | 0.75 s stable preparation, then visible 3→2→1 for 3 s; at least the existing 30 samples |
| OPEN | Existing thumb/index distance divided by current palm scale is at least 0.65 |
| CLOSED | Same ratio at most 0.22; open minus closed at least max(0.005, 0.35 palm scales) |
| Final quality | Both candidate calibrations valid; finite neutral references; open/closed separation also checked against neutral palm scale |

The most recent 30 validated raw frames go through the existing median sampler.
Samples are bounded in memory. Both hands commit together. Calibration completion
is displayed for 1.5 seconds before the existing five-second LIVE countdown can
start. Both valid/fresh mapped hands must be near HOME throughout that countdown.
Moving outside HOME or losing a hand restarts the five seconds. No instrument
commands reach the task during countdown; paused observations keep session timing
correct if a user intentionally recenters during an existing session.

The ratio thresholds are initial UX heuristics, not scientific cutoffs or a
calibration score. They require real-camera evaluation across users, cameras and
lighting. The guidance **0.8–1.2 m** is only an initial positioning suggestion.
Acceptance uses visible frame margin and apparent scale, never estimated metres.
Lighting and background advice are instructional; image luminance/contrast is
not automatically scored. Existing MediaPipe identity limitations remain.

Public feedback includes HOLD STILL, OPEN MORE, PINCH MORE, MOVE TO HOME,
MOVE CLOSER, MOVE BACK SLIGHTLY, KEEP HANDS INSIDE FRAME and explicit lost-hand
messages. A rejected range displays a retry instruction and cannot complete.

## HOME and tracking loss

HOME is the existing calibrated neutral palm center for each hand. Mirrored
preview circles/crosses are labelled L HOME and R HOME. During setup/recovery,
a green center dot indicates HOME and an arrow plus LEFT/RIGHT/UP/DOWN guidance
shows the direction toward it. During LIVE the references remain subtle; HOME
does not restrict motion or trigger calibration.

Loss preserves calibration and held task state. Invalid/stale hand commands are
never applied; the missing tool holds and the other valid tool can continue.
Reacquisition uses existing stabilizer and controller rate bounds. No additional
recovery timer, snap-to-neutral or automatic pause is introduced. Active task time
continues during tracking loss, preserving the Phase 4 definition. Before LIVE,
loss instead cancels the startup countdown. A real-camera trial must confirm
that reacquisition feels comfortable, even though bounded behavior is tested.

## Pause, recenter, retry and keyboard audit

| Action | Public behavior / remaining input |
| --- | --- |
| Launch | Open scene, run startup script and invoke Start Webcam Control using the existing Blender UI |
| Position/neutral/open/pinch/start | Hands-free once the flow is started |
| Gameplay and temporary tracking recovery | Hands-free, existing pinch interactions |
| Intentional pause/resume | Space in Blender; resume requires both valid hands |
| Window focus loss after LIVE | Existing safety pause remains; Space resumes |
| Recenter | Pause, release all held objects, then Backspace in Blender; rejected otherwise |
| Retry/reset | R in Blender clears task/results and starts a new HOME-gated five-second countdown, preserving calibration |
| Stop | Esc in Blender or Q/Esc in preview; stop and restart if camera process fails |

No pause, recenter or retry gesture was added because it could collide with ring
manipulation. A future deliberate UI/gesture may invoke the guarded recenter hook
only after pausing and confirming that no object is held. Recenter reruns the
neutral/open/closed guide and LIVE gate without resetting the task. Paused
observations continue throughout it, preserving telemetry pause exclusion.

The previous per-hand N/O/C/1/2 preview bindings are no longer exposed in the
public worker, avoiding manual/guided sampler races. `HandStabilizer.calibrate`
remains available for debug code and all prior tests. Backspace provides the
explicit public/debug recalibration fallback. Results stay visible until an
explicit retry or exit; they are not automatically discarded on completion.

## UI and layout

The simulator, task HUD and Phase 4 result summary remain in Blender. Developer
transport/control text has been removed from the public HUD. The mirrored
OpenCV preview starts as a compact 420×640 window; its image is 420 pixels wide,
with wrapping instructions beneath it. It shows landmarks, physical identities,
tracking/calibration state and persistent HOME references. Countdown numerals
are larger than body text. Guidance never covers the camera image.

**Layout limitation:** this phase keeps the existing separate native preview
window rather than docking video into Blender. Arrange Blender at about 75–80%
of the display and the preview beside it at about 20–25% before raising hands.
The OS controls window placement and exact proportions; automatic tiling is not
implemented. Keep the preview outside the trainer area so it cannot cover pegs,
tools, handoff space or results. No camera object, scene/task geometry, collision
shape, renderer or control sensitivity was changed. Small displays may need a
larger preview or a second display for readable guidance.

## Files added and modified

| File | Change |
| --- | --- |
| `src/lapsim_ai/control/public_setup.py` | Added guided calibration state machine, quality checks, HOME and recenter hook |
| `src/lapsim_ai/control/public_runtime.py` | Added public runtime status over existing LIVE gate |
| `src/lapsim_ai/control/webcam_bridge.py` | Added setup metadata and parent-to-preview messages |
| `src/lapsim_ai/vision/stabilization.py` | Added atomic pair capture through existing calibration sampler |
| `src/lapsim_ai/vision/webcam_demo.py` | Connected automatic setup, compact mirrored preview and HOME guidance |
| `blender/scripts/webcam_ui.py` | Connected runtime HUD, automatic start/retry and guarded recenter |
| `tests/test_public_setup.py` | Added 14 pure/stateful regression tests |
| `blender/scripts/verify_phase5.py` | Added synthetic-hand Blender modal integration validation |
| `docs/phase5.md` | Added architecture, rules, results, limitations and exact manual procedure |
| `README.md` | Linked current guided workflow and superseded public N/O/C instructions |

Existing mechanics, mapping, collision, containment, task and telemetry-definition
modules and all prior tests are unchanged. Generated validation reports and the
synthetic preview check live under ignored `outputs/`; no scene file was edited.

## Validation results

- Complete unittest suite: **94 tests PASS** (80 prior tests plus 14 Phase 5 tests).
- Existing `verify_peg_transfer.py`: PASS, 449 controller ticks, complete six-ring
  pickup/lift/handoff/placement trial and reset; 12 grasps, 12 releases, six
  handoffs and six placements, zero drops/incorrect placements.
- Existing peg collision and containment checks pass each trial tick; camera
  framing and deterministic scene fingerprint remain unchanged.
- Existing Phase 4 telemetry/result checks pass, including event totals, timing,
  pause exclusion, paths, JSON/HUD agreement and reset isolation.
- Peg pivot error: **1.5359765386647212e-08 m**, tolerance **1e-06 m**.
- Existing `verify_phase2d.py`: PASS, both sides/all command fields, jaws, loss
  hold, fixed pivots, 20 keyboard bindings and UI registration. Pivot error
  **7.679882693323606e-09 m**.
- Existing `verify_phase3.py`: PASS, grasp/follow/release/reset, visibility and
  previous-scene hashes. Pivot error **8.33000234328132e-09 m**.
- New `verify_phase5.py`: PASS, real Blender modal adapter driven by synthetic
  calibrated hands: setup/countdown task and telemetry isolation, loss restart,
  automatic LIVE, loss/reacquisition, pause, recenter and pause-time exclusion,
  retry/reset and unchanged camera matrix.
- Preview import/render smoke check: PASS with installed OpenCV/MediaPipe and
  synthetic frames. This is not a screenshot of a live webcam trial.
- Some existing headless builders log a sandbox-denied Blender extension-cache
  write and small shutdown memory notices; assertions pass and processes exit 0.

Commands (PowerShell, repository root):

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/verify_peg_transfer.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/verify_phase2d.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/verify_phase3.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/verify_phase5.py
```

## Exact manual hands-free acceptance test — PENDING

1. Restart Blender. Open `blender/scenes/lapsim_ai_peg_transfer.blend`. In the
   Text Editor open `blender/scripts/start_webcam.py` and run Alt+P. Hover the
   simulator viewport, F3 → **LapSim: Start Webcam Control**. Arrange the two
   windows beside each other while hands are down. This is the launch/layout
   preparation boundary. From now until six-ring completion, touch neither
   keyboard nor mouse and do not switch window focus.
2. **Camera:** start roughly 0.8–1.2 m away. Read framing/light/background advice.
   Raise both fully visible hands with movement margin. Move too close, too far,
   put one hand at a frame edge, and hide each hand in turn. Expect useful scale,
   margin and named loss guidance, with no calibration while invalid. A camera
   may hit its frame-margin limit before its scale limit; no metric-distance
   message should be asserted as a measurement.
3. **Neutral:** place both hands comfortably, palms toward the camera. No fixed
   screen HOME points are required yet. Hold still; observe 3→2→1. Move during
   countdown; verify reset. Hold again until both user-specific HOME references
   appear together. Confirm physical left/right labels follow the correct hand.
4. **OPEN:** spread each thumb/index relationship while staying near HOME. Try
   moving during countdown and briefly hiding a hand: both must cancel capture.
   Return, open clearly and hold for the complete 3→2→1.
5. **PINCH:** bring both thumb/index tips together near HOME. Hold a partly open
   posture first; expect PINCH MORE, then close and complete 3→2→1. If a poor
   range can be produced, expect RETRY, never silent acceptance. The normal
   OPEN/CLOSED thresholds intentionally make poor-range capture difficult.
6. **Start:** observe CALIBRATION COMPLETE. Return both hands to HOME. Observe
   the five-second GET READY countdown. Move outside a HOME zone once, then
   hide one hand once: each must restart the full countdown, preserving
   calibration. Return both hands, hold for five uninterrupted seconds and
   verify automatic LIVE without Space. Tools must not move before LIVE.
7. **Play:** steer both tools, insert/retract, roll, grasp and release. For a
   handoff, bring the receiver beside the donor, close the receiver, then open
   the donor. Transfer rings onto matching targets. Move well outside HOME
   during normal task motion: references stay visible but must not constrain
   movement or recalibrate.
8. **Loss:** while playing, hide the left hand briefly. Expect LEFT HAND LOST;
   its tool holds. The other valid hand retains its existing control semantics.
   Return the left hand near HOME: calibration remains, movement resumes at
   bounded rates without a snap. Repeat on the right. Do not treat this as a
   pause test; active task time continues.
9. **Finish:** seat all six rings. Confirm PEG TRANSFER COMPLETE, 6/6 and the
   unchanged Phase 4 time, grasp/drop/handoff/placement and path summary. Leave
   hands idle and verify results persist. Record whether any keyboard/mouse
   input was needed between step 1's preparation boundary and completion.
10. **Separate fallback audit, after acceptance:** R should clear results and
    task history but retain calibration, then automatically countdown from HOME.
    Space pauses/resumes after LIVE. While an object is held, Backspace must be
    refused. Release it, pause, press Backspace and complete the guided recenter;
    verify the task is preserved and recenter time is paused time. Switching
    window focus after LIVE should safety-pause; Space is required to resume.

A successful trial is necessary before describing Phase 5 as validated for a
public demonstration. Remaining limitations are physical comfort/threshold
validation, camera/identity limitations, manual initial window arrangement,
focus-loss pause fallback, and explicit keyboard pause/recenter/retry/stop.
No web application, gesture classifier, AI coaching or clinical claim is added.
