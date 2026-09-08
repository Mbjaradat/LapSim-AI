# Phase 2B: calibration and stabilization

From the repository root run:

```powershell
.\.venv\Scripts\python.exe src/lapsim_ai/vision/webcam_demo.py
```

Select physical Left with **1**, Right with **2** (Right initially selected).
Hold your comfortable neutral wrist pose, press **N**, and remain still until
sampling finishes. Hold thumb/index comfortably open and press **O**; hold
them pinched closed and press **C**. Each capture uses 30 consecutive detected
frames and their median. Repeat for the other hand. A dropped detection restarts
the current capture. An inverted or too-small pinch range is rejected; recapture
O/C with distinct poses. **R** clears the selected hand's filters and calibration;
**Q/Esc** exits. Calibration is session-only.

The mirrored preview retains the manually verified physical handedness correction.
Raw landmarks remain visible; debug numbers are stabilized. Check each physical
hand alone, both together, steady and small deliberate movements, open/closed
pinch near 1/0, loss longer than 0.5 seconds, gradual reacquisition, and independent
reset. Hold each pose before starting its capture. Recalibrate after changing
camera distance significantly: this image-space calibration accommodates the
current user's hand size/distance but is not distance invariant.

`vision/stabilization.py` uses only the standard library. `HandStabilizer.update`
accepts raw HandStates and strictly increasing monotonic seconds once per frame,
and returns separate frozen Left/Right outputs. Settings centralize a 60 ms EMA,
0.002 normalized continuous deadband, 0.03 maximum component change per update,
0.10 maximum calibrated pinch change per update, 0.5 second availability timeout,
sample count and minimum accepted pinch span.
EMA time steps are capped at 1/15 second to avoid jumps after stalls. The deadband
allows accumulated deliberate movement. Filtering adds modest latency; these
defaults require subjective webcam validation and are not clinically validated.

`tracked` means detected this frame; `available` includes the short loss grace
period; `valid` requires current detection, complete calibration and no capture
in progress. Missing hands retain their last numeric values, with `valid=False`
immediately. Before first detection, coordinates are None; before calibration,
normalized pinch is None. Duplicate identities/nonfinite samples count as missing.
Calibration survives loss; reacquisition resumes the bounded filter. MediaPipe
identity errors remain possible; no identity persistence or instrument behavior
is added. Normalized pinch is clamped to [0, 1].

Pipeline: raw HandState → smoothing/deadband → per-hand calibration →
StableHandState. Blender connections and Phase 2C mapping are not implemented.
