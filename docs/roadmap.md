# Roadmap

These are proposed gates, not implemented features or delivery promises.

| Phase | Scope | Completion evidence |
| --- | --- | --- |
| 0 | Repository foundation, environment inventory, licensing preparation | Scaffold and documentation reviewed; pending setup/license decisions explicit |
| 1 | Primitive Blender instrument and trocar kinematics proof | Original primitive scene; two tools with fixed pivots, bounded insertion, deterministic scripted controls; repeatable checks and launch instructions |
| 2 | Webcam hand tracking and calibration | Two-hand identity and confidence handling; loss/recovery behavior; measured latency; no recording by default |
| 3 | Connect hand controls to constrained instruments | Defined coordinate/schema contract; stable control and explicit stale-input behavior |
| 4 | Simplified cholecystectomy educational environment | Original or license-reviewed anatomy; clearly documented interaction and fidelity limits |
| 5 | Telemetry and descriptive metrics | Reproducible event schema, metrics and tests; no competency claims |
| 6 | Research into AI skill assessment | Reviewed data protocol, suitable labels and baselines, held-out evaluation and validation plan |

## Exact next step

After maintainer approval to begin Phase 1, specify and implement a primitive-only Blender kinematics demonstration: two cylinder instruments through two fixed trocar points, driven by deterministic scripted inputs. Define axes, units, insertion limits, and a numerical pivot-error tolerance first. Verify each shaft continues through its pivot and insertion remains bounded. No anatomy, webcam, downloaded assets, or scoring is needed for this milestone.

Resolve the Blender-script licensing decision before adding distributable integration code. Select a compatible standalone Python version when external CV dependencies are evaluated; do not install heavy frameworks preemptively.
