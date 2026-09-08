# Phase 2C mapping (no Blender connection)

Run `.\.venv\Scripts\python.exe src/lapsim_ai/vision/webcam_demo.py` from the
repository root. Select physical Left/Right with 1/2, then capture N/O/C as in
Phase 2B. N now also records median wrist-to-middle-MCP (landmark 9) geometry.
Face the palm toward the camera in a comfortable neutral pose; hold still for
each 30-frame capture. R resets the selected hand; Q/Esc exits.

The mapper emits absolute targets, not the existing keyboard's signed rates.
Motion channels use [-1,1] around neutral; jaw uses [0,1]. `to_control` converts
targets to the existing InstrumentControl pose contract using supplied neutral
poses/limits. No controller is invoked; Phase 2D must integrate this pose path
without passing absolute targets into the keyboard rate update method.

Defaults in MappingSettings:
- yaw = mirrored wrist delta-x / 0.20; pitch = delta-y / 0.20.
- insertion = (1 - current palm length / neutral palm length) / 0.50.
  Moving away from the webcam increases insertion; toward it retracts.
- rotation = negative wrapped palm-angle delta / 60 degrees.
  Clockwise in the mirrored preview is negative rotation.
- jaw = existing calibrated pinch. All outputs are clamped.

Palm geometry is aspect-corrected, stabilized using Phase 2B's filter, and
normalized to each user's neutral sample. A palm shorter than 0.02 image-height
units is rejected. Missing/untracked/invalid calibration emits invalid targets
with no numeric pose; there is no decision about instrument behavior.

Sign convention: image right/down correspond to rig world +X/-Y. The Phase 1
rig has handle at local +Z, tip at -Z; positive yaw sends handle right and tip
left; positive pitch sends handle down and tip up. Use positive image x/y
displacements as positive yaw/pitch, leaving fulcrum inversion to the rig.
This is a world-axis convention, not a promise of exact camera-screen alignment.

Manual checks: neutral gives approximately zero motion channels; translate right/
left for positive/negative yaw, down/up for positive/negative pitch. Keep palm
orientation steady and move closer/farther for negative/positive depth. Rotate
in-plane clockwise/counter-clockwise for negative/positive roll. Pinch/open for
jaw 0/1. Test each hand independently, loss, reacquisition and reset.

Projected palm size is a depth proxy, not measured depth: out-of-plane tilting
also changes scale. Palm deformation, occlusion and landmark jitter can couple
channels. Keep the palm facing the camera and recalibrate after repositioning.
Roll wraps at 180 degrees; use the intended +/-60-degree operating range.
No new models, assets, Blender changes or live integration are included.
