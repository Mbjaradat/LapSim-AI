# v0.1.0 distribution inventories

Review date: 2026-09-12. These are separate distribution scopes. A GitHub source archive follows tracked repository content; the minimal artifact must be assembled from its include list. Never package the working directory with ignored outputs, dependencies, caches, credentials or recordings.

## A. PUBLIC GITHUB SOURCE REPOSITORY

| Decision | Material | Reason / required treatment |
| --- | --- | --- |
| INCLUDE | `src/`, `tests/`, `web/src/`, `web/tests/`, fixtures, scripts, manifests and lockfile | Original Apache-2.0 source and reproducibility material; dependencies keep their terms |
| INCLUDE | `blender/scripts/`, independent configuration and five tracked `.blend` scenes | Native reference is distributable under `licensing.md`; Phase 3B retains SPL terms |
| INCLUDE | Original procedural assets and `assets/original/` provenance | Maintainer-owned Apache-2.0 components; Phase 3B inherited parts are separated |
| INCLUDE | MediaPipe model provenance/license and Tasks Vision provenance/static notices | Required runtime and exact notice record |
| INCLUDE | Ten SPL VTKs, full `LICENSE.txt`/`SOURCE.json`, and derived Phase 3B scene | Public redistribution permitted with recorded preface, full terms, attribution and modification statement |
| INCLUDE | Root LICENSE/NOTICE/AUTHORS/CITATION/register and `docs/` | Legal, scientific and reproducibility record; publish only sanitized evidence |
| INCLUDE | `requirements-native.txt`, `pyproject.toml`, Vite/Vercel configuration | Installation/deployment metadata; does not bundle Python/Blender |
| EXCLUDE | `forcing-vs-convincing/` | Confirmed unrelated and removed in Phase 6.3 |
| EXCLUDE | `outputs/`, `.venv/`, node_modules, caches, downloads, recordings, local env/secrets, Blender backups/temp files | Ignored/generated/private material |
| EXCLUDE | `web/dist/` and generated `web/public/{wasm,models}/` from source archive | Generated build products; create separately from reviewed source |
| REVIEW REQUIRED | None for distribution licensing | Manual content/history/privacy/form checks remain before publication |

Keeping SPL material public requires the full adjacent license, exact preface and attribution in `THIRD_PARTY_LICENSES.md`, `SOURCE.json` provenance/hashes and modified-status description. Those records are present; recheck them if the files change.

## B. MINIMAL v0.1 RELEASE ARTIFACT

| Decision | Material | Reason / required treatment |
| --- | --- | --- |
| INCLUDE | Browser trainer production output: HTML, compiled JS/CSS, worker, all six packaged WASM files and model | Actual v0.1 trainer runtime |
| INCLUDE | `licenses/dependencies.txt`, MediaPipe static notices/upstream license, model `LICENSE.txt`/`SOURCE.json` | Required redistribution terms and provenance |
| INCLUDE | Root LICENSE, NOTICE, AUTHORS, CITATION, third-party register, README, release notes, technical method, privacy/containment and focused reproducibility documentation | Legal and research record |
| INCLUDE | Trainer source needed to reproduce the artifact: `web/src/`, relevant shared/native reference source and fixtures, build scripts, manifests and lockfile | Reproducible source distribution |
| INCLUDE | Native Blender reference source, original scenes and original-asset provenance when the artifact is a source bundle | Preserved compliant reference; Blender remains external |
| EXCLUDE | Ten SPL VTKs and `blender/scenes/lapsim_ai_phase3b.blend` | Historical experiment not required by v0.1 trainer |
| EXCLUDE | SPL-derived Phase 3B outputs; retain only provenance/documentation needed to describe the historical experiment | Avoid unnecessary historical third-party data |
| EXCLUDE | `forcing-vs-convincing/` | Removed unrelated scaffold |
| EXCLUDE | Engineering outputs/screenshots, virtual environments, node_modules, caches, recordings, secrets, backups and downloads | Generated/private/non-release material |
| EXCLUDE | Blender executable/bundled Python and installed Python/npm packages | Users install prerequisites; no third-party binary environment redistribution |
| REVIEW REQUIRED | None for distribution licensing | Inspect assembled artifact and complete manual pre-publication checks |

The minimal deployed browser artifact is `web/dist/`; a minimal source bundle can additionally contain the listed source and documentation. Neither includes SPL VTK/Phase 3B anatomy.

## Procedural origin summary

The enclosure, board, pegs, rings, targets, handoff guide, tools and browser geometry are original procedural components. Original Phase 3 uses analytic/procedural anatomy. Phase 3B's independent shell/tubes/materials are original, while its liver/gallbladder and anatomy-derived regions are SPL-derived. Maintainer confirmation and generator/history inspection support these classifications; they do not relicense third-party material.

## Removed scaffold record

The six tracked `forcing-vs-convincing/` files originated in commit `6e7453251ab622fa4833d07d51f04f9d1682724d`. Its missing render entry/composition, private package, isolated workspace and absent trainer import/build/test edge established that it was unrelated. Phase 6.3 removed the entire directory, including ignored local dependencies, and no other Remotion material.
