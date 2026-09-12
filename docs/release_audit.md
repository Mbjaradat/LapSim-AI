# Release audit — Phase 6 record with resumed Phase 6.1 findings

Base commit inspected: `244134707f511d1d943ccb910af58404c3316dda`. Initial working tree was clean. Remote configuration is `https://github.com/Mbjaradat/LapSim-AI.git`; remote freshness/public visibility was not changed or confirmed. No applicable AGENTS.md was found in the repository. The audit inspected 157 tracked entries before Phase 6 additions, including five `.blend` scenes, native/browser source, tests, metadata, lockfiles, model and anatomy provenance.

## Distribution findings

| Finding | Disposition |
| --- | --- |
| Original source/assets license and attribution | RESOLVED: canonical Apache-2.0; creator/holder Mohammad Jaradat, 2026, expressly confirmed |
| Blender API integration | RESOLVED: original Apache-2.0 scripts are GPLv3-compatible; Blender GPL-3.0-or-later installed separately; no Blender binary/copied GPL source found |
| Independent scaffold | REMOVED after dependency recheck and maintainer authorization; no trainer relationship |
| MediaPipe JS/WASM | RESOLVED: official npm package Apache-2.0, exact hashes/integrity and Google/Closure/upstream notices retained |
| Historical SPL anatomy | CLEAR for public repository with existing full terms/preface/attribution/modification record; excluded from minimal artifact |
| Creator and copyright | RESOLVED by maintainer confirmation: Mohammad Jaradat, 2026; CFF updated |
| Research form default matches supplied URL | Local wiring verified; hosted contents/settings/contact/removal mechanism not verified |
| `.venv`, `node_modules`, build/public output, caches, downloads, screenshots | Ignored, not tracked; exclude from release archives |
| `H/` and four oddly named root directories containing `.thumbnails` directory trees | Empty directory scaffolding observed, no tracked files; retained unchanged, do not include a working-directory ZIP |
| Historic documentation reports earlier pending/manual status | Labeled as historical and linked to current evidence; native physical acceptance remains separately pending |
| Explicit premature Stop Camera metadata | Internal beginner result can retain generic structured task labels; documented technical limitation, normal timed workflow unaffected; no runtime fix made |

## Secrets/configuration scan scope

A read-only heuristic scan covered all 141 UTF-8 tracked text files (before new Phase 6 files), looking for private-key headers, GitHub/AWS/API-key patterns, quoted secret assignments, credential-bearing URLs and personal absolute paths. No candidate credential was found. The single path-pattern hit was the prose `setup/HOME/LIVE` in `docs/web-mvp.md`, a false positive for `/home/`, not a local path. Review also used `git grep` for passwords/credentials/tokens and inspection of `web/.env.example`, native loopback tokens and `.npmrc`. The native random bridge token is generated per worker, not a committed credential. The `.npmrc` contains only `node-linker=hoisted`.

No tracked `.env` secrets, private-key files, node_modules, build output, virtual environments, screenshots or video were found. Source URLs are dependency/provenance links, configured GitHub/form links and documented localhost examples. Developer instructions use illustrative system install paths, not private user paths. No actual production site URL was established.

This scan is not a full Git-history secret scanner, entropy analysis or binary forensic audit. Git history and remote hosting settings were not certified. Maintainer must inspect final staged changes and history exposure before changing repository visibility. New Phase 6 documents contain no credentials; public links and copied evidence are intended metadata.

Useful repeat commands (repository root):

```powershell
git status --short --ignored
git ls-files
git diff --check
git grep -n -I -E 'api[_-]?key|password|credential|Bearer |BEGIN .*PRIVATE KEY|ghp_' -- .
```

Review matching content locally; do not publish secret values if found. `.gitignore` already covers local env files, credentials, recordings, datasets, caches and Blender backups. The browser ignore file excludes its node_modules/output. Phase 6.3 removed only the confirmed unrelated scaffold and its ignored local install.

## Saved-scene and asset inspection

Headless Blender loaded all five tracked scenes without saving them. No images, external linked libraries, sensitive-property candidates or session/telemetry properties were found in that inventory. Peg Transfer uses an unpacked built-in font. START_HERE text blocks have no external file paths. Phase 3B contains its embedded third-party anatomy license. The inventory is preserved in `docs/evidence/phase6_checks.json`; it does not prove every binary byte is free of metadata.

The MediaPipe model and all ten VTK source files matched SOURCE.json SHA-256 values. Native peg verification confirmed historical scene hashes remained unchanged and deterministic regeneration matched. No binary asset was modified. Ignored screenshot/output material was not admitted to the release; it would need separate visual/privacy approval if later added.

## Privacy and publication boundaries

Source inspection supports local frames, landmarks, calibration and simulator results. Phase 6.2B implemented worker-response CSP and verified an 80.056-second production-preview run: the metrics POST was CSP-blocked and inference continued. Actual Vercel verification remains a pre-publication requirement. See [containment](worker_network_containment.md) and [privacy](privacy_research.md). Form administration, host access logs and browser extensions remain outside this audit.

All publication actions remain manual. No commit, push, tag, GitHub Release, deployment, Zenodo upload or DOI creation occurred. The technical contribution is documented without ownership, novelty, patentability or clinical-effectiveness claims.

## Phase 6.3 conclusion — 2026-09-12

**READY AFTER MANUAL PRE-PUBLICATION CHECKS.** Distribution treatment is recorded in [licensing](licensing.md) and the two [explicit inventories](release_inventory.md). Original ownership/attribution, Blender native source/scenes, release-specific MediaPipe notices, anatomy scope and scaffold disposition are resolved. Form administration and actual private Vercel production verification remain manual gates. MediaPipe privacy is **RESOLVED LOCALLY — VERCEL PRODUCTION CHECK PENDING**. Engineering suites were not repeated because simulator/control/task behavior source did not change.
