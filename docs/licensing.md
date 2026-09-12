# Licensing and distribution treatment — v0.1.0

Review date: 2026-09-12. Copyright **2026 Mohammad Jaradat**. The maintainer confirmed ownership of original LapSim-AI source, documentation and procedural assets and grants them under Apache-2.0. Third-party and derived material keeps its recorded terms.

## MediaPipe Tasks Vision 1.0.1

The official npm distribution for `@mediapipe/tasks-vision@1.0.1` declares Apache-2.0, contains the JS loaders and three WASM variants recorded by hash in `assets/third_party/mediapipe_tasks_vision/SOURCE.json`, and declares zero runtime dependencies. The npm package contains no `LICENSE`, `NOTICE`, bundled third-party notice file, or release-specific component manifest. Its source map carries Google LLC and Closure Library Apache-2.0 attributions. Printable-string inspection found no further notice text in the three WASM binaries.

LapSim-AI redistributes the six files under `web/dist/wasm/` byte-for-byte from the installed npm package. The production worker contains the bundled `vision_bundle.mjs`; the configured SIMD/module path loads `vision_wasm_module_internal.js` and `vision_wasm_module_internal.wasm`, while the other copied variants are fallbacks/package output. Redistribution treatment is therefore:

- retain Apache-2.0;
- ship `licenses/mediapipe-NOTICES.txt` with the Google/Closure source-map attributions;
- ship `licenses/mediapipe-upstream-LICENSE.txt`, which conservatively retains the complete upstream MediaPipe license and its Lucent UTF notice; and
- retain exact npm tarball integrity and per-file hashes in the provenance record.

This closes the identified notice blocker. The smallest remaining provenance limit is that npm 1.0.1 metadata provides neither `gitHead` nor a release-specific component SBOM, so the opaque WASM cannot be mapped to one exact upstream source commit from the published package alone. The official package license covers the distributed package artifacts, and no evidence of an additional or omitted license was found. Recheck all evidence on a MediaPipe version change.

## Blender native reference

Blender's [official licensing guidance](https://www.blender.org/about/license/) says Blender is GPL software, artwork/data created with Blender belongs to its creator, and distributed Python scripts using Blender's API must use a GPL-compliant license. Apache confirms Apache-2.0 is [compatible with GPLv3](https://www.apache.org/licenses/GPL-compatibility.html).

The exact repository inventory contains original LapSim-AI Python builders, controllers and verification scripts importing `bpy`, `bmesh`, `mathutils` or `bpy_extras`; five `.blend` scene/data files; original procedural geometry; and the separately identified SPL-derived Phase 3B anatomy. Inspection found no Blender executable/library, copied Blender/GPL source, linked external Blender library, embedded image, or embedded Python program. Peg Transfer contains an unpacked built-in Blender font; Phase 3B embeds its anatomy notice.

| Component | Treatment | Status |
| --- | --- | --- |
| Original procedural artwork and independent scene content | Creator-owned Apache-2.0 assets. Blender does not claim copyright in user artwork. | CLEAR |
| Original Python scripts using Blender's API | Distribute as Apache-2.0 source, an OSI license compatible with GPLv3. Preserve LapSim-AI LICENSE/NOTICE and identify separately installed Blender as GPL-3.0-or-later. Do not incorporate GPL-only Blender code without recording its terms. | CLEAR for source distribution |
| `.blend` files | Data/artwork files may use the creator's chosen terms; original content is Apache-2.0. Phase 3B also carries inherited SPL terms and attribution. | CLEAR with component provenance |
| Blender application | External GPL-3.0-or-later tool obtained separately from Blender. No Blender binary or source is shipped. | EXCLUDE from LapSim-AI artifacts |

This preserves the native reference without adding a GPL grant to unrelated LapSim-AI work or claiming Blender is Apache-licensed.

## Historical SPL anatomy

The ten VTK files and derived Phase 3B scene may remain in a public GitHub repository under the recorded 3D Slicer Contribution and Software License Agreement v1.0 terms. Any repository/archive redistributing them must include the adjacent full `LICENSE.txt`, the required Brigham preface, creator/institution attribution, source and hashes in `SOURCE.json`, and a clear statement that LapSim-AI modified the atlas geometry. The Phase 3B `.blend` also embeds `THIRD_PARTY_ANATOMY_LICENSE.txt`. Do not describe these components as Apache-only or imply institutional endorsement.

They are excluded from the minimal v0.1 artifact because the public trainer does not require them. Original analytic/procedural Phase 3 anatomy remains separate and Apache-2.0.

## Installed dependencies

Python requirements describe a separately installed environment; no wheels, native shared libraries, virtual environment, CPython, or Blender executable are distributed. The browser artifact carries Three.js under MIT, MediaPipe/model material under Apache-2.0 and the static notice files recorded in `THIRD_PARTY_LICENSES.md`. Future binary vendoring or dependency upgrades require a new component review.
