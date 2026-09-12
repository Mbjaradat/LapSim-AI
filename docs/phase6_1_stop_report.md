# Phase 6.1 stop report — MediaPipe privacy discrepancy

**Historical report — Phase 6.2B update:** the approved worker CSP is now implemented and verified locally; actual Vercel production verification remains pending. See [current containment status](worker_network_containment.md). Statements below about pending implementation describe the earlier phase.

**Historical record:** the subsequently authorized [Phase 6.2 investigation](mediapipe_privacy_investigation.md) traces the payload and records a timed POST attempt. This stop report preserves the earlier evidence boundary; its request to authorize that investigation has been fulfilled. Broader Phase 6.1 work remains paused pending privacy remediation.

Status: **NOT READY — BLOCKERS REMAIN**. The Phase 6.1 maintainer instruction requires stopping and reporting an actual release-blocking defect rather than modifying simulator behavior. The audit stopped on the dependency privacy finding below. The other Phase 6.1 licensing/scope tasks are unfinished; this is not a completed blocker-resolution audit.

## Static evidence

The installed `@mediapipe/tasks-vision` package is version 1.0.1. Its README's “Privacy Notice” (marked June 5, 2026) states that input processing takes place on device, and separately states that the APIs send performance/utilization metrics to Google. It describes user-consent responsibilities. This is a dependency notice, not proof of actual successful network transmission in this application.

Inspection of `web/node_modules/@mediapipe/tasks-vision/vision_bundle.mjs` found:

- The detector creation path constructs its logger (`t.m=new Dh(t.C(),e,r)`) before applying task options.
- The logger constructs a sender and schedules `setInterval(...,6e4)`: a 60-second flush interval.
- The sender contains a POST request to `https://odml.pa.googleapis.com/v1/log` using `application/x-protobuf`.
- Logger code handles task/performance counters. The inspected evidence does not establish upload of webcam images or LapSim-AI session results.
- The current built worker `web/dist/assets/hand-worker-CFdBzOHs.js` also contains the logging endpoint and timer code. Thus this is not merely an unused README example or a native-only dependency notice.

SHA-256 values at inspection:

| Artifact | SHA-256 |
| --- | --- |
| Installed vision_bundle.mjs | d885630c297c0b20b1fe86096cb06291c4c8080876f27852e724f24ac603713f |
| Built hand-worker-CFdBzOHs.js | 94471389acbb1864febd9d42ccb60ea026b820ed4c4b3732fe799c8fa3b88526 |

No behavioral test or network transmission was initiated to exercise that endpoint. Whether the deployed worker's effective policies block a particular request, and precisely when its queue becomes nonempty, were not dynamically verified. No dependency API-key value is reproduced in this report.

## Why this blocks release

Phase 6 application-source inspection and short browser smoke scenarios observed no uploads. Those bounded observations remain historical facts, but did not establish that the bundled dependency has no analytics/metrics sender over longer use. The README/privacy record's broader no-analytics assurance cannot currently be treated as verified for the full browser distribution.

This is a release-blocking privacy-assurance discrepancy, not evidence that hand frames were uploaded or a claim that a metrics request succeeded. It must be resolved before reaffirming no cloud telemetry or publishing the software with that promise. Do not fix it by silently weakening the privacy statement or changing a dependency/control pipeline.

## Required next step

Authorize a separate focused investigation/correction of the MediaPipe metrics path. Establish its exact behavior and a supported way to meet the intended no-cloud-telemetry policy without transmitting user data during validation. Any dependency/configuration/code change requires explicit review under the Phase 6.1 stop instruction, focused validation, and corrected privacy evidence. Resume the remaining licensing/scope tasks afterward.

## Other findings before the stop

- GitHub repository metadata was read through the connector and returned `visibility: private`. No visibility mutation or other publication action was made.
- The maintainer's Apache-2.0 choice is authorized, but no root LICENSE or license metadata change was made before this stop. The existing Phase 6 working changes remain.
- `forcing-vs-convincing/` contains six tracked configuration files and ignored node_modules; its Remotion render command targets missing `src/index.ts`, composition `TreatmentChoice`, and a video under `out/`. It entered Git in commit `6e7453251ab622fa4833d07d51f04f9d1682724d` with the Peg Transfer work. The commit does not explain why. Searches performed so far found configuration/documentation references, not a trainer runtime import. The full requested forensic audit is incomplete; classification for now: **MAINTAINER DECISION REQUIRED**. Nothing was deleted.
- Tracked-file inspection found no wheel, executable, shared-library or image files matching the queried binary patterns. Python dependencies remain declarations plus an ignored local environment; an ordinary declaration is not wheel redistribution.
- Existing SPL atlas provenance links to the official atlas page, which explicitly points to Slicer License section B. This supports narrowing the anatomy review, but the complete Phase 6.1 notice audit was not finished.
- The Research Interest URL matches repository configuration. Public form content could not be fetched by the web tool. No form was submitted and no response/admin settings were accessed.

## Validation and safety

No simulator/control/task source, tests, scene binaries or dependency versions were changed. Phase 6 engineering results are **VERIFIED IN PHASE 6 — NOT RE-RUN IN PHASE 6.1**. The prior tests do not settle the new privacy finding. The only Phase 6.1 writes are this report and prominent links warning readers in README, privacy documentation and release evidence.

No commit, push, tag, GitHub Release, repository-visibility change, Vercel deployment, Zenodo publication or invented DOI occurred. The existing Ahmad Jaradat equipment acknowledgement remains unchanged. Copyright-holder/creator names and publication date were not invented.
