# LapSim-AI

An experimental educational and research prototype for webcam-controlled laparoscopic simulation, planned for public open-source release.

The intended first scenario is a simplified laparoscopic cholecystectomy environment. Eventually, a laptop webcam will track both hands and control two virtual instruments in Blender through software-enforced trocar/fulcrum constraints.

**Status: Phase 1A — rigid instrument mechanics prototype.** A reproducible Blender training box contains two independently controlled instruments, fixed trocar pivots, and a deterministic demonstration. Anatomy, hand tracking, tissue interaction, and performance assessment are not implemented.

Open `blender/scenes/lapsim_ai_phase1a.blend` and press **Numpad 0** for the camera view, then **Space** to play. See [Phase 1A mechanics and verification](docs/phase1a.md) for regeneration commands, manual controls, and limitations.

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
| `src/lapsim_ai/vision/` | Future webcam and hand tracking |
| `src/lapsim_ai/control/` | Bounded instrument-control contract; future calibration/mapping |
| `src/lapsim_ai/simulator/` | Future constraints and simulator logic |
| `src/lapsim_ai/telemetry/` | Future interaction event contracts |
| `src/lapsim_ai/scoring/` | Future descriptive performance metrics |
| `assets/` | Original assets and separately documented third-party assets |
| `tests/` | Control contract tests; Blender integration checks live in `blender/scripts/` |
| `docs/` | Architecture, roadmap, setup, licensing decisions |

## Dependencies and setup

Phase 1A has no third-party Python dependencies beyond the existing Blender runtime. `pyproject.toml` records provisional metadata; packaging and license metadata will be finalized later. No ML frameworks or assets are installed. See the development guide before creating a standalone Python environment. Blender uses its own bundled Python.

## Licensing and contributions

Apache License 2.0 is proposed for original independent source code, **pending maintainer approval**. No root LICENSE has been finalized; this README is not a license grant. Blender integration requires a separate GPL compatibility review before distribution. See [licensing decisions](docs/licensing.md).

Third-party code, models, textures, datasets, and other materials retain their own terms and must be recorded in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md). No third-party assets are included.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution and provenance expectations.
