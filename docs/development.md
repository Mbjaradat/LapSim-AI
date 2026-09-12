# Development and reproducibility — Research Preview

Phase 6 reference environment: Windows, Python 3.12.10 in the standalone `.venv`, Blender 5.2.1 LTS (bundled Python separate), Node 24.19.0, pnpm 11.19.0. This records the tested environment, not cross-platform certification. Python project metadata allows >=3.11, but the native webcam workflow is currently Windows-specific and tested with 3.12.10. Pure Python tests do not require a webcam or third-party imports.

## Browser

Prerequisites from `web/package.json`: Node >=22.12.0, pnpm 11.19.0. Runtime pins: Three.js 0.186.0 and MediaPipe Tasks Vision 1.0.1; dev versions and transitive resolution are in `web/pnpm-lock.yaml`.

```powershell
cd web
pnpm install --frozen-lockfile
pnpm dev
```

Open `http://127.0.0.1:5173`. A full checkout is necessary: `scripts/assets.mjs` verifies/copies the model from `../assets/third_party/mediapipe_hand_landmarker`, copies package WASM and generates runtime notices. There is no runtime CDN download. Do not commit generated `web/public`, `web/dist` or `node_modules`.

```powershell
pnpm test
pnpm typecheck
pnpm build
pnpm preview
```

Preview is `http://127.0.0.1:4173`. Serve the complete `web/dist` over HTTPS for production, including `models`, `wasm`, and `licenses`. Camera access requires permission and a secure context (HTTPS or localhost). Desktop viewport >=900 px, WebGL2, workers, OffscreenCanvas and ImageBitmap support are expected. Chrome was exercised headlessly; broader physical browser/device support is not established. Start requests video only; choose another camera while stopped.

For headless smoke tests, leave the relevant server running in another terminal:

```powershell
# Use an existing Chrome installation; adjust path for your machine.
$env:TEST_CHROME_PATH = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$env:TEST_BASE_URL = 'http://127.0.0.1:5173'
pnpm test:browser
$env:TEST_BASE_URL = 'http://127.0.0.1:4173'
pnpm test:browser
```

Alternatively install the matching Playwright Chromium (`pnpm exec playwright install chromium`) and omit the executable override. Tests use a fake camera, synthetic hand/task states and software WebGL. They cannot substitute for physical acceptance. Outputs are under ignored `outputs/web/`. `physicalWebcamValidation:PENDING` in that script means the automated harness never conducts a physical test; see the separate maintainer observation in release evidence.

`VITE_RESEARCH_INTEREST_URL` defaults to the supplied HTTPS Google Form. Unset uses default; empty/invalid disables it. Never put secrets in VITE variables: they are public build-time values. See `web/.env.example`.

## Native Python and Blender

Use a standalone Python 3.12 installation, not Blender's Python, for webcam dependencies. From repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-native.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

If `py` is unavailable, replace it with the full path to standalone Python. `requirements-native.txt` is an exact installed-version snapshot from this Windows reference environment, without wheel hashes; a fresh download/install was not performed in Phase 6. Availability of those wheels on another OS is not asserted. `pyproject.toml` is lightweight project metadata, not a complete webcam installer; follow this explicit environment workflow. Do not install third-party packages into Blender's bundled Python.

The unchanged model is `assets/third_party/mediapipe_hand_landmarker/hand_landmarker.task`, SHA-256 `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1`. Its SOURCE.json records source/license evidence. Use that exact version/checksum; the upstream `latest` URL is not a reproducible version pin. Verify with `Get-FileHash -Algorithm SHA256` after retrieval if the file is missing.

Open `blender/scenes/lapsim_ai_peg_transfer.blend` in Blender 5.2.1 LTS. In its Text Editor open `blender/scripts/start_webcam.py`, run Alt+P, hover the simulator viewport and use F3 → **LapSim: Start Webcam Control**. Arrange the separate OpenCV preview beside Blender. The worker currently launches `.venv/Scripts/python.exe`; Linux/macOS native launch is not claimed supported.

Follow HOME/OPEN/PINCH holds, return near HOME, then wait for the automatic five-second LIVE gate. Space pauses/resumes; focus loss safety-pauses; R retries preserving calibration; after releasing held rings, pause then Backspace to recalibrate. Esc in Blender or Q/Esc in the preview stops. New worker sessions recalibrate. See [native Phase 5 workflow](phase5.md) for complete acceptance steps.

Keyboard fallback is the separate `blender/scripts/start_live.py` registration and **LapSim: Start Keyboard Control** operator. Bindings are authoritative in `control/keyboard.py`: left W/S pitch, A/D yaw, Q/E insertion, Z/X roll, F/G jaw; right arrows pitch/yaw, PageUp/PageDown insertion, N/M roll, J/K jaw. Do not confuse preview Q (quit) with Blender keyboard Q (insert). See [native controls](phase2d.md).

```powershell
$blenderExe = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
& $blenderExe --background --factory-startup --python-exit-code 1 --python blender/scripts/verify_peg_transfer.py
& $blenderExe --background --factory-startup --python-exit-code 1 --python blender/scripts/verify_phase5.py
```

The peg verifier loads the saved scene, checks mechanics/interactions and regenerates the scene in memory to compare a deterministic fingerprint. To intentionally rebuild the distributable scene separately, use `blender/scripts/build_peg_transfer.py`; review any binary change before committing. Older phase builders/verifiers reproduce their own historical checkpoints, not beginner browser behavior.

Fixture refresh from root:

```powershell
.\.venv\Scripts\python.exe web/scripts/generate_fixtures.py
```

Review fixture changes, then rerun browser parity tests. Physical calibration/comfort, real camera identity, device performance and public deployed links remain manual. No accounts, server, clinical dataset or research participant data are required for these engineering checks.

## Release hygiene

Use a reviewed Git source archive, never a ZIP of the whole working directory. `.venv`, dependency folders, outputs, caches, local environment files and downloads are excluded. Main `.blend` sources and third-party model/anatomy files are intentional tracked assets with component terms recorded in the licensing audit. The unrelated `forcing-vs-convincing/` scaffold was removed in Phase 6.3. See [audit findings](release_audit.md) and [release checklist](release_checklist.md).
