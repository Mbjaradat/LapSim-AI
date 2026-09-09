# Phase 3B anatomy audit — 2026-09-08

Audit recorded before downloading anatomy. Primary candidate: **SPL Liver Atlas,
February 2014**, Open Anatomy Project / SPL and Boston Medical Center.

## Sources reviewed first

| Source | Exact terms and obligations | Decision |
| --- | --- | --- |
| [SPL Liver Atlas](https://www.openanatomy.org/atlas-pages/atlas-spl-liver.html) | Linked 3D Slicer License v1.0 (2005), Part B, with Part C applicable. Commercial use, modification and redistribution allowed. Preserve full terms, required preface and attributions; identify modified versions. No share-alike requirement; no endorsement rights. License includes disclaimers/indemnity and inherited third-party rights caveat. | USE minimum individually identified meshes after archive inventory; retain notices. |
| [SPL Abdominal Atlas](https://www.openanatomy.org/atlas-pages/atlas-spl-abdomen.html) | Same linked terms; authors Florin Talos, Marianna Jakab, Ron Kikinis. CT-derived segmentation, separate models. | NEEDS REVIEW only if liver archive lacks usable large organs; avoid mixing patient frames. No download planned. |
| [Z-Anatomy Models of Human Anatomy](https://github.com/Z-Anatomy/Models-of-human-anatomy/blob/master/License.txt) | Declares CC BY-SA 4.0, with BodyParts3D CC BY-SA 2.1 Japan attribution. Those licenses permit commercial derivatives and redistribution with attribution and share-alike. However the same register lists NC kidney/ear sources; per-structure inheritance is not resolved here. | DO NOT USE aggregate Z-Anatomy.zip; required individual meshes NEED REVIEW. Not downloaded. |

SPL authors: Marianna Jakab, Sonia Pujol, Kitt Shaffer, Ron Kikinis; organizations
SPL/Brigham and Women's Hospital/Harvard Medical School and Boston Medical Center.
Additional contributors: Matthew D'Artista, Alex Kikinis, Tobias Penzkofer.
Source archive: https://www.openanatomy.org/atlases/nac/liver-2014-02-20.zip
(39,035,218 bytes according to server HEAD). No radiology-grade fidelity is claimed.

License evidence: https://www.openanatomy.org/atlas-pages/slicer-license.html
CC evidence: https://creativecommons.org/licenses/by-sa/4.0/ and
https://creativecommons.org/licenses/by-sa/2.1/jp/deed.en

## Structure inventory before acquisition

All SPL rows inherit the permissions/attribution above; commercial/modification/
redistribution: **yes subject to those terms**; share-alike: **no**. Exact internal
file names and complexity will be appended after inspecting the one approved
archive. Unknown availability is not a claim that a structure exists.

| Structure | Candidate/file | Format/complexity before inventory | Blender/realtime suitability | Recommendation |
| --- | --- | --- | --- | --- |
| Liver | SPL Liver Atlas; internal file pending | Segmented 3D model; count unknown | Convert only selected mesh; simplify if needed | USE if identified |
| Gallbladder | SPL Liver Atlas; internal file pending | Availability/count unknown | Same patient coordinates preferred | USE if identified |
| Cystic duct | SPL Liver Atlas; internal file pending | Availability/count unknown | Small vessels may be below CT segmentation detail | NEEDS REVIEW; original procedural fallback |
| Common bile duct | SPL Liver Atlas; internal file pending | Availability/count unknown | Separate lightweight mesh desirable | NEEDS REVIEW; original fallback |
| Common hepatic duct | SPL Liver Atlas; internal file pending | Availability/count unknown | Separate lightweight mesh desirable | NEEDS REVIEW; original fallback |
| Cystic artery | SPL Liver Atlas; internal file pending | Availability/count unknown | Fine branch segmentation may be absent | NEEDS REVIEW; original fallback |
| Hepatic artery | SPL Liver Atlas vascular models | Availability/count unknown | Use only useful local branch; no full-body tree | NEEDS REVIEW |
| Portal vein (optional) | SPL Liver Atlas vascular models | Availability/count unknown | Not required if it adds occlusion | NEEDS REVIEW; omit if unnecessary |
| Peritoneal cavity | SPL abdominal context | Dedicated surface not established | Original curved surface avoids importing full body | USE original procedural geometry |

For Z-Anatomy, each requested structure has unverified internal file attribution,
polycount and inherited obligations; archive is a Blender template bundle. No
individual entry passes this audit yet. Share-alike would apply to distributed
adapted meshes, not automatically to independent unrelated project source code.
Do not relicense imported meshes as original Apache code. No ambiguous asset
will be imported. Original supplements will be explicitly labeled as such.
