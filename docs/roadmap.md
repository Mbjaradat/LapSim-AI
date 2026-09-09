# Roadmap

These are gates, not delivery promises. Phase 1/2 are manually validated by the
user. Phase 3 is an engineering checkpoint awaiting manual environment/grasp evaluation.

| Phase | Scope | Completion evidence |
| --- | --- | --- |
| 0 | Repository foundation, environment inventory, licensing preparation | Scaffold and documentation reviewed; pending setup/license decisions explicit |
| 1A | Primitive Blender instrument and trocar kinematics proof | Implemented: original primitive scene, two fixed-pivot tools, four bounded controls, deterministic demo and script-based verification; see phase1a.md |
| 1B | Keyboard/manual control and camera usability | Validated live controls, articulated jaws, reset/pause, independent fixed-pivot instruments |
| 2A–2D | Hand tracking, calibration, mapping and live Blender integration | User-validated dual-hand webcam control, palm-based relative depth, fresh-state transport, automatic startup and safe hand loss |
| 3 | Workspace-aware original surgical environment and first grasp foundation | Procedural liver/gallbladder, measured overlap, rigid training beads and automated checks implemented; manual validation PENDING |
| 4 | Future metrics | Not started; scope requires separate authorization, with no competency claims |
| Later | Research into AI skill assessment | Not started; requires reviewed data protocol and validation planning |

## Exact next step

Perform the manual Phase 3 checks in [phase3.md](phase3.md): camera composition,
central reach with both hands, bead pickup/release/reset and webcam responsiveness.
Then consider a separately authorized bounded, anchored gallbladder-retraction
prototype. No retraction physics or Phase 4 metrics are implemented in this checkpoint.

Public licensing remains unresolved. Keep original code/procedural assets and
the existing third-party MediaPipe model records separate before distribution.
