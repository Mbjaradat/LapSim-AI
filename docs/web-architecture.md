# Browser MVP architecture decision (before implementation)

Audit: native reference commit 922fdc0. Python modules under src/lapsim_ai separate
instrument/controller, hand geometry/stabilization, Phase 5 setup/runtime,
collision/containment, grasp/Peg Transfer and Phase 4 telemetry from bpy adapters.
Blender config/peg_config define metres, degrees, board, rings and camera. Scene
provenance is original procedural geometry; anatomy assets are unrelated and excluded.
94 native tests and four relevant headless scripts form the regression baseline.
Native physical webcam comfort remains unvalidated.

Decision: additive web/ with TypeScript + Vite static build + Three.js WebGL2.
No React (one imperative high-frequency working surface), backend, Python runtime,
Blender streaming, database, accounts, analytics or persistence. MediaPipe Tasks
Vision runs locally in a worker with one in-flight mirrored ImageBitmap; model
and WASM served from the same origin, pinned locally. Render cadence uses RAF,
tracking is capped at 30 Hz, status updates at 10 Hz. Camera requires user action.

Parity contract: Z up; metres; angles in degrees; Ry(yaw) Rx(pitch) Rz(roll);
fixed pivots (+/-0.085,0,0.12), insertion along local -Z; exact native joint
bounds and bounded rates. Physical left/right use the existing mirrored detector
identity correction. Palm-center steering, apparent scale insertion, transported
palm twist, calibrated pinch remain separate. Port median atomic calibration,
EMA/deadbands, 0.5 s freshness, HOME radius .065, .75+3 s holds and 5 s LIVE gate.

Port deterministic capsule sweep/axis projection and camera/board inward planes;
use native camera position, target, sensor/lens and fixed 4:3 optical frame,
letterboxed inside responsive viewport so resize cannot alter containment.
Port exclusive ownership, offset-preserving grasp, armed handoff, occupied-peg
checks, drop/placement/completion. Observe accepted shaft references with Phase 4
0.5 mm path anchors, first-grasp active time, pause exclusion and bounded histories.

Before comparing JS outputs, generate small JSON fixtures by executing Python
reference functions: mapping, poses, planes, collision cases, task sequences,
telemetry histories and calibration observations. Regeneration does not change
native source. Numerical tolerances: 1e-9 ordinary math, 1e-6 m pivot/geometry.
Add browser synthetic input seam only in development/test builds; no UI shortcut
may directly assign task completion. Test actual deterministic updates.

Visual thesis: a restrained surgical research workbench. Slate trainer surface,
ivory rings, teal source markings, amber targets, clear typography, white status
sidebar. Simulator receives about 77% width, integrated mirrored camera 23%.
Small screens get a desktop-use message. Results occupy their own region.

Licensing: original project license is not finalized; do not assert an Apache
license for original code. Reuse the recorded model checksum/license and include
runtime dependency notices. No third-party anatomy/assets or native bpy scripts
are shipped. Manual review and distribution licensing remain separate from tests.
No commit, push, external accounts, credentials or deployment are authorized.
