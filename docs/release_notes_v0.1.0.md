# Draft release notes — do not publish until checklist is cleared

Tag: `v0.1.0`  
Title: **LapSim-AI v0.1.0 — Research Preview**  
Date: YYYY-MM-DD (maintainer to finalize)

LapSim-AI is experimental webcam-controlled virtual laparoscopic practice software intended for open-source educational/research release. This release records two implementations: a native Python/MediaPipe/Blender research reference and a client-side TypeScript/Vite/Three.js/MediaPipe browser application. The browser is a native web implementation, not streamed Blender.

## Included behavior

- Single ordinary RGB webcam input, physical-hand routing, per-hand HOME/OPEN/PINCH calibration and five-second HOME-gated LIVE countdown.
- Separate palm-center steering, apparent-palm-scale insertion, palm-frame roll and thumb–index jaw channels, with temporal filtering and bounded motion.
- Fixed virtual trocar pivots, instrument transforms, deterministic collision/workspace constraints and ring interactions.
- Public Beginner Free Transfer: either hand, any available ring, any valid target; no mandatory handoff or number matching; 120 active seconds from first successful grasp; success confirmation and safe deterministic recycling.
- Internal structured six-ring Peg Transfer architecture and native engineering checkpoints.
- Descriptive time, transfer/event counts and accepted instrument paths, persistent results and explicit retry.

## Engineering evidence

Phase 6 reruns: 36 web tests and 94 native Python tests passed; TypeScript check and production build passed. Development browser smoke: 12 checks; production: 9 checks, both with a fake camera and no page errors. Blender Peg Transfer and guided modal setup checks passed. Reconstructed browser pivot maximum was 1.3877787807814457e-17 m across 486 generated poses; native Peg Transfer pivot maximum was 1.5359765386647212e-08 m. Both are numerical constraint checks, not clinical validation. See [full release evidence](release_evidence_v0.1.0.md).

The maintainer reports a physical browser usability test with a positive overall impression. Hardware/browser/date details and quantitative outcomes were not supplied; it is a qualitative observation, not a controlled study. Native physical acceptance and wider hardware/browser testing remain separate.

## Use and limitations

See the root README and [development instructions](development.md). Browser development requires Node >=22.12.0 and pnpm 11.19.0, a webcam, WebGL2 and HTTPS/localhost. Native reference uses the recorded Windows Python 3.12.10 environment and Blender 5.2.1 LTS. No verified production URL is supplied in these notes.

Insertion is calibration-relative monocular control, not metric physical depth measurement. Lighting, pose, framing, occlusion, identity and device performance affect tracking. There are no haptics or full rigid-body/tissue physics. Tracking loss holds tools but continues active time; explicitly pause when needed.

Beginner Free Transfer is not official FLS Peg Transfer and is not a validated competence/proficiency assessment. No composite skill score exists. Clinical, construct and predictive validity and training effectiveness are not established. LapSim-AI is not a certified medical device, supervised-training replacement, patient-care tool or clinical decision-support tool.

## Privacy, interest and citation

LapSim-AI processes webcam frames locally and does not upload webcam frames, hand landmarks, calibration data or training-session results. MediaPipe Tasks Vision performs hand-landmark inference locally. The bundled dependency contains internal usage/performance metrics logic; LapSim-AI applies a browser Content Security Policy to prevent the worker from transmitting metrics to its external metrics endpoint. This blocks transmission, not internal collection, when the configured response policy is served and enforced. The optional Research Interest form is separate and receives no automatic simulator results. Hosting providers may retain ordinary request logs. **Local containment verified; Vercel production check pending.** See [containment](worker_network_containment.md). Research Interest remains voluntary contact interest, not study enrollment or informed consent; verify form settings before publication.

Cite Mohammad Jaradat and version 0.1.0 using CITATION.cff. Original-material license: Apache-2.0. Release date and DOI remain unset until actual publication; creator/holder/year were confirmed by the maintainer.

## License and acknowledgements

**Release status:** distribution licensing treatment is complete. Original source and original procedural assets are Apache-2.0, copyright 2026 Mohammad Jaradat. MediaPipe and Blender component treatment is recorded, and historical SPL/Phase 3B anatomy is excluded from the minimal artifact while retaining its terms in the repository. Google Form administration, private Vercel deployment/production CSP test and final content/date review remain manual pre-publication checks. See docs/licensing.md and docs/release_inventory.md.

Special thanks to Ahmad Jaradat for generously providing access to his high-performance laptop, which supported the development, testing, and validation of LapSim-AI.

This credits equipment support, not software or scientific authorship. See AUTHORS.md and the [manual release checklist](release_checklist.md).
