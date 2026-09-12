# Privacy and research-interest boundaries

**Phase 6.2B: PRIVACY BLOCKER RESOLVED LOCALLY — PRODUCTION CHECK PENDING.** Worker-response CSP containment is implemented and verified in production preview. Internal metrics collection remains present. The actual Vercel response and >75-second runtime check remain required before publication. See [containment](worker_network_containment.md) and the historical [investigation](mediapipe_privacy_investigation.md).

Audit date: 2026-09-11. Scope: current browser source, built asset preparation and headless development/production smoke scenarios. This is not an audit of hosting providers, browser extensions, operating-system camera services or Google's form administration.

## Verified simulator behavior

- `app.ts` requests video only after Start Training. Frames are drawn to a mirrored canvas and transferred transiently to a local worker. `hand-worker.ts` detects locally and closes ImageBitmaps.
- No MediaRecorder, recording/export path, frame persistence, frame upload, sendBeacon, simulator WebSocket client, or localStorage/sessionStorage/IndexedDB use was found in application source. The imported MediaPipe dependency does include a metrics collector and external sender; application-source-only inspection does not exclude dependency metrics.
- Calibration, landmarks, task events and results are held in page/worker memory. Camera labels/device IDs populate the selector in memory. No user account is implemented.
- Stop/page exit ends media tracks and terminates the worker. Hidden tabs pause the session and stop capture while hidden; hiding a tab does not itself stop the camera stream. Resume is explicit.
- Model/WASM are copied locally by `assets.mjs`. Historical Phase 6 short smoke tests observed same-origin GET assets only. Phase 6.2 crossed the 60-second logger boundary and observed the dependency POST attempt; the short tests cannot support a no-metrics claim.
- Development Vite retains local hot reload. The document meta CSP is separate from worker policy. `web/vite.config.ts` now serves the approved worker response header locally, using the value in `web/vercel.json`; Vercel configuration applies it to `/assets/:path*`. Local production-preview enforcement passed; actual Vercel verification is pending.
- Browser results are not automatically transmitted to the research form. Its link opens only through a separate user action, in a new tab with `rel=noreferrer`, without simulator parameters.

The native implementation is different: local OpenCV preview and token-checked loopback UDP carry commands/status, not video. Native result JSON is stored in Blender scene properties; users could save that state in a scene. The browser's in-memory statement must not be generalized to all native saves.

## Public wording

LapSim-AI processes webcam frames locally and does not upload webcam frames, hand landmarks, calibration data or training-session results. MediaPipe Tasks Vision performs hand-landmark inference locally. The bundled dependency contains internal usage/performance metrics logic; LapSim-AI applies a browser Content Security Policy to prevent the worker from transmitting metrics to its external metrics endpoint. This blocks transmission, not internal collection, when the configured response policy is served and enforced. The optional Research Interest form is separate and receives no automatic simulator results. Hosting providers may retain ordinary request logs.

The reviewed metrics builders receive counters and timing values, not frames, landmarks, calibration or simulator results. Phase 6.2B verified an attempted POST rejected by enforced worker `connect-src`, with no external request reaching the harness guard and continued inference. This evidence applies to the configured local production preview, not every host or browser. The deployment check remains mandatory.

## Research interest registry

Configured default: [Research Interest List](https://forms.gle/Jz6Wva2JEVHcomc36), matching `web/src/config.ts` and `.env.example`. The HTTPS-only URL validator permits an explicit build-time override; deployed configuration must be checked separately. The short URL could not be fetched by the Phase 6 web tool. Link wiring was tested, but actual form contents, sign-in requirements, recipients and response permissions are **NOT VERIFIED**.

Current site wording correctly separates joining an interest list from study enrollment. Recommended form/public wording:

> Help Shape the Future of LapSim-AI. Interested in participating in future research, testing the simulator, or collaborating with the project? Join the Research Interest List. Joining the interest list does not enroll you in a research study.

This is an interest/contact registry, not informed consent, ethics approval, trial recruitment acceptance or automatic study participation. Joining is voluntary. Future studies require a separate protocol, applicable ethics review, participant information, eligibility/data-handling information and informed consent. Training effectiveness and construct/predictive validity are not established. Do not submit medical or sensitive personal information.

## Maintainer form review before launch

Suggested minimal fields, subject to actual contact needs:

| Group | Suggested fields/options |
| --- | --- |
| About you | Full name, email, country of residence, role/career level |
| Role | Medical student; Intern/Foundation doctor; Resident/Specialty trainee; Fellow; Surgeon/Attending/Consultant; Other physician; Researcher; Engineer/Developer; Other healthcare professional; Other |
| Experience | Laparoscopic experience; previous physical/virtual simulator use; previously tried LapSim-AI |
| Interests | Future studies; usability testing; technical/beta testing; skills-training studies; comparisons with other training methods; feedback; research collaboration; software collaboration; major project updates |
| Practical | Access to desktop/laptop with webcam; willingness for remote testing if eligible; possible in-person research interest |

Avoid unnecessary required questions. No file uploads, DOB, medical history, institution ID or sex unless a future approved protocol specifically justifies it. Avoid unnecessary forced Google sign-in. Do not attach simulator metrics or calibration data. Restrict responses to the small appropriate project/research team. Provide a named contact/removal-request mechanism and retention/access information before formal launch. Interest responses must not become a research dataset by default. No form settings or responses were changed or submitted in Phase 6.
