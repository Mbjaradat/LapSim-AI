# MediaPipe worker network containment — Phase 6.2B

**PRIVACY BLOCKER RESOLVED LOCALLY — PRODUCTION CHECK PENDING.** Final review: 2026-09-12. No Vercel deployment or edge-response verification was performed.

The bundled MediaPipe Tasks Vision 1.0.1 logger collects internal usage/performance metrics and attempts a periodic POST to `https://odml.pa.googleapis.com/v1/log`. LapSim-AI contains that worker's external connections with an enforced browser CSP. Collection remains present; transmission is blocked when the configured response policy is served and enforced. See the [Phase 6.2 investigation](mediapipe_privacy_investigation.md) for payload and data-flow analysis.

## Configuration and coverage

`web/vercel.json` specifies a Vercel `headers` rule for `/assets/:path*`:

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'self'
```

The Vite build emits the actual module worker at `/assets/hand-worker-<hash>.js`. The directory rule survives content-hash changes and also covers future workers emitted into that directory. CSP on an ordinary imported JS/CSS asset does not replace the parent document's policy; on a worker entry response it governs the worker's own context. The document's existing meta CSP remains separate. No restrictive response header is added to the HTML by this change.

`web/vite.config.ts` reads the policy value from `vercel.json` and adds it through Vite's development and preview middleware to `/assets/` responses and the development entry `/src/hand-worker.ts` (including its worker query string). Local preview therefore exercises a real served header, rather than test-harness header injection. This middleware is local configuration, not a newly deployed server or proxy. Vercel serves the static build with its own configured headers.

Same-origin JS, WASM and model fetches remain permitted; `wasm-unsafe-eval` permits WASM compilation. The Research Interest link is user-initiated navigation in the parent page, not a worker connection, and retains its separate `_blank`/`noreferrer` behavior. The model, MediaPipe version, simulator source and tracking logic are unchanged.

## Vercel project setup

Use **Root Directory `web`**, Vite, build command `pnpm build`, output directory `dist`. Keep the parent repository assets available during the build: the existing asset preparation script reads `assets/third_party/mediapipe_hand_landmarker` outside `web`. Enable inclusion of source files outside the Root Directory for that build. Publish only `web/dist`, not the parent repository or ignored audit outputs.

Vercel loads `vercel.json` from the configured project root and supports response headers matched by source paths. See [Vercel configuration documentation](https://vercel.com/docs/project-configuration/vercel-json#headers). The dashboard configuration and actual Vercel edge response must still be verified; this phase does not deploy or change account settings. Merely serving `dist` with an arbitrary static server does not install the CSP. Other hosts must implement the equivalent worker response header.

## Repeatable local verification

### Completed evidence

The saved production-preview test completed successfully before interruption and was inspected, not rerun, on continuation. Its 80.056-second observation recorded the actual `/assets/hand-worker-CFdBzOHs.js` response with HTTP 200 and the approved CSP. WASM and model responses were HTTP 200. At worker elapsed 61.010 seconds, the logger attempted its POST; `fetch` rejected with TypeError and the worker recorded an enforced `connect-src` violation for the endpoint. No external request reached the harness's fallback abort guard. There were 333 inference responses at the end of the window and 340 after the additional continuation check. No page errors or unexpected worker policy violations were recorded.

The production Beginner Free Transfer setup displayed its two-minute/first-grasp timer. Fake-video inference and camera initialization passed; blank fake input does not validate human hand calibration quality. The already completed 36 web unit tests included guided calibration and Beginner Free Transfer progression. TypeScript and the final production build passed. The remaining production browser smoke completed with nine checks and zero page errors (camera lifecycle, local inference, landing/scene, link configuration, refresh, narrow-layout guidance, permission denial and missing-camera behavior). Its first attempt after interruption found the preview server stopped; it was rerun only after restarting that server. The timed containment test was not repeated.

All 95 source/scene hashes recorded in Phase 6 still match. Simulator/control/task source, dependency manifests/lockfile and MediaPipe 1.0.1 are unchanged. No native files changed and no Blender/native suite was rerun. `git diff --check` passed. See [sanitized Phase 6.2B evidence](evidence/phase6_2b_containment.json).

### Commands

From `web`, run the web tests, typecheck and build, then start `pnpm preview`. In a separate terminal:

```powershell
$env:TEST_CHROME_PATH = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:TEST_BASE_URL = 'http://127.0.0.1:4173'
node scripts/privacy-network.mjs
```

Omit `TEST_CHROME_PATH` when using Playwright's installed Chromium. The test observes fake-camera inference for 80 seconds after readiness and confirms further inference after that window. It reads the actual worker response header, observes the worker's metrics fetch and enforced CSP violation, and checks successful same-origin WASM/model loads. It never injects headers. An external-request abort guard prevents accidental transmission if the policy regresses; reaching that guard **fails** the test and is not accepted as CSP containment. No API keys, HTTP headers containing credentials, frames or landmark coordinates are retained in its report.

Results are written to ignored `outputs/phase6_2b/production.json` (or `development.json` for port 5173). Running against `pnpm dev` with port 5173 verifies the development worker route separately.

## Required Vercel post-deployment check

This is a **PRE-PUBLICATION human verification item**, not completed by a localhost test:

1. On the intended HTTPS production URL, open DevTools Network before Start Training. Use a fresh page/cache state and preserve the log. Locate the actual hashed `hand-worker-*.js` request and confirm its **response** contains the enforced CSP above, not only a report-only policy or the HTML meta policy.
2. Confirm same-origin model/WASM responses succeed, guided setup initializes, Beginner Free Transfer loads and webcam inference runs. Keep the tab visible for **more than 75 seconds after initialization**.
3. At the logger interval, confirm the `odml.pa.googleapis.com/v1/log` attempt is blocked by `connect-src`/CSP, with no successful external request/Google response. Confirm inference continues after the block and no required local resource is blocked. An unexplained absence of requests alone is insufficient evidence.
4. Verify the Research Interest link opens through the ordinary user action, with no automatically attached simulator results; do not submit the form as part of this check. Record deployed commit/build, actual worker URL, browser/version, duration and outcomes. Repeat for supported browsers and any custom domain/CDN path.

The automated command above can additionally target the deployed origin using `TEST_BASE_URL`; it must still pass with zero external requests reaching its guard. Deployment protection or toolbar injections can make that check fail and must not be mistaken for proof that the worker header is absent. Inspect the actual worker and distinguish unrelated host requests. Do not export unsanitized HAR files, camera content or credentials.

## Maintenance and privacy semantics

Repeat the >75-second privacy check after **every MediaPipe upgrade**, worker filename/location change, Vite worker-output change, hosting/CDN/header change or supported-browser change. If workers move outside `/assets/`, update both production and local coverage. Do not weaken `connect-src` to permit Google or `*`. A report-only policy does not block transmission.

The supported statement is that the configured CSP blocks the tested dependency's external metrics transmission. It does not mean collection is disabled, the dependency has no telemetry code, no network communication occurs, or Google can never receive information in every possible environment. Normal same-origin hosting requests and the optional external form are separate boundaries.

Repository privacy was confirmed through read-only GitHub metadata. No commit, push, tag, GitHub Release, Vercel deployment, Zenodo publication or DOI creation occurred. The broader Phase 6.1 licensing audit was not resumed.
