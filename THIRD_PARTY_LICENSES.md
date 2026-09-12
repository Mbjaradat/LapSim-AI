# Third-party materials and dependency register

Resumed Phase 6.1 audit: 2026-09-12. Copyright 2026 Mohammad Jaradat; original maintainer-owned source/docs/procedural assets use Apache-2.0. This register preserves external terms and does not relicense third-party or derived material. See [licensing](docs/licensing.md) and [inventory](docs/release_inventory.md).

## Original work (separate from dependencies)

| Component | Provenance | Status |
| --- | --- | --- |
| Independent Python/TypeScript and documentation | Repository source; maintainer-confirmed ownership | Apache-2.0; Mohammad Jaradat, 2026 |
| Original Phase 3, Peg Transfer and independent Phase 3B additions | assets/original provenance and generators | Apache-2.0 original components; inherited anatomy/regions excluded |
| Browser board, pegs, rings, instruments, materials and UI geometry | browser/instruments provenance; renderer.ts, grasper.ts | Apache-2.0 original assets |
| Blender API scripts and embedded scene instructions | `blender/scripts`, saved scene text blocks | Apache-2.0 original source; GPLv3-compatible for use with separately installed GPL-3.0-or-later Blender |

## Redistributed model and historical anatomy

| Material | Source / rights holder | Version / integrity | Terms and notices | Status |
| --- | --- | --- | --- | --- |
| MediaPipe Hand Landmarker full float16 | Google / MediaPipe; [official source](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task) | Retrieved 2026-09-07; SHA-256 `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1` | Apache-2.0 per local SOURCE.json/model-card record; unchanged; local LICENSE.txt; preserve applicable notices | Recorded source/license clear; checksum verified by build |
| SPL Liver Atlas February 2014 source VTKs and derived Phase 3B anatomy | Marianna Jakab, Sonia Pujol, Kitt Shaffer, Ron Kikinis; SPL/Brigham and Women's Hospital and Boston Medical Center; [atlas](https://www.openanatomy.org/atlas-pages/atlas-spl-liver.html) | Retrieved 2026-09-08; ten file hashes and source archive hash in SOURCE.json | 3D Slicer Contribution and Software License Agreement v1.0 (2005-12-20), Part B and applicable Part C; local LICENSE.txt | CLEAR for public repository with recorded preface, full terms, attribution and modified status; excluded from minimal artifact |

Model source, model-card evidence, retrieval date and obligations are in `assets/third_party/mediapipe_hand_landmarker/SOURCE.json`. Model and WASM binaries are copied without modifications. Model `latest` is only a source URL: the recorded hash identifies the bundled artifact.

Anatomy source and exact per-file integrity are in `assets/third_party/anatomy/spl_liver_2014/SOURCE.json`. Its local LICENSE.txt is part of the distribution. The native Phase 3B scene also contains `THIRD_PARTY_ANATOMY_LICENSE.txt`. The public Peg Transfer and browser trainer do not use this anatomy, but Git archives include it unless the maintainer changes scope.

Required attribution: Liver and gallbladder adapted from SPL Liver Atlas (February 2014), Jakab M., Pujol S., Shaffer K., Kikinis R.; SPL/Brigham and Women's Hospital and Boston Medical Center. Modified by LapSim-AI; not the original atlas.

Required preface: All or portions of this licensed product (such portions are the “Software”) have been obtained under license from The Brigham and Women’s Hospital, Inc. and are subject to the following terms and conditions:

The complete terms follow in [the included anatomy license](assets/third_party/anatomy/spl_liver_2014/LICENSE.txt); this register does not replace them. Retain all Part B paragraphs and applicable terms in copies/sublicenses and user documentation. The [official Slicer terms](https://www.openanatomy.org/atlas-pages/slicer-license.html) were checked in Phase 6. No institutional endorsement is implied. Modifications include VTK triangulation, joined/remeshed liver segments, smoothing/decimation, common presentation transform/scale and procedural materials; details remain in SOURCE.json and builder configuration.

## Browser runtime and direct build dependencies

Installed package.json license metadata was inspected; versions are pinned in `web/package.json` and `web/pnpm-lock.yaml`.

| Package | Version | Declared license | Distribution role / upstream |
| --- | --- | --- | --- |
| three | 0.186.0 | MIT | Bundled runtime; [three.js](https://github.com/mrdoob/three.js) |
| @mediapipe/tasks-vision | 1.0.1 | Apache-2.0 | JS runtime + packaged WASM; [MediaPipe](https://github.com/google-ai-edge/mediapipe) |
| vite | 8.2.2 | MIT | Build/development tool; [Vite](https://github.com/vitejs/vite) |
| typescript | 7.0.2 | Apache-2.0 | Type checker/compiler tooling; [TypeScript](https://github.com/microsoft/TypeScript) |
| tsx | 4.23.13 | MIT | Test runner tooling; [tsx](https://github.com/privatenumber/tsx) |
| playwright | 1.63.0 | Apache-2.0 | Browser tests; [Playwright](https://github.com/microsoft/playwright) |
| @types/node | 26.5.0 | MIT | Type definitions; [DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped) |
| @types/three | 0.185.4 | MIT | Type definitions; DefinitelyTyped |

`web/scripts/assets.mjs` verifies the model and generates dependencies.txt with full Three.js MIT and Apache text. Model provenance/license files accompany the model. Vite bundles/minifies JS without package edits. The minified MediaPipe JS omits source-map license comment blocks, so the new static notice files preserve those attributions in the next build. WASM/model bytes remain unchanged. Hashes and notice sources are in assets/third_party/mediapipe_tasks_vision/SOURCE.json.

**WASM notice closure:** the official npm 1.0.1 distribution declares Apache-2.0 for the package containing the exact hashed JS/WASM artifacts and declares zero runtime dependencies. It supplies no separate LICENSE, NOTICE or binary component manifest. Redistribution includes the source-map Google/Closure Apache attributions in `web/public/licenses/mediapipe-NOTICES.txt` and the conservatively retained full upstream license, including Lucent UTF notice, in `mediapipe-upstream-LICENSE.txt`. Npm tarball integrity and file hashes are in `assets/third_party/mediapipe_tasks_vision/SOURCE.json`. The remaining provenance limit is the absent `gitHead`/release-specific SBOM; no additional or omitted license was evidenced. Build tools/node_modules are not distributed.

## Native installed environment (not redistributed)

Versions below were read from local installed distribution metadata; `requirements-native.txt` captures the same environment without pip. No virtual environment or Blender executable should be shipped.

| Package | Version | Installed declared license / caveat |
| --- | --- | --- |
| mediapipe | 1.0.1 | Apache-2.0 |
| opencv-contrib-python | 5.0.0.93 | Apache-2.0; wheel embedded third parties require their own notices if redistributed |
| numpy | 2.5.3 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 in installed metadata; inspect wheel notices if bundled |
| absl-py | 2.5.0 | Apache-2.0 |
| certifi | 2026.7.22 | MPL-2.0 |
| cffi | 2.1.1 | MIT-0 |
| contourpy | 1.3.3 | BSD-3-Clause |
| cycler | 0.12.1 | BSD-3-Clause |
| flatbuffers | 25.12.19 | Apache-2.0 |
| fonttools | 4.64.0 | MIT |
| kiwisolver | 1.5.1 | Modified BSD |
| matplotlib | 3.11.1 | Matplotlib license plus bundled component/font notices; not one blanket license |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pillow | 12.3.0 | MIT-CMU |
| pycparser | 3.0 | BSD-3-Clause |
| pyparsing | 3.3.2 | MIT |
| python-dateutil | 2.9.0.post0 | Dual Apache/BSD per metadata |
| six | 1.17.0 | MIT |
| sounddevice | 0.5.6 | MIT; bundled audio components need separate review if distributed |
| pip | 25.0.1 | MIT; environment tooling |

These are inspection results, not an assertion that every package is directly imported by the application. Package source/project links are available from each distribution's metadata and its package index entry. CPython and Blender are separately installed prerequisites. Blender 5.2.1 LTS is GPL-3.0-or-later software with its own dependencies and is not bundled; see [Blender licensing](https://www.blender.org/about/license/). Original artwork remains creator-owned, and original Apache-2.0 API scripts use a GPLv3-compatible license.

## Fonts, icons, screenshots and unrelated material

Browser uses system fonts, text symbols/CSS and procedural Three.js geometry, with no external font/icon/image imports found. Saved scene inventory found no images or linked libraries and only an unpacked built-in Blender font in Peg Transfer; historical Phase 3B includes its anatomy notice. No screenshot/video is tracked. Ignored `outputs/` can contain local test screenshots and must not enter a release automatically.

The independent six-file `forcing-vs-convincing/` Remotion scaffold had no trainer import/build/test relationship and was removed in Phase 6.3 under the maintainer's explicit decision. Its ignored local dependencies were removed with it; no other Remotion material was removed.

## Admission and update procedure

Record source, creator, retrieval date, exact version/hash, terms, modifications, local license text, attributions and review status for any added asset. Preserve inherited terms and distinguish original from adapted work. Recheck replacement versions and actual built bundles. Unknown terms remain a blocker; neither a lockfile nor this register is a blanket license grant.
