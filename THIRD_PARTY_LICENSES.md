# Third-party materials register

The peg-transfer MVP adds no third-party assets or downloads. Its procedural
board/pegs/rings/materials are recorded in
`assets/original/peg_transfer/PROVENANCE.json`. It does not import the separate
anatomy assets. Existing prerequisites and original-license decisions are unchanged.

Phase 3 adds **no third-party assets**: its liver, gallbladder, cavity, beads and
debug geometry/materials are original procedural work. See
`assets/original/phase3/PROVENANCE.json`. No external anatomy was downloaded,
traced or copied. Original code and generated-scene distribution licensing remain
pending under docs/licensing.md; no license is finalized by this addition.

The existing Phase 2 MediaPipe model is third-party and remains separate from
original code/assets. Blender and the locally installed Python packages are
external prerequisites, not redistributed Blender binaries or vendored packages.

This register is separate from the proposed license for original source code. Before adding any material, record all fields below, including embedded textures, fonts, scripts, model weights, and transitive bundled components. Use one row per item or link a detailed per-item record if necessary.

| ID / repository path | Type / version / SHA-256 | Origin and title | Author / rights holder | Original URL / source | Retrieved date | Exact license / version | Local license text | Modifications | Attribution and redistribution requirements | Review status / reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| assets/third_party/mediapipe_hand_landmarker/hand_landmarker.task | Hand Landmarker full float16; SHA-256 fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1 | MediaPipe Hand Landmarker | Google / MediaPipe | [Official model](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task) | 2026-09-07 | Apache-2.0, per existing SOURCE.json/model-card evidence | assets/third_party/mediapipe_hand_landmarker/LICENSE.txt | None | Retain license/applicable notices; identify modifications; commercial use, modification and redistribution permitted subject to license terms | Existing Phase 2 record preserved; not newly downloaded in Phase 3 |

The per-model `SOURCE.json` preserves the exact origin, author, license evidence,
retrieval date, checksum and redistribution requirements. Generated Phase 3
reports under `outputs/phase3/` are intermediates, not imported assets. A future
release must review original source licensing separately from asset licensing
and include the applicable third-party notices; this register is not a blanket
license grant.

## Admission process

### Browser MVP runtime additions (2026-09-10)

| Item | Source / rights holder | License and shipped notices | Modification / review |
| --- | --- | --- | --- |
| three 0.186.0, pinned in web/pnpm-lock.yaml | https://github.com/mrdoob/three.js / three.js authors | MIT; installed package LICENSE copied into generated dist/licenses/dependencies.txt | Bundled/minified by Vite; upstream source unchanged; package license inspected |
| @mediapipe/tasks-vision 1.0.1, including packaged WASM variants, pinned in web/pnpm-lock.yaml | https://github.com/google-ai-edge/mediapipe / Google and MediaPipe contributors | Apache-2.0; Apache text included in generated dist/licenses/dependencies.txt, inline packaged notices retained | JS bundled; WASM copied unchanged; package license and upstream license checked |
| Existing Hand Landmarker model and provenance record | Existing registered model above | SOURCE.json and LICENSE.txt copied alongside checksum-verified model in dist/models | No new model download; no modifications |

`web/scripts/assets.mjs` generates the notices and verifies the model SHA-256 before
development/build. The lockfile records exact npm distributions and integrity
hashes. Vite/TypeScript/tsx/Playwright and their development dependencies are local
build/test tools, not shipped application modules. Three.js and MediaPipe are the
two bundled runtime packages. No downloaded visual assets or fonts were added;
the browser trainer uses original procedural geometry and system fonts. Public
distribution still requires the existing original-license decision; this register
does not grant a license to the project's original code.

### Procedure

1. Verify terms at the original source and record author, source URL, version, and checksum.
2. Preserve the applicable license text under `assets/third_party/<item>/` for assets, or alongside vendored code, and link it here.
3. Record modifications explicitly, including “none” where applicable.
4. Record attribution wording, share-alike, source-offer, notice, commercial-use, and redistribution conditions as applicable. Identify incompatible restrictions before inclusion.
5. Review the whole bundle, including embedded components. Unknown or unverifiable terms mean do not add the material.
6. Recheck provenance when replacing or updating an item. Include required notices in release packages.

Future dependencies must also have their version, upstream source, and license reviewed. A dependency lockfile alone is not a license record. An empty register does not inventory the contents of a separately installed Blender distribution.
