# Roadmap

These are gates, not delivery promises. Phase 1A implements the primitive instrument mechanics milestone; later phases remain proposed.

| Phase | Scope | Completion evidence |
| --- | --- | --- |
| 0 | Repository foundation, environment inventory, licensing preparation | Scaffold and documentation reviewed; pending setup/license decisions explicit |
| 1A | Primitive Blender instrument and trocar kinematics proof | Implemented: original primitive scene, two fixed-pivot tools, four bounded controls, deterministic demo and script-based verification; see phase1a.md |
| 1B | Proposed keyboard/manual control and camera usability pass | Live controls without animation interference, reset/pause behavior, documented sensitivity and usability checks; no webcam or anatomy |
| 2 | Webcam hand tracking and calibration | Two-hand identity and confidence handling; loss/recovery behavior; measured latency; no recording by default |
| 3 | Connect hand controls to constrained instruments | Defined coordinate/schema contract; stable control and explicit stale-input behavior |
| 4 | Simplified cholecystectomy educational environment | Original or license-reviewed anatomy; clearly documented interaction and fidelity limits |
| 5 | Telemetry and descriptive metrics | Reproducible event schema, metrics and tests; no competency claims |
| 6 | Research into AI skill assessment | Reviewed data protocol, suitable labels and baselines, held-out evaluation and validation plan |

## Exact next step

After review of Phase 1A and explicit authorization, begin Phase 1B: add simple keyboard/manual controls to the same primitive rig, with reset/pause and sensitivity settings. Resolve animation-versus-manual ownership explicitly. Retain fixed-pivot and limit checks. Do not introduce anatomy, webcam input, downloaded assets, or scoring in that usability milestone.

The user authorized local Phase 1A implementation; public licensing remains unresolved. Resolve the Blender-script licensing decision before distribution. Select a compatible standalone Python version when external CV dependencies are evaluated; do not install heavy frameworks preemptively.
