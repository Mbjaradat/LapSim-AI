# LapSim-AI

An experimental educational and research prototype for webcam-controlled laparoscopic simulation, planned for public open-source release.

**Browser MVP:** the additive [web application](web/README.md) now runs the trainer,
camera, guided calibration, Peg Transfer and results on one page without a native
runtime. See the [implementation report, local commands and manual webcam test](docs/web-mvp.md).
Automated web/native checks pass; physical browser webcam validation remains pending.
The native Blender implementation below is preserved as the reference.

The primary MVP is a **peg-transfer box trainer**. A laptop webcam tracks both hands and controls two virtual instruments in Blender through software-enforced trocar/fulcrum constraints. Previous cholecystectomy/anatomy work remains a reference checkpoint.

**Status: Peg-transfer MVP implemented — awaiting manual evaluation.** Six rings,
matching pegs, deterministic grasp/handoff/placement, reset, and READY/RUNNING/
COMPLETE states reuse the existing mechanics and dual-hand webcam controls.
No scoring, AI feedback, anatomy rebuild or public-release packaging is included.

Open `blender/scenes/lapsim_ai_peg_transfer.blend` and follow [Peg transfer build/manual testing](docs/peg_transfer.md).
For the current webcam flow, use [Phase 5 guided setup and hands-free acceptance](docs/phase5.md):
both-hand neutral/open/pinch holds now calibrate automatically, followed by the
existing five-second LIVE countdown. HOME references persist during play.
Physical hands-free acceptance is pending; earlier N/O/C setup instructions are
superseded for this public worker.
The earlier `lapsim_ai_phase3.blend` engineering scene remains preserved.
Phase 1A/1B scene files remain preserved. See [Phase 1A mechanics](docs/phase1a.md)
and [Phase 2D webcam workflow](docs/phase2d.md) for their separate instructions.

This project has no clinical validation, does not certify surgical competency, and does not replace supervised surgical training. Future metrics will describe simulator behavior; their relationship to surgical skill requires research and validation.

## Goals

- Build a functional technical prototype.
- Prepare a lightweight, reproducible public open-source project.
- Document AI-assisted development using Codex/Astra with human review.
- Explore future automated laparoscopic skill assessment as a research direction.

## Intended pipeline

Laptop Webcam → Hand Tracking → Control Mapping → Laparoscopic/Trocar Constraints → Blender Simulation → Interaction/Telemetry → Performance Metrics → Future AI Skill Assessment

See [architecture](docs/architecture.md), [roadmap](docs/roadmap.md), and [development setup](docs/development.md).

## Repository layout

| Path | Purpose |
| --- | --- |
| `blender/scenes/` | Distributable Blender scene files |
| `blender/scripts/` | Scene builder, instrument rigs, demonstration, verification |
| `src/lapsim_ai/vision/` | Webcam tracking and per-hand calibration/stabilization |
| `src/lapsim_ai/control/` | Bounded controller, keyboard/webcam inputs, mapping, bridge and startup gate |
| `src/lapsim_ai/simulator/` | Pure workspace characterization and rigid-token grasp logic |
| `src/lapsim_ai/telemetry/` | Future interaction event contracts |
| `src/lapsim_ai/scoring/` | Future descriptive performance metrics |
| `assets/` | Original assets and separately documented third-party assets |
| `tests/` | Control contract tests; Blender integration checks live in `blender/scripts/` |
| `docs/` | Architecture, roadmap, setup, licensing decisions |

## Dependencies and setup

The working Phase 2 setup uses the existing standalone Python 3.12 virtual
environment with MediaPipe/OpenCV and the separately recorded official hand model.
Blender uses its own Python. Phase 3 adds no dependencies, model downloads or
external geometry; its workspace/grasp logic uses the standard library.
Packaging and public-release license metadata remain provisional.

## Licensing and contributions

Apache License 2.0 is proposed for original independent source code, **pending maintainer approval**. No root LICENSE has been finalized; this README is not a license grant. Blender integration requires a separate GPL compatibility review before distribution. See [licensing decisions](docs/licensing.md).

Third-party materials retain their own terms, recorded in
[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md). The existing MediaPipe model
is separate from the original procedural Phase 3 geometry.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution and provenance expectations.
