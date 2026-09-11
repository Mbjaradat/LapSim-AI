# Beginner Free Transfer polish

The public default is now **Beginner Free Transfer**, replacing the structured
six-ring completion rule in the public UI. The original `PegTransfer` and default
`Session()` structured mode remain intact internally for parity tests/future
Advanced mode. No public mode selector or native change was needed.

Practice lasts 120 active seconds from the first grasp. Calibration, ready countdown,
waiting before the first grasp and pauses consume no practice time. Live tracking
loss continues the timer, preserving existing active-time semantics. Either hand
can move any ring onto any unoccupied target, without matching or handoff. Source
returns and drops do not count. A successful release adds one transfer and lights
the receiving target green.

After 1.2 active simulation seconds, the ring returns to the first free source in
stable name order. Recycling waits if rings/tool contacts obstruct the source or
if a tool is near the confirmed ring; regrasp cancels recycling. Held rings are
never recycled. At expiry interaction freezes, including any held object, and the
results snapshot is fixed. Try again clears objects, recycling, counts, time and
telemetry while retaining valid calibration/HOME and repeating the ready countdown.

Results emphasize Successful Transfers, plus Time, Grasps, Drops, Handoffs and
left/right/total accepted instrument path. These describe practice, not surgical
competence. Procedural metallic shafts, tapered opposing jaws, hinge pins, collars
and small groove details replace cylinder-only visuals. Jaw animation and roll
follow the native poses. One 1024-pixel shadow map and revised board/ring materials
improve depth readability; no external model, texture, post-processing or physics
dependency was added. Collision proxies and gameplay coordinates are unchanged.

Research Interest defaults to the provided Google Form through `web/src/config.ts`.
`VITE_RESEARCH_INTEREST_URL` remains an optional override (an explicit empty value
disables the link). The URL opens with `target=_blank`, `rel=noreferrer`, with no
session/query data appended. No automatic navigation, form submission or enrollment
occurs. Local camera privacy and the experimental disclaimer remain unchanged.

Changed: `beginner.ts` and its focused tests; `session.ts`; `grasper.ts` and
`renderer.ts`; `app.ts`, `index.html`, `style.css`; `config.ts`, `.env.example`;
browser smoke checks and documentation. Mechanics, tracking, calibration, native
task, accepted-motion telemetry implementation and native files are untouched.

Validation: 36 web tests PASS (29 preserved + 7 focused), TypeScript and production
build PASS; 94 native tests PASS. Prior Blender validations remain the baseline;
they were not repeated because no native code/scene changed. Browser screenshots
and synthetic results checks are local evidence; physical webcam acceptance remains
PENDING. Hardware frame rate and the refined visual/collision feel need manual review.

Development headless browser smoke: 12 checks PASS, including the preserved
structured synthetic trial and Beginner results/Retry. Screenshots were inspected.
The synthetic camera check does not validate physical hand tracking. Final verdict:
**READY FOR BEGINNER MODE MANUAL VALIDATION**. No commit, push or deployment.

Short manual check: open the app and inspect the new graspers/scene; calibrate and
enter LIVE; grasp any ring with either hand and place it on a different-numbered
target; confirm +1, green confirmation and safe recycling; repeat, then drop a
ring and confirm no increment; verify the timer began at the first grasp and ends
at two active minutes; inspect results; Try again and confirm clean reset with
retained HOME; open Research Interest and verify the intended Google Form.
