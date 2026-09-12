# Archival and citation readiness

Target tag: `v0.1.0`. GitHub and Zenodo title: **LapSim-AI v0.1.0 — Research Preview**. This is preparation only: no tag, release, upload, archive or DOI has been created.

## Metadata worksheet

| Field | Prepared value / status |
| --- | --- |
| Title | LapSim-AI v0.1.0 — Research Preview |
| Resource type | Software |
| Version | 0.1.0 |
| Creators | Mohammad Jaradat, explicitly confirmed by maintainer on 2026-09-12 |
| Description | Experimental single-RGB-webcam virtual laparoscopic practice software combining per-hand calibration, separated motion channels, apparent-scale insertion control, fixed-trocar kinematics, deterministic interactions and descriptive telemetry. Includes native Python/Blender reference and browser TypeScript/Three.js implementation; browser default is Beginner Free Transfer. Clinical validity and training effectiveness are not established. |
| License | Apache-2.0 for original maintainer-owned material, copyright 2026 Mohammad Jaradat. Third-party/derived components retain their terms; native combined scope and binary notice review remain |
| Keywords | laparoscopic simulation; surgical simulation; hand tracking; computer vision; webcam; medical education; MediaPipe; Three.js; Blender; add open-source software only once license grant is finalized |
| Related repository | https://github.com/Mbjaradat/LapSim-AI |
| Release date | YYYY-MM-DD — not finalized |
| DOI | Pending archival publication; omit machine DOI fields |

No ORCID, affiliation or institutional endorsement is inferred. Rights holder/year were explicitly confirmed: Mohammad Jaradat, 2026. Equipment support remains an acknowledgement, not creator attribution.

## CITATION.cff

CITATION.cff uses CFF 1.2.0, confirmed creator Mohammad Jaradat, version 0.1.0 and Apache-2.0 for original work. Actual release date and DOI remain omitted. No affiliation/ORCID is invented. New schema validation is recorded in evidence/phase6_1_release_checks.json. The archive must match the [inventory](release_inventory.md); citation metadata is not a blanket third-party license grant.

## Manual sequence after blockers are resolved

1. Use the confirmed creator/original-material license. Resolve the remaining component/scope checks in the release checklist, inspect the actual legal artifact, and complete the private Vercel deployment check before public release. Finalize the actual release date and source diff.
2. Commit and push the reviewed preparation manually. Review the exact commit again, then create the annotated `v0.1.0` tag and GitHub Release using the prepared release notes. These publication actions are not performed by the assistant.
3. Choose an archival route. For Zenodo/GitHub integration, enable the intended repository before the release event according to Zenodo's current instructions; if a release already exists, follow the supported archive workflow or manually upload a reviewed source archive. Check what files will be archived, especially historical anatomy and the unrelated scaffold. Do not upload the full local working directory.
4. Populate the worksheet's confirmed values, select software as the resource type, verify included source/notices and publish only after final review. Archive version 0.1.0, not a moving branch or local dataset. No participant or webcam data belongs in this archive.
5. After publication, verify the minted record and DOI resolve to the intended version and files. Add the actual version DOI to citation/release documentation if desired. Distinguish a version-specific DOI from a concept DOI covering versions; do not invent either.
6. Connect only links verified during the required pre-publication deployment check. A repository archive is not a browser deployment; do not postpone that check until after public release.

Follow the current [Zenodo GitHub/software guidance](https://help.zenodo.org/docs/github/) at publication time. No `.zenodo.json` containing invented creators/license has been added; this worksheet is deliberately not an upload-ready payload while blockers remain.

A DOI creates a persistent citable software record. It is not a patent grant or evidence that novelty, priority, ownership or patentability has been legally established. Public source history and archival records can document an implementation and its timing, but this project makes no patent-protection claim.
