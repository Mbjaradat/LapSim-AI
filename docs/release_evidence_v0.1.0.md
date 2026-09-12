# Release evidence — LapSim-AI v0.1.0 Research Preview

**Phase 6.2B: PRIVACY BLOCKER RESOLVED LOCALLY — PRODUCTION CHECK PENDING.** Worker-response CSP containment is implemented and verified in production preview. Internal metrics collection remains present. The actual Vercel response and >75-second runtime check remain required before publication. See [containment](worker_network_containment.md). Historical Phase 6/6.2 test records below remain distinct from the Phase 6.2B evidence.

Phase 6.2B validation: 36 web tests, TypeScript check, production build and nine production browser smoke checks passed. The saved 80.056-second network test passed without header injection: worker/model/WASM loaded, the attempted metrics POST was CSP-blocked, and inference continued from 333 to 340 responses. The completed timed test was not repeated after interruption. [Machine-readable evidence](evidence/phase6_2b_containment.json) records the measured outcomes. No simulator source or dependency changed; all 95 earlier source/scene hashes match. No actual Vercel deployment has occurred.

Validation date: **2026-09-11**. Base source commit: `244134707f511d1d943ccb910af58404c3316dda`, with Phase 6 documentation/metadata changes uncommitted. Environment: Windows, standalone Python 3.12.10, Node 24.19.0, pnpm 11.19.0, Blender 5.2.1 LTS (build hash 9e2066aef7ef), local headless Chrome with fake video and software WebGL. No physical webcam was accessed by the assistant. No release date is inferred from this audit date.

**Verdict: READY AFTER MANUAL PRE-PUBLICATION CHECKS.** Engineering checks pass and distribution licensing/scope is resolved. Form administration, private Vercel production verification and final release content/date review remain manual actions. No runtime behavior was changed.

## Measured reruns

Commands use PowerShell. Web commands run from `web/`; native/Blender commands from repository root. Exact reusable setup is in [development.md](development.md).

| Command | Phase 6 result |
| --- | --- |
| `pnpm test` | PASS: 36 tests, 0 failed/skipped; full constrained Node trial 452 ticks |
| `pnpm typecheck` | PASS: TypeScript noEmit |
| `pnpm build` | PASS: model checksum, notice/WASM copy, typecheck, Vite production bundle |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` | PASS: 94 tests |
| `.\.venv\Scripts\python.exe -m pip check` | PASS: no broken requirements |
| Blender `verify_peg_transfer.py` | PASS: 449 controller ticks, six complete handoffs/placements, reset, 13 critical reach points, 10% joint margin, 20 keyboard bindings |
| Blender `verify_phase5.py` | PASS: synthetic guided pair capture, modal countdown, loss/restart/LIVE, isolation, recovery, pause, recenter, retry, unchanged camera |
| `pnpm test:browser`, TEST_BASE_URL=http://127.0.0.1:5173 | PASS: 12 checks, 0 page errors; fake-camera worker inference, synthetic structured/beginner completion, results/retry, link wiring, lifecycle/error/layout checks |
| `pnpm test:browser`, TEST_BASE_URL=http://127.0.0.1:4173 | PASS: 9 checks, 0 page errors; production has no dev synthetic seam; local model/WASM/camera lifecycle and no uploads |

Blender command prefix:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/verify_peg_transfer.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/verify_phase5.py
```

Browser used `TEST_CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe`, a running `pnpm dev` or `pnpm preview`, and the base URLs above. The first default Playwright launch failed because its downloaded headless-shell executable was absent; the installed Chrome override then passed. Initial sandboxed pnpm/Python launches were denied access to installed runtimes/caches; reruns with approved tool access passed. No test was weakened and no application dependencies/browser binaries were installed. Citation-only PyYAML/jsonschema utilities were installed into ignored outputs/phase6/validation-deps, outside the application environment. Blender peg verification emitted an extension-cache warning and 0.023346 MB shutdown memory notice, with all assertions passing and exit code 0.

In Phase 6, web tests/typecheck/build and native Python tests were run again after documentation/metadata preparation, with the same pass counts and unchanged production asset hashes. Local links, JSON/TOML, versions and acknowledgement were checked. The then-draft CFF passed schema validation. Attribution was subsequently confirmed by the maintainer in resumed Phase 6.1; engineering suites were not rerun for those legal metadata edits.

## Numerical checks (MEASURED)

| Quantity | Current measured value | Scope |
| --- | --- | --- |
| Browser reconstructed pivot maximum | 1.3877787807814457e-17 m | 486 mixed/extreme poses, both sides, tolerance 1e-6 m |
| Browser rendered shaft pivot | 2.8609792490763984e-17 m | Development smoke completion scene, tolerance 1e-6 m; not a 486-rendered-pose sweep |
| Native Blender Peg Transfer pivot maximum | 1.5359765386647212e-08 m | Saved-scene six-ring trial, tolerance 1e-6 m |
| Native event totals | 12 grasps, 12 releases, 6 handoffs, 6 successful placements; 0 drops/incorrect placements | Synthetic full-trial assertions |
| Browser Chrome structured trial | 450 ticks | Same outcome as 452-tick Node/449-tick native trial; counts are not equality requirements |

These are numerical/geometric constraint checks, not measurements of clinical realism, surgical skill or training effectiveness. The idle headless software-rendering sample is diagnostic only (60 frames, approximately 46.29 ms mean in this run); it is not physical-camera gameplay latency or a hardware benchmark.

Selected machine-readable reports, asset checks and scene inventory are in [phase6_checks.json](evidence/phase6_checks.json). Raw tool logs and synthetic screenshots remain ignored under `outputs/`; the retained record does not include webcam images or participant data.

## Capability/evidence matrix

All current simulator capabilities below remain **EXPERIMENTAL**; engineering PASS does not mean clinical validation. “Observed overall” means only the maintainer's broad positive browser impression, not a separate measured pass for every row.

| Capability | Implementation | Automated evidence | Physical/manual evidence | Validation boundary |
| --- | --- | --- | --- | --- |
| Landmark detection | IMPLEMENTED native/web | Real browser model/WASM on fake camera; native module tests | Browser use reported overall; no detailed protocol | Accuracy across users/lighting NOT VALIDATED |
| Physical handedness | IMPLEMENTED | Extraction/mapping and duplicate/missing identity tests | Per-hand physical acceptance NOT DOCUMENTED | Occlusion/crossing robustness NOT VALIDATED |
| Calibration/HOME/LIVE | IMPLEMENTED | Pure native/web tests + Blender modal synthetic sequence | Browser overall observation only; native acceptance pending | User-range heuristics NOT VALIDATED |
| Yaw/pitch | IMPLEMENTED | Palm steering, mapping, bounds/parity tests | Browser overall observation only | Ergonomic generalization NOT VALIDATED |
| Insertion | IMPLEMENTED | Palm-depth/independence/deadband tests | Browser overall observation only | Metric depth NOT IMPLEMENTED |
| Roll | IMPLEMENTED | Palm-frame/swing/twist/wrap/degenerate tests | Browser overall observation only | Biomechanical angle validity NOT ESTABLISHED |
| Jaws | IMPLEMENTED | Pinch/rate/clamp tests | Browser overall observation only | Force/haptic realism NOT IMPLEMENTED |
| Dual tools/trocar | IMPLEMENTED | Pose/proxy/parity and pivot checks | Browser overall observation only | Clinical fidelity NOT ESTABLISHED |
| Board collision | IMPLEMENTED | Capsule/plane, evaluated native vertices | Separate physical protocol NOT TESTED | Simplified geometry only |
| Instrument collision | IMPLEMENTED | Pair sweep and escape checks | Separate protocol NOT TESTED | Gross collision, no full dynamics |
| Workspace/held ring | IMPLEMENTED | Boundary/camera/support tests each trial | Separate protocol NOT TESTED | Deterministic containment only |
| Grasp/release/handoff | IMPLEMENTED | State/edge/ownership/full-trial tests | Browser overall observation only | Simplified interaction |
| Ring transfer/drop | IMPLEMENTED | Correct/wrong/occupied/drop/recycle tests | Browser overall observation only | FLS equivalence NOT ESTABLISHED |
| Telemetry | IMPLEMENTED | Exact event totals, timing, pause, threshold, reset/freeze | Independent physical reference comparison NOT TESTED | Descriptive only |
| Beginner Free Transfer | IMPLEMENTED web | 7 beginner tests + browser synthetic transitions | Browser usability reported | Competence/proficiency assessment NOT VALIDATED |
| Browser execution | IMPLEMENTED | Development 12 / production 9 checks | One maintainer qualitative report | Broad browser/device coverage NOT TESTED |
| Webcam permissions/lifecycle | IMPLEMENTED | Fake-device and simulated denial/absence; stop tracks | Physical use reported overall | Camera compatibility matrix NOT TESTED |
| Native Blender execution | IMPLEMENTED | Peg and Phase 5 headless reruns | Native physical hands-free acceptance pending | Synthetic integration evidence |
| Tracking loss/recovery | IMPLEMENTED | Stale hold, bounded reacquisition, calibration persistence | Separate detailed physical protocol NOT TESTED | Loss does not pause timer |
| Local processing/privacy | Local frames/landmarks/calibration/results; dependency collection remains present | Phase 6.2B: served worker CSP blocked POST during 80.056-second production-preview test | Actual Vercel >75-second check PENDING | Containment verified locally; no universal network/privacy guarantee |
| Clinical training effectiveness | NOT ESTABLISHED | No clinical study | No clinical study | PLANNED research direction |
| Construct/predictive validity | NOT ESTABLISHED | No validation study | No validation study | PLANNED research direction |

## Manual observation (OBSERVED, maintainer-reported)

The Phase 6 request states that a physical manual browser usability test was performed by the maintainer with a positive overall usability impression. It supplies no exact date, camera/browser/GPU details, participant count, timing measurements or per-step checklist. We record that report without inventing them. It does not close native hands-free acceptance or establish clinical validity. Before public launch, record the actual tested build/device/browser and unresolved issues, and verify the final deployed workflow. No new human-subject data was collected here.

The browser smoke script's `physicalWebcamValidation:PENDING` field describes its own inability to test real hands. It is not evidence contradicting the separately reported manual trial.

## Not rerun / not tested

`verify_phase1a.py`, `verify_phase1b.py`, `verify_phase2d.py` and `verify_phase3.py` standalone suites: **NOT RE-RUN IN PHASE 6**. Some shared assertions execute through the current peg verifier, but that is not a full rerun of those standalone suites. Historical results remain in their phase documents; no additional historical pivot numbers are promoted as current measurements.

Fresh dependency installation on another computer, physical native hands-free acceptance, multi-user/device/browser testing, hosted Google Form contents/privacy settings, public repository visibility, deployed production URLs and clinical studies: **NOT TESTED/NOT ESTABLISHED** here. No DOI or archive exists as a result of this work.

## Audit conclusions and limitations

The model and ten anatomy VTK checksums matched. Saved-scene inventory found no embedded images, linked external libraries or stored session properties. Historical tracked-text heuristics found no credential candidate; this is not a complete history/binary secret audit. Original licensing and creator metadata are confirmed. Phase 6.3 closed Blender component treatment and exact WASM notices, defined anatomy scope and removed the unrelated scaffold. Form administration and private-production checks remain. See [audit](release_audit.md), [licensing](licensing.md), [privacy](privacy_research.md) and [checklist](release_checklist.md).

Monocular scale/pose limitations, calibration dependence, lighting/occlusion sensitivity, lack of haptics, simplified collisions/objects, procedural visuals and limited physical hardware coverage remain. No validated skill score, construct/predictive validity or training effectiveness is claimed. Further studies are PLANNED, not completed evidence.

## Resumed Phase 6.1 release-only validation

Canonical LICENSE, confirmed Mohammad Jaradat/2026 attribution, Apache metadata, procedural/model/anatomy provenance, static notices, CFF schema and inventories were checked without rerunning engineering suites. Phase 6.3 closes exact WASM notice coverage and native/scope decisions; the earlier Phase 6.1 evidence remains a historical snapshot. See [licensing](licensing.md) and [inventory](release_inventory.md). Phase 6.2B privacy remains RESOLVED LOCALLY — VERCEL PRODUCTION CHECK PENDING.
