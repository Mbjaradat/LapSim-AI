# Technical method — v0.1.0 Research Preview

This is the inspected implementation as of the 2026-09-11 Phase 6 audit. See the [architecture figure](../README.md#architecture), [reproduction commands](development.md) and [evidence matrix](release_evidence_v0.1.0.md). Numerical engineering verification does not establish clinical realism.

## Source map and runtime boundary

| Stage | Browser (`web/src/`) | Native (`src/lapsim_ai/` unless specified) |
| --- | --- | --- |
| Capture/detection | `app.ts`, `hand-worker.ts` | `vision/webcam_demo.py` |
| Features/orientation | `tracking.ts` | `vision/hand_state.py`, `palm_orientation.py` |
| Filtering/calibration | `tracking.ts`, `setup.ts` | `vision/stabilization.py`, `control/public_setup.py` |
| Freshness/LIVE | `session.ts`, `setup.ts` | `control/webcam_bridge.py`, `webcam_startup.py`, `public_runtime.py` |
| Mapping/controller | `tracking.ts`, `core.ts` | `control/hand_mapping.py`, `controller.py`, `instrument.py`, `settings.py` |
| Transform/constraints | `core.ts`, `renderer.ts`, `grasper.ts` | `simulator/collision.py`, `containment.py`; `blender/scripts/mechanics.py`, `live_rig.py` |
| Task | `task.ts`, `beginner.ts`, `session.ts` | `simulator/tasks/peg_transfer.py`; `blender/scripts/peg_interaction.py` |
| Telemetry | `telemetry.ts` | `telemetry/session.py` |

Browser functions are independent TypeScript ports, not Python imports or streamed Blender. `web/fixtures/native.json` and `web/scripts/generate_fixtures.py` check selected native outputs, not every possible execution. Floating-point thresholds can produce different controller tick counts with equivalent outcomes.

## Input, coordinates and identity

A single ordinary RGB webcam supplies images. Browser capture requests video only (`audio:false`), ideally 640×480, uses actual negotiated dimensions, horizontally mirrors the canvas, and transfers an ImageBitmap to a dedicated worker. MediaPipe Hand Landmarker runs in VIDEO mode with at most two hands, CPU delegation and OffscreenCanvas. The app attempts capture/simulation near 30 Hz, skips duplicate video times and allows one inference in flight. Processed bitmaps are closed. Native uses OpenCV/MediaPipe and sends normalized commands/status over token-checked loopback UDP to Blender, not images.

The control pipeline uses 21 normalized image landmarks, not detector world-landmark outputs. In the mirrored image +x is right and +y is down. With aspect `a=image_width/image_height`, palm geometry uses `p_i=(a*x_i,y_i,a*z_i)`. This z is wrist-relative landmark depth, not whole-hand camera distance. The browser rejects unknown labels, non-21-point arrays and any nonfinite xyz. Native extraction supports some incomplete legacy geometry, but the public mapper requires finite, nondegenerate scale, orientation, center and calibration.

Both implementations swap detector Left/Right labels in their mirrored-input path to route physical hands to LEFT/RIGHT instruments; they do not infer identity from screen position. Duplicate labels invalidate the affected hand. This is an implemented/tested convention, not a guarantee under occlusion/crossing: check physical labels during setup.

Scene lengths are metres; controller angles are degrees; twist is radians; time is monotonic seconds. Image features and normalized commands are dimensionless. No stereo camera, depth sensor, wearable controller or physical instrument is required.

## Feature extraction

Clamp selected x/y to [0,1] for steering and pinch. Palm steering is:

```text
center = .40*xy(0) + .15*(xy(5)+xy(9)+xy(13)+xy(17))
```

Landmark 0 is wrist and 5/9/13/17 are the four MCP knuckles. Excluding thumb/fingertips avoids directly steering from jaw articulation and distributes wrist noise. It does not eliminate physiological or tracking coupling.

Scale uses unclamped aspect-corrected xyz palm points:

```text
pairs = [(0,5),(0,9),(0,13),(0,17),(5,17),(5,13),(9,17)]
scale = median(norm(p_i-p_j) for (i,j) in pairs)
```

Seven palm distances reduce dependence on one pair; relative z contributes a foreshortening-related proxy. HOME stores `s0`; a degenerate reference cannot map commands. No fingertip pair contributes to scale.

Orientation uses `k=[p5,p9,p13,p17]`:

```text
long = unit(mean(k)-p0)
t_raw = (-1.5*k0-.5*k1+.5*k2+1.5*k3)/5
trans = unit(t_raw-long*dot(long,t_raw))
```

Norms ≤1e-6 are rejected. HOME's frame is orthonormalized from coordinatewise medians of sample axes. Twist removes shortest-arc swing from neutral longitudinal axis `a` to current `b`, with neutral/current transverse axes `t0,t1`:

```text
c = clamp(dot(a,b),-1,1)
if c < -.95: invalid twist
v = cross(a,b)
reference = t0+cross(v,t0)+cross(v,cross(v,t0))/(1+c)
theta = atan2(dot(b,cross(reference,t1)),dot(reference,t1))
```

Nearly reversed axes are ambiguous and rejected; no image-angle fallback exists. This is a palm-frame twist proxy, not a measured biomechanical wrist angle.

Pinch `d=norm(xy(8)-xy(4))` is index-tip to thumb-tip distance in clamped normalized 2D axes. It is intentionally not aspect-corrected in the implementation. OPEN/CLOSED calibration normalizes the user's span; this is not metric finger distance.

## Guided calibration

Browser `GuidedSetup` and native `public_setup.py` progress through HOME → OPEN → PINCH → CALIBRATION_COMPLETE → WAITING_FOR_LIVE → LIVE_COUNTDOWN → LIVE. Each accepted frame needs both uniquely identified hands. Quality checks use raw geometry, so filtering cannot conceal hold motion.

| Check | Current rule |
| --- | --- |
| Framing | All landmark x/y in [.06,.94] |
| Scale | .045 ≤ scale ≤ .30 |
| HOME return | Center within radius .065 of per-hand HOME |
| Hold position drift | ≤ .015 from initial anchor |
| Hold relative scale change | ≤ .08 |
| Hold pinch change / anchor scale | ≤ .12 |
| Hold orientation drift | Each axis Euclidean distance ≤ .15 |
| OPEN | d/scale ≥ .65; both near HOME |
| PINCH | d/scale ≤ .22; OPEN−d ≥ max(.005,.35*scale); both near HOME |
| Stable hold | .75 s preparation + 3 s countdown |
| Samples | At least 30; latest 30 raw samples aggregated by median |
| Captured range | OPEN−CLOSED ≥ max(.005,.35*s0) |
| Stall | Frame gap > .5 s restarts hold |

Browser sample storage is bounded at 120 frames. Missing hands, invalid pose, movement, bad framing/scale or inadequate range reset the hold and display guidance. Both candidates commit together. HOME captures neutral values/orientation; OPEN/PINCH capture pinch medians. Native uses a private candidate stabilizer; browser uses candidate calibration records. Both retain live feature history and reset twist history on neutral capture.

Completion is displayed for 1.5 seconds, followed by five uninterrupted seconds with both fresh valid mapped hands near HOME. Departure, loss or a gate gap >.5 seconds restarts the LIVE countdown. Task motion is blocked during setup/countdown and on the entry tick. Returning HOME during LIVE never recalibrates. Explicit recalibration requires pause and no held object, preserves task, and repeats all stages. Retry clears task/telemetry and reruns LIVE while retaining calibration. New camera sessions start fresh.

Calibration reduces dependence on hand size, camera framing, resting pose and pinch range within accepted geometry; it does not eliminate them. The displayed 0.8–1.2 m advice is not a measured camera distance. Thresholds are engineering heuristics, not scientifically validated quality criteria.

## Temporal filtering and bounded updates

Each hand has independent state. First valid values initialize history. Use `dt=1/30` initially, otherwise `min(elapsed,1/15)`, and `alpha=1-exp(-dt/tau)`:

```text
filtered = old_filtered+alpha*(raw-old_filtered)
delta = filtered-old_output
output = old_output+sign(delta)*min(step,max(0,abs(delta)-deadband))
```

| Feature | tau seconds | Output deadband | Maximum step per observation |
| --- | --- | --- | --- |
| Center/ordinary components | .06 | .002 | .03 |
| Scale | .10 | .005*s0 | .03*s0 |
| Calibrated pinch | .04 | .005*(OPEN−CLOSED) | .35*(OPEN−CLOSED) |

Precalibration scale uses prior output scale as baseline. Precalibration pinch uses ordinary output deadband/step but .04 s EMA. Twist uses wrapped .06 s EMA: `angle=wrap(old+alpha*wrap(theta-old))`, in [-pi,pi). Missing twist yields no mapped target but retains history. Twist has no separate feature step cap; downstream roll rate is bounded. Timestamps must increase.

## Normalized channels and monocular insertion

Define `R(delta,range,dead)=sign(delta)*clamp(max(0,abs(delta)-dead)/(range-dead),0,1)`. With stabilized center `c`, scale `s`, twist `theta`, pinch `d` and HOME values `c0,s0`:

| Channel | Actual mapping |
| --- | --- |
| yaw | R(c.x−c0.x,.08,.003) |
| pitch | R(c.y−c0.y,.08,.003) |
| insertion | R(1−s/s0,.15,.02) |
| rotation | R(−theta,35*pi/180,2*pi/180) |
| jaw | clamp((d−CLOSED)/(OPEN−CLOSED),0,1) |

**THIS IS CALIBRATION-RELATIVE MONOCULAR CONTROL.** Smaller apparent palm scale increases insertion; larger scale retracts. The command has a 2% relative deadband and saturates at ±15% scale change, after feature filtering/bounding. It is not a direct metric measurement of physical hand depth from the camera and performs no metric depth reconstruction. Scene metre units and wrist-relative landmark z do not change that fact.

## Laparoscopic mapping and trocar transform

For signed commands `u`, map around neutral `n` as `q=n+u*(high-n)` if `u>=0`, otherwise `q=n+u*(n-low)`. Jaw maps directly to [0,1]. Invalid targets hold the corresponding tool.

| DOF | Limits | LEFT / RIGHT neutral | Webcam rate |
| --- | --- | --- | --- |
| Yaw | −35° to +35° | −18° / +18° | 22°/s |
| Pitch | −25° to +25° | 12° / 12° | 22°/s |
| Insertion | .12–.28 m | .20 / .20 m | .035 m/s |
| Roll | −180° to +180° | 0° / 0° | 90°/s |
| Jaw | 0–1 | .5 / .5 | 8/s |

Approach each target by at most `rate*min(dt,.05)` and clamp poses again after constraints. Native keyboard rate commands are separate: jaw 1.5/s, Fine/Normal/Fast multipliers .35/1/2. Browser uses fixed webcam rates with no native keyboard/profile UI.

Pivots: `T_LEFT=(-.085,0,.12)`, `T_RIGHT=(.085,0,.12)` metres. For column vectors `R=Ry(yaw)*Rx(pitch)*Rz(roll)` (roll, then pitch, then yaw):

```text
tip = T+R*(0,0,-insertion)
shaft_line(lambda) = T+lambda*R*(0,0,-1)
```

The fixed pivot lies on this line for every pose. The external handle lies toward local +Z: positive yaw moves handle +X/tip −X, positive pitch handle −Y/tip +Y. Roll rotates about the shaft without moving the pivot/shaft axis.

Jaw half-angle is `30°*jaw`; hinges are `tip+R*(±.0015,0,0)`; endpoints add `R*(±.018*sin(half_angle),0,-.018*cos(half_angle))`. Contact is `tip+R*(0,0,-.0126*cos(half_angle))`. Rendered tools and collision proxies use the same pose contract. Telemetry tracks shaft tips, not jaw contacts.

Numerical reconstructed-pivot accuracy verifies transforms; it does not establish forces, physical realism, clinical fidelity or transfer to surgery.

## Collision and workspace stage

Constraints run after rate-limited proposals, before task/telemetry. Browser `Collision` uses shaft radius .003 m, jaw capsule radius .0025 m, board plane and opposing capsule distance checks. Board top is z=−.112 m, clearance .0001 m. Workspace planes bound x to ±.053 m, y to [−.001,.085] m, floor −.112 m, ceiling neutral tip +.036 m. Camera-frustum planes derive from a 48 mm lens/36 mm sensor, 4:3 view and .92 inset. Containment uses the distal .018 m shaft segment plus jaws, not the entire shaft. Held-ring support includes radius .0071 m and vertical half-size .0016 m with its retained contact offset.

The resolver estimates travel, divides by .00075 m, and processes at most 64 substeps in fixed LEFT/RIGHT and jaw/rotation/yaw/pitch/insertion order. Candidates project insertion into board/workspace bounds. Invalid candidates are restricted with nine bisection iterations or held. Pair, board and workspace checks use numerical tolerances. Large proposals need not reach their target in one update. Native modules use corresponding capsule/plane and bounded sweep logic with explicit configuration classes. See [containment documentation](workspace_containment.md).

This is deterministic geometric constraint resolution, not full rigid-body physics, friction, tissue deformation, force simulation or haptics. Ring capture/settling is separate.

## Task interaction and Beginner Free Transfer

Structured states: READY/RUNNING/COMPLETE. Six source seats have x=−.033/−.014, y=.020/.042/.064, z=−.110 m; targets mirror x. Capture requires a close edge to jaw ≤.25 from >.25, contact within .009 m, one ring per tool and one owner per ring. Distance/name/side sorting makes competition deterministic. The contact-to-ring offset is retained. Jaw ≥.65 releases. A receiver can prepare a handoff while donor holds; transfer requires donor release while receiver remains closed, nearby and unoccupied.

Placement requires horizontal distance ≤.006 m, vertical difference ≤.012 m and no unheld ring within .006 m of the seat. Candidates sort by distance/kind/peg name. Structured matching targets are CORRECT, other targets INCORRECT, source seats SOURCE. Otherwise a fixed-offset search settles the ring clear of seats/rings at z=−.110 m as DROPPED. This is not a gravitational rigid-body trajectory. Structured completion is six currently correct rings; handoff is supported but not required by task logic.

`BeginnerTransfer` counts either target classification as a successful transfer and replaces six-ring completion with 120 active seconds. Either hand, any ring, any valid target; no matching/handoff requirement. Source returns and drops do not count. Confirmation lasts 1.2 active simulation seconds; task dt is capped at .05 per tick. Recycling waits until tool contacts are at least .018 m from the placed ring and a lexically selected source is more than .016 m from other current/predicted ring positions and more than .018 m from tool contacts. Regrasp cancels recycling. Delay may exceed 1.2 wall-clock seconds during obstruction or low frame rate. Retry clears rings, ownership, count, handoffs and recycling.

Public app construction is `Session('beginner')`; `Session()` defaults to structured internally. Beginner Free Transfer is an experimental LapSim-AI practice task, not official FLS or a validated competence/proficiency/training-effectiveness assessment.

## Telemetry

Telemetry starts when task first becomes RUNNING (successful grasp). Browser `started=clock-dt` includes that observation tick's full dt, not an interpolated grasp timestamp. Setup, countdown and idle READY time are excluded. Browser expiry clips final dt to exactly 120 active seconds and freezes task, poses and cloned result. Native structured completion is task-driven with no beginner timer.

Explicit pause and pre-LIVE gates exclude elapsed intervals; hidden tabs set pause. **Tracking loss is not a pause**: invalid/stale targets hold, the other hand may move, and time continues. Target freshness is at most .5 s. Resume requires fresh valid targets for both hands. Explicit pauses reanchor paths; tracking loss alone does not reanchor. Bounded tracking reacquisition retains calibration/filter history without a snap to neutral or another LIVE gate.

Paths sum accepted shaft-tip displacement once distance from each last path anchor reaches ≥.0005 m. Subthreshold motion accumulates relative to that anchor. Unchanged constrained poses add no path. Total is left+right virtual metres, not physical hand travel or an exact continuous arc integral.

| Metric | Definition |
| --- | --- |
| active_seconds / paused_seconds | Monotonic observation time with explicit pause exclusion |
| objects_completed | Structured current correct objects; beginner cumulative transfers |
| successful_transfers | Added to normal timed beginner result |
| grasps / releases | Ownership transitions; each handoff contributes one of each |
| handoffs | Direct donor-to-receiver ownership transition |
| drops / incorrect_placements / successful_placements | Classification on release; beginner valid targets count successful |
| path_metres LEFT / RIGHT / TOTAL | Thresholded accepted shaft-tip paths |
| events / tip_samples / pause_intervals | Bounded histories with truncation flags |

Browser caps: 4096 events, 600 tip samples, 1024 pause intervals, dropping oldest when full. Tip samples occur at most every .1 s of observation clock. Ownership changes are observed at telemetry boundaries, not an exhaustive physics event log. Finish freezes a cloned snapshot; reset clears history. Native results serialize into Blender scene properties and could persist in a user-saved scene. Browser data remains in memory with no automatic upload/export. No composite skill score is implemented.

Known internal metadata limitation: explicit Stop Camera calls generic `Telemetry.finish()` directly. A prematurely stopped beginner result may retain generic `task:'peg_transfer'` / `objects_total:6` fields internally; the visible UI uses beginner mode. Normal timed completion relabels them. This does not affect the documented timed workflow, and Phase 6 does not change telemetry semantics. Consumers of internal results must check outcome and mode.

## Differences, assumptions and reproducibility

Native uses a Windows `.venv` worker, OpenCV preview, loopback transport and Blender modal UI; browser uses worker messages and an integrated Three.js page. Native offers additional typed protocol validation, keyboard controls, sensitivity profiles and historical scenes. Browser validates full landmark arrays earlier and adds beginner recycling, page controls and hidden-tab pause. The shared feature/calibration/mapping concepts and fixture checks are not a shared compiled runtime.

Follow [development setup](development.md), then regenerate fixtures with `web/scripts/generate_fixtures.py` and inspect their diff when changing native/port behavior. Camera/hardware acceptance remains manual. Dependencies are pinned for a recorded Windows environment, not asserted universal compatibility.

Lighting, occlusion, hand identity, framing, hand pose and calibration affect tracking. Scale and orientation remain nonmetric proxies. No haptics or tissue/full rigid-body physics exists. Procedural visuals and simplified interaction limit realism. Physical device/browser coverage is limited. Clinical, construct and predictive validity and training effectiveness are not established. Controlled usability/performance studies and future advanced tasks are planned directions, not validated capabilities. Novelty and patentability have not been determined.
