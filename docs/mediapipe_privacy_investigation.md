# Phase 6.2 — MediaPipe metrics privacy investigation

**Historical report — Phase 6.2B update:** the approved worker CSP is now implemented and verified locally; actual Vercel production verification remains pending. See [current containment status](worker_network_containment.md). Statements below about pending implementation describe the earlier phase.

Date: 2026-09-11. Scope: the installed `@mediapipe/tasks-vision` 1.0.1 JavaScript logger and its use by the current LapSim-AI browser worker. No licensing audit, dependency change or publication is part of this investigation.

**Verdict: REMEDIATION AVAILABLE — MAINTAINER APPROVAL REQUIRED.** An enforced worker response CSP blocked the metrics fetch while inference continued in the tested development/production browser. That policy was injected only by the audit harness and has not been implemented or deployed. The release blocker remains open until approved remediation is verified.

## Evidence identity

- Application entry: `web/src/app.ts`; detector boundary: `web/src/hand-worker.ts`.
- Installed package: `web/node_modules/@mediapipe/tasks-vision/{package.json,README.md,vision.d.ts,vision_bundle.mjs,vision_bundle.mjs.map}`. The package is pinned to 1.0.1 in `web/package.json` and the lockfile.
- Installed `vision_bundle.mjs` SHA-256: `d885630c297c0b20b1fe86096cb06291c4c8080876f27852e724f24ac603713f`.
- Existing production worker `web/dist/assets/hand-worker-CFdBzOHs.js` SHA-256: `94471389acbb1864febd9d42ccb60ea026b820ed4c4b3732fe799c8fa3b88526`. It contains the same sender and timer.
- The package source map contains one `vision_js.js` source. It was extracted to ignored `outputs/phase6_2/vision_source.js`. Symbols below refer to that source, not to the differently minified final bundle or an assumed upstream version.
- Authoritative upstream comparison: [TaskRunner source](https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/mediapipe/tasks/web/core/task_runner.ts). The inspected current source calls `enableLogging(options)` during construction. The installed bundle remains the controlling evidence.

## Static call trace

1. Start Training requests camera permission, starts the local worker and sends `init`. `FilesetResolver.forVisionTasks(data.base + 'wasm', true)` resolves local WASM; `true` requests the module loader. It is not a privacy setting. `HandLandmarker.createFromOptions` uses the local model, CPU delegate, VIDEO mode, two hands and an OffscreenCanvas.
2. `createFromOptions` → vision helper `X` → `lk` → `jk` → `ek` creates the graph runner. `jk` then unconditionally calls `kk(a, options)` before applying options. `kk` gets the task name, running mode and optional WASM-supplied API key, then assigns `new Tj(...)`. No feature flag, consent check or opt-out guards this path.
3. `Tj` owns counters, a timestamp-to-start-time map and `new Mj(apiKey)`. `setGraph` calls `Tj.ya()`, which queues an initialization event including elapsed initialization time. Thus initialization alone creates a sendable event; inference is not required.
4. VIDEO processing `tl` increments the CPU/GPU input counter and maps the input timestamp to `performance.now()`. The image takes a separate graph-input path. `finishProcessing(timestamp)` calls `Tj.za(timestamp)` after graph execution and error checking; it measures invocation duration, updates completed count, sums and maximums. At a completion more than 30 seconds after the previous statistics boundary, it queues interval statistics via `Rj`/`Sj`. Older unmatched invocations contribute a dropped/uncompleted count.
5. `Qj` serializes common context plus an event (`zj`), stores these bytes in field 6 of a log envelope (`Bj`) and queues that envelope in `Mj.h`. It does not receive image buffers, landmarks or LapSim-AI results.
6. `Mj` starts `setInterval(..., 60000)` in its constructor. A nonempty queue is drained, batched by `Jj` and serialized by `Lj`. `Mj.flush` calls `Aj.send`, which uses `fetch` to POST to `https://odml.pa.googleapis.com/v1/log`, with a 10-second AbortController timeout when supported. Headers are `Content-Type: application/x-protobuf` and `x-goog-api-key`. The key value is deliberately excluded from this record. No cross-origin `credentials: include` is set.
7. Only HTTP 200 is treated as sender success. A failed send sets terminal error state, clears queued events and the timer; no retry is evident. Counters can still update, but `Qj` drops subsequent events once the sender is in error state.
8. Library `close()` queues final performance/session-end events and flushes. LapSim-AI stops by terminating its worker, without invoking detector `close()`, so that final-flush path is not the application's current stop path.

Source-map landmarks: sender/envelopes approximately lines 91–100; construction at 121; graph initialization/completion/close at 126; input-arrival hook at 168. These line references are specific to the extraction above.

## Payload construction and data boundaries

Field numbers below describe the **constructed messages**, not every field permitted by Google's larger protobuf schema. Defaults may be omitted by protobuf serialization. Units for measured durations are milliseconds (`performance.now()`); `Zd`/`vc` converts durations to unsigned integer fields for serialization.

| Category | Constructed values and evidence |
| --- | --- |
| Library/common context (`yj`) | Field 4: literal `1.0.1`; field 6: enum value 4, whose semantic label is not established. Fields 2, 3 and 5 are explicitly empty strings. |
| Platform | Common field 1: value 0 when `typeof window === 'undefined'`, as in this worker. The alternate window path maps user-agent text to coarse OS enums, but does not serialize the raw user-agent. Browser/network-added headers are separate from this payload. |
| Task and mode | `Oj('HandLandmarker')` → task 10; `Pj('VIDEO')` → mode 12. No model URL, filename, hash or bytes are supplied to the logger. |
| Initialization (`tj`) | Field 1: mode; field 3: initialization elapsed time. Event kind 0, task 10. |
| Performance (`qj`) | Field 1: mode; field 4: average completed-invocation duration when available; field 5: maximum duration; field 6: interval/session elapsed time; field 7: dropped/uncompleted count. Repeated field 8: delegate input-count messages (subfield 1: CPU enum 3 or GPU enum 4; subfield 2: count). Interval events use kind 1. Completed count and duration sum feed the average; they are not separately written here. |
| Session end | Kind 2, containing full-session performance; available on library close. No random/session identifier is constructed. |
| Envelope | Outer `Kj` field 2 constant 1786; repeated field 3 envelopes; each `Bj` field 6 contains serialized metrics. Semantic name of constant 1786 is not established by the installed builder. |
| Errors | Dropped/uncompleted counts are present. No exception message, stack trace or simulator error content enters these builders. Sender errors remain internal. |
| Time/identifiers | Input timestamps index the local pending map; durations are serialized. No wall-clock timestamp, user/account ID or generated session ID is written by this path. |
| URLs/origins | No application origin or URL is written into the constructed payload. The endpoint is fixed. Normal HTTP transport can expose IP address and browser-supplied headers such as Origin, Referer or User-Agent; this is distinct from protobuf contents. Actual Google receipt was not tested. |

Explicit answers for the inspected logger and application data flow:

- **Raw webcam frames: not included.** ImageBitmap input goes to local graph inference, then is closed; the logger receives input counts and timestamps.
- **Encoded/cropped webcam images: not included.** No image encoding, image bytes or crop data is passed into the metrics builders.
- **Hand landmark coordinates: not included.** Detector results are extracted and posted back to the local page, independently of logger events.
- **Calibration: not included.** Page-local setup/stabilizer state is not an input to the worker logger.
- **LapSim-AI task/session results: not included.** Page-local task/Telemetry state is not posted to MediaPipe. MediaPipe's own performance statistics are a different data category.

These are bounded findings about the reviewed implementation, not a certification of browsers, extensions, hosts, operating systems, every WASM instruction or future dependency versions.

## Runtime results

Local headless Chrome 152.0.7977.84, Playwright 1.63.0, a fake video device and software WebGL were used; no physical webcam or private input was used. Cases ran sequentially. Every nonlocal network request was intercepted and aborted by Playwright context routing, which demonstrably captured the dedicated worker's baseline POST body. No successful Google response was sought. Timings below are measured from each case's start; the observation window starts after page/worker readiness and is independently longer than 70 seconds.

| Case | Observation window | Endpoint observation | Inference/session evidence |
| --- | --- | --- | --- |
| Development page idle | 75.028 s | No external request | No worker; camera OFF |
| Development worker initialized, no camera/frames | 75.051 s | POST at 61.343 s; 39 bytes; harness-aborted | Worker ready; initialization event alone |
| Development fake camera + running session | 75.042 s | POST at 62.354 s; 90 bytes; harness-aborted | RUNNING; 75.210 active seconds; final observation age 0.357 s |
| Development with test-only worker CSP | 75.028 s | No external request reached routing | RUNNING; 75.175 active seconds; final observation age 0.395 s |
| Existing production build, fake camera | 75.057 s | POST at 63.906 s; 90 bytes; harness-aborted | 281 inference responses; final response age 314 ms |
| Existing production build, test-only worker CSP | 75.041 s | No external request reached routing | 274 inference responses; final response age 160 ms |
| Production worker CSP, explicit worker-side observer | 75.046 s | Metrics `fetch` at worker elapsed 60.369 s rejected with TypeError; enforced `connect-src` violation; no external request reached routing | 281 inference responses; final response age 239 ms |

The final observer attached a `securitypolicyviolation` listener inside the worker and wrapped `fetch` only to record its destination/method/outcome while forwarding the original arguments unchanged. Chrome reported `blockedURI: https://odml.pa.googleapis.com/v1/log`, `effectiveDirective: connect-src`, `disposition: enforce`. This establishes **attempted and CSP-blocked transmission**, rather than assuming an absent network event means collection stopped. Payloads were inspected only in harness-aborted baseline requests; the CSP-blocked body did not reach routing.

Across these cases: **collection enabled**; **baseline transmission attempted and harness-blocked**; **candidate-policy transmission attempted and CSP-blocked**; **successful transmission to Google not tested**. The final worker instrumentation demonstrates observability of worker activity that the page console did not report.

All captured endpoint requests used `POST https://odml.pa.googleapis.com/v1/log`. There were no page errors in these completed cases. Same-origin model/WASM loading and worker readiness succeeded in the active cases. Final Research Interest href remained `https://forms.gle/Jz6Wva2JEVHcomc36`. No form was submitted. The link's actual external page and administration were not tested; worker CSP does not govern parent-page navigation.

The development RUNNING tests used the existing development seam to set `session.gate.started = true` and task state to RUNNING after real fake-camera/MediaPipe initialization. Actual inference continued on the fake video; no landmarks or task results were forged into the worker. This tests a running application session across the flush boundary, not physical calibration, successful grasps or human tracking quality. Production has no development seam and remained in its normal fake-camera setup flow while inference ran.

The 39-byte body decodes to envelope constant 1786, common version `1.0.1`, worker platform 0, empty common strings, enum 4, task 10, event kind 0, mode 12 and integer initialization duration 3501 ms. The development 90-byte body contains initialization plus one performance event: average 289 ms, maximum 450 ms, interval 30180 ms, dropped count 0 and CPU input count 91. These are headless test measurements, not product performance benchmarks. They corroborate the static builder rather than suggesting any image content is present.

The first concurrent exploratory run stopped on a 30-second readiness timeout before reaching the flush boundary. It is excluded from successful runtime evidence. Sequential reruns above completed. A missing early request or that failed initial run must not be treated as a privacy pass.

### Test record and reproduction

[Sanitized machine-readable evidence](evidence/phase6_2_privacy.json) preserves durations, request methods/destinations, payload byte lengths/hashes and decoded wire fields, worker violations, inference counts, source hashes and assertions. It excludes API-key values, HTTP headers, raw frames and physical-user data.

The ignored audit scripts are `outputs/phase6_2/runtime.mjs`, `production.mjs`, `csp-proof.mjs` and `finalize.mjs`. From the repository root, the commands actually run were `node outputs/phase6_2/runtime.mjs`, `node outputs/phase6_2/production.mjs`, `node outputs/phase6_2/csp-proof.mjs` and `node outputs/phase6_2/finalize.mjs`; development was served with `pnpm dev` in `web`, and the pre-existing build with `pnpm preview`. Script SHA-256 values are recorded in the evidence. All browser contexts block external requests, including baseline; do not remove that guard when repeating this audit.

Final assertions passed for seven >70-second cases, expected request/block outcomes, parsed payloads, active inference/session evidence, research href preservation and zero page errors. All 95 source/scene hashes in the Phase 6 evidence still match. `git diff --check` passed. Application unit tests, TypeScript check and production build were **not rerun in Phase 6.2** because no application/dependency source changed; the existing production artifact was tested and its hash recorded. Earlier Phase 6 test counts must not be reported as new Phase 6.2 runs.

## Package notice and supported opt-out

The installed README, “Privacy Notice” (lines 212–227, dated June 5, 2026), distinguishes on-device input processing from performance/utilization metrics sent to Google. It assigns consent responsibilities to the application provider. The [official MediaPipe repository notice](https://github.com/google-ai-edge/mediapipe#privacy-notice) makes the same distinction. Package metadata declares Apache-2.0 and links the privacy notice; bundle comments contain license notices. No separate LICENSE file is present in the installed package's top-level directory, and no metrics configuration switch was identified in those notices. This phase does not reassess licensing.

No supported disable mechanism was found in the installed README, types, options handling or logger construction:

- `TaskRunnerOptions`: base options; no metrics flag.
- `BaseOptions`: model path/buffer and CPU/GPU delegate; no metrics flag.
- `VisionTaskOptions` and `HandLandmarkerOptions`: canvas, running mode and detection settings; no metrics flag.
- `FilesetResolver.forVisionTasks(basePath?, useModule?)`: asset/module resolution only.
- `TaskRunner.enableLogging(options)` is an initializer, not a boolean switch. No supported `disableLogging` API is exposed by this package.
- No environment flag or documented build-time opt-out was identified. Upstream's [TaskLogger interface](https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/mediapipe/tasks/web/core/task_logger.ts) contains a dummy implementation, but exposes no installed-package switch to select it. The referenced upstream factory implementation was not available at the inspected public path. A dummy class in upstream source is not evidence of a supported npm opt-out.

LapSim-AI passes no disabling option. Inventing one, omitting the API key or setting a prototype property would not be a verified opt-out.

## Version comparison, without installing

After finding no opt-out, the official npm distribution of 0.10.35 was inspected through [its JavaScript bundle](https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/vision_bundle.mjs) and [types](https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/vision.d.ts), saved only under ignored investigation output. Its JS bundle has no identified `odml.pa.googleapis.com` sender or this logger implementation. Types retain `HandLandmarker.createFromOptions`, `detectForVideo`, VIDEO mode, CPU delegate, canvas, numHands and the module-loader option used here.

This makes 0.10.35 a candidate for a separately approved compatibility/privacy evaluation, **not a verified replacement**. Matching JavaScript/WASM assets, model compatibility, initialization, physical tracking behavior, browser support and full-distribution network behavior still need validation. No dependency, lockfile or distributed asset was changed. No assertion is made about all older/newer versions.

The downloaded 0.10.35 JS SHA-256 is `55d7ab624fbb70dcc5adc4ae6d7ea9cfcb569139d3dbfbf2b1deafcb966bc0fe`. It also lacks `setInterval`, the `x-goog-api-key` header name and `_mediapipeLoggerGetEncodedApiKey` found in 1.0.1. This is a JS comparison, not a full old-version WASM/network audit.

## Network-policy candidate

The document currently has a meta CSP with same-origin `connect-src` (plus the development loopback WebSocket exception). A separately fetched worker has its own policy context. A restrictive document meta tag alone does not establish restrictions on its fetches. A CSP response header on the worker script is the relevant control; see [MDN worker CSP guidance](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers#content_security_policy).

Test-only worker response header:

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'self'
```

This is a candidate for deployment/server configuration, not an application change made here. It permits same-origin module/WASM/model loads and WASM compilation while rejecting the Google connection. Apply it to the actual worker response, including hashed production worker paths, on every serving environment. A report-only policy is insufficient. A host that cannot set worker response headers cannot provide this guarantee by copying the HTML meta tag. Verify redirects, caching, CDN responses, future subworkers and supported browser versions. Worker network restrictions do not govern the parent document's user-initiated external Research Interest navigation.

This approach prevents transmission when correctly enforced; it does **not** disable collection, timer execution or attempted `fetch`. It must not be advertised as “MediaPipe telemetry disabled.”

## Ranked remediation, pending maintainer approval

1. **PREFERRED: enforce a worker response CSP with same-origin connections.** This is the smallest candidate that preserves the installed inference implementation. Configure the local development/preview server and actual production host to cover worker responses, keeping required same-origin WASM/module permissions. Add an automated regression check beyond the logger interval and verify the real hosted response plus supported browsers. Do not rely only on the document policy or a successful localhost test. No server/deployment policy was changed here.
2. **ACCEPTABLE fallback: separately evaluate official 0.10.35 with matching WASM assets.** Its JS lacks the identified sender and its API surface appears compatible, but tracking behavior and full-distribution privacy have not been verified. A dependency change requires separate approval and broader validation.
3. **NOT RECOMMENDED as a fix for a no-cloud-metrics policy: disclosure alone.** Accurate disclosure is necessary now but does not prevent transmission or close the intended privacy blocker. Reconsidering that policy would be a separate maintainer decision.
4. **NOT RECOMMENDED: patch minified code/node_modules, replace private logger properties, swallow global fetch, remove the key, or terminate/recreate tracking before 60 seconds.** These are unsupported or invasive and can be brittle or change tracking behavior. The fetch observer used in one audit case only records calls and forwards them unchanged; it is not a proposed application mitigation.

A supported dependency opt-out would be preferable to a network block if one becomes available and is verified; none was found for the installed 1.0.1 package.

## Remaining unknowns and limits

- Whether Google accepts the request on an ordinary unblocked network; external sends were deliberately intercepted. CORS/preflight, network availability, browser transport headers and server retention/processing were not measured.
- Semantic names of common-context enum 4, envelope constant 1786 and the currently empty string fields. Numeric values and emptiness are established; meanings are not invented.
- Behavior of untested browsers, physical camera hardware, GPU inference, hosted CDN/cache policies, alternate MediaPipe tasks and future package versions.
- Full compatibility and WASM/network behavior of the uninstalled 0.10.35 candidate.
- No full decompilation or formal verification of the WASM/browser/network stack was performed. Conclusions about excluded payload categories follow the actual JS metrics builders and the application's input/output boundaries.
- The current browser UI still says `ON · LOCAL` and describes local camera processing. No UI source was changed under this investigation-only scope; any user-facing dependency-metrics disclosure or mitigation-specific wording requires the approved remediation step.

## Public wording for the current unmitigated build

> LapSim-AI processes webcam frames locally and does not upload webcam frames, hand landmarks, calibration data or training-session results. Its MediaPipe Tasks Vision 1.0.1 dependency separately collects initialization, performance and usage metrics and attempts to send them to Google. The current build has no verified dependency opt-out or deployed worker network restriction. The optional Research Interest form is separate and receives no automatic simulator results. Hosting providers may retain ordinary request logs.

The first four local-data statements are supported by separate application/logger data-flow evidence. “No third-party dependency metrics are transmitted” is **not supported for the current distribution**. Interception during an audit is not a deployed privacy feature.

## Scope and safety

Only privacy/release documentation and sanitized audit evidence are deliverables. Temporary scripts, package comparisons and logs live in ignored `outputs/phase6_2/`. Application source, controls, tracking, calibration, task mechanics, visuals and dependency versions are unchanged. No broad licensing work resumed. GitHub's read-only repository metadata confirmed `Mbjaradat/LapSim-AI` remains private. HEAD remains `244134707f511d1d943ccb910af58404c3316dda`. No commit, push, tag, release, deployment, repository visibility change, Zenodo operation or DOI creation was performed.

**One next action:** approve the worker-response CSP remediation and its deployment/browser validation before resuming Phase 6.1. Approval is needed because the Phase 6.2 instruction permits only a verified small dependency opt-out to be implemented automatically; this is a server/network policy change.
