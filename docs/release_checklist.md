# Manual release checklist — v0.1.0 Research Preview

**READY AFTER MANUAL PRE-PUBLICATION CHECKS.** Distribution licensing blockers were closed locally on 2026-09-12. The repository remains private and no publication action is authorized by this checklist.

## Completed distribution decisions

- [x] Canonical Apache-2.0 root LICENSE, scoped NOTICE, creator/copyright and original-asset grant recorded.
- [x] MediaPipe Tasks Vision 1.0.1 exact JS/WASM package files, hashes, npm integrity and source-map notices recorded; required static notices included.
- [x] Native Blender categories separated: original artwork/scenes Apache-2.0, original API scripts Apache-2.0 and GPLv3-compatible, Blender GPL-3.0-or-later installed separately and excluded.
- [x] SPL VTK/Phase 3B terms permit public repository retention with existing full license, preface, attribution, provenance and modification record.
- [x] SPL VTKs and derived Phase 3B scene explicitly excluded from the minimal v0.1 artifact.
- [x] Unrelated `forcing-vs-convincing/` dependency edge rechecked and directory removed under maintainer authorization.
- [x] Public GitHub and minimal artifact INCLUDE/EXCLUDE/REVIEW REQUIRED inventories recorded.
- [x] MediaPipe privacy remains **RESOLVED LOCALLY — VERCEL PRODUCTION CHECK PENDING**; existing 80.056-second local preview evidence retained.

## Required before publication

- [ ] Inspect the exact staged repository diff and history for unintended/private content; ensure the scaffold deletion is included in the reviewed commit.
- [ ] Assemble the minimal artifact only from `docs/release_inventory.md`; confirm SPL VTKs and `lapsim_ai_phase3b.blend` are absent.
- [ ] Inspect the built artifact for root/project legal documentation as applicable, `licenses/dependencies.txt`, both MediaPipe static files, and model provenance/license.
- [ ] Confirm Research Interest Form response access, email collection, sign-in, uploads, sensitive questions, linked-sheet permissions, permission-to-contact wording, removal contact and confirmation message.
- [ ] Set the actual release date after publication timing is known; review README, release notes and CITATION content. Do not invent a DOI.

## Required after private Vercel deployment, before public release

- [ ] Use Vercel Root Directory `web` with the recorded build/output configuration.
- [ ] Inspect the actual production document and hashed worker responses for the enforced CSP header.
- [ ] Run the documented >75-second real production privacy check; confirm the MediaPipe metrics POST is attempted and CSP-blocked while worker, WASM, model and inference continue.
- [ ] Verify the final private URL, browser/build identity, Research Interest navigation and absence of unintended successful external simulator requests.

## Publication controls

- [ ] Maintainer deliberately performs reviewed commit/push/tag/release/repository-visibility actions only after the checks above.
- [ ] No Blender executable, installed dependency environment, raw outputs, recordings, credentials or working-directory ZIP is admitted.

Previous engineering evidence remains valid: 94 native tests and Blender verification; 36 web tests, TypeScript/build, nine production smoke checks and timed local CSP test. Phase 6.3 changed release documentation/provenance and removed an isolated scaffold; simulator/control/task behavior source was unchanged, so engineering suites were not rerun.
