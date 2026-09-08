# Phase 2D: live webcam integration

1. Close any standalone webcam demo. Open `blender/scenes/lapsim_ai_phase1b.blend`.
2. In Blender's Text Editor, Open `blender/scripts/start_webcam.py`, then Run Script
   (Alt+P). In a 3D Viewport press F3 and select **LapSim: Start Webcam Control**.
   Stop existing keyboard mode with Esc first. No scene regeneration is needed.
3. The separate webcam preview opens. Blender starts at neutral and PAUSED.
   Focus the preview; select physical Left with **1**, Right with **2**. Hold your
   neutral palm-forward pose at a comfortable middle distance, press **N**,
   and hold for 30 detected frames. Capture
   **O** with pinch open and **C** with pinch closed. Repeat for the other hand.
   Status must show ready and valid commands for both hands.
4. Once both hands are ready, visible and valid, Blender automatically counts
   down **5, 4, 3, 2, 1**, then enters **LIVE**. No initial Space press or focus
   change is required. Instruments remain stationary throughout the countdown.
   Losing either hand or fresh data cancels it; reacquisition starts a full five
   seconds again. The HUD shows WAITING FOR CALIBRATION, WAITING FOR BOTH HANDS,
   BOTH HANDS READY — STARTING IN ..., LIVE, or PAUSED.
   After initial LIVE, **Space** pauses/resumes (resume still requires both valid
   hands). Manual pause never auto-resumes. Switching away from Blender after
   initial LIVE retains the existing focus-loss pause. Stop/restart webcam mode
   to enable automatic startup again.
5. Test each physical hand independently: Right routes only to RIGHT, Left only
   to LEFT. Mirrored right/left displacement gives positive/negative yaw;
   down/up gives positive/negative pitch. The existing fixed-trocar rig supplies
   opposite internal-tip movement. Move the whole hand farther for insertion,
   closer for retraction; start with small movements. Clockwise/counter-clockwise
   tilting of the knuckle line in the preview gives negative/positive roll.
   Pinched/open fingers close/open the corresponding jaw.
6. Hide one hand: that instrument holds while the other remains controllable.
   Reacquisition approaches the new target at bounded speed. Verify trocar
   positions remain fixed, and test Space pause/resume.
7. **R in Blender** restores both instruments to neutral and pauses. Calibration
   remains in the worker. For recalibration, focus preview (Blender pauses), use
   **R there** to clear the selected hand, then N/O/C. Return to Blender and Space.
8. **Esc in Blender** stops the worker and releases
   ownership. The preview normally closes promptly; a stuck worker is killed
   after 1.5 seconds. Wait for it to close before restarting. Q/Esc in the preview
   also exits the worker; Blender then holds until you stop its mode with Esc.
   Keyboard mode remains available through F3 **LapSim: Start Keyboard Control**.

Architecture: Blender starts the repository `.venv/Scripts/python.exe` with the
existing demo, MediaPipe model and Phase 2A/B/C pipeline. A separate process runs
inference/preview, capped at 30 FPS; no third-party packages are needed inside
Blender. Token-tagged JSON absolute targets travel over a loopback-only UDP socket
with an automatically assigned port. Blender drains a bounded number of packets
on a main-thread 30 Hz modal timer; no worker touches bpy. Packets older than
0.5 seconds, out of order, malformed, nonfinite, or invalid are not applied.

`InstrumentController.update_targets` converts through the existing target-to-
InstrumentControl contract and approaches poses using existing channel speed
limits. Keyboard rate updates remain separate, sharing the controller/rig and
exclusive mode lock. No fulcrum or driver formulas change. Missing hands hold
immediately on an invalid packet; interrupted transport holds after 0.5 seconds.
The worker detects parent pipe closure and releases camera/window resources;
nonblocking shutdown has a forced-exit fallback for blocked camera reads.

Ergonomic defaults: full yaw/pitch at 0.08 normalized wrist displacement (previously
0.20), with a 0.003 neutral dead zone. Depth now uses the median 3D image-space
length of seven palm pairs: 0–5, 0–9, 0–13, 0–17, 5–17, 5–13, 9–17. X and Z are
aspect-corrected to the Y scale. Apparent palm size supplies the range signal;
relative Z compensates foreshortening rather than directly measuring hand travel.
[MediaPipe documents Z as wrist-relative](https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/hands.md),
so a common Z offset cannot indicate camera distance. No fingertips or finger
joints contribute. The existing 30-frame N capture records median neutral scale.
Depth delta is `1 - current_scale / neutral_scale`: smaller/farther inserts,
larger/closer retracts. Full output is at +/-15% scale change, with a +/-2%
mapping deadband and clamping to [-1,1]. Depth-only filtering uses a 100 ms EMA,
0.5% neutral-scale deadband, and 3% neutral-scale maximum change per frame.
This is a relative monocular hybrid proxy, NOT metric or true physical depth.
Roll uses the index-to-pinky knuckle line (5–17) and reaches full
command at 25 degrees (previously 60). Settings live in control/hand_mapping.py.

Jaw filtering uses a 40 ms EMA and 0.005 calibrated deadband, a 0.35 normalized
per-frame cap, and an 8 units/second webcam-only controller rate. Previously the
60 ms filter, 0.10 cap and 1.5 units/second controller added noticeable response
delay. Wrist filtering and keyboard rates remain unchanged. Filter settings are
in vision/stabilization.py; webcam jaw rate is in control/settings.py.

After this tuning, restart Blender once to clear cached Python modules, restart
webcam mode, and recalibrate both hands. Move each whole hand a little toward/
away from the camera, returning to neutral between trials. Check depth remains
near neutral while pinching, curling the middle finger, translating X/Y and
moderately tilting the palm without changing distance. Finally combine
controls and test each hand's loss/reacquisition independently.

Known limits: inferred landmark Z, palm deformation and occlusion can affect
the depth proxy. Real perspective/tilt errors may remain; sensitivity does not
correspond to a universal travel distance in centimetres. Knuckle roll is
2D tilt, not forearm pronation, and an edge-on palm is unreliable. Synthetic
geometry checks do not establish real-camera tilt invariance. Calibration is session-only;
vision frame rate/latency depend on this laptop. Window focus matters for keys.
Camera/driver hangs may require the forced shutdown fallback. If startup exits,
run the standalone demo from a terminal to see its error:
`.\.venv\Scripts\python.exe src/lapsim_ai/vision/webcam_demo.py`.
This is an educational engineering prototype, with manual end-to-end validation
still required. No anatomy, scoring, telemetry or new assets are included.

Pure checks: `.\.venv\Scripts\python.exe -B -m unittest discover -s tests`.
Optional small headless rig check: Blender `--background --python-exit-code 1
--python blender/scripts/verify_phase2d.py`. This does not save or rebuild scenes.
