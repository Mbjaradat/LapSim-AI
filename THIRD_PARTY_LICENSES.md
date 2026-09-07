# Third-party materials register

No third-party code, assets, models, textures, recordings, or datasets are currently bundled. No external Python dependencies are currently declared. Blender is an external prerequisite, not redistributed in this repository. Phase 1A geometry and materials are generated from Blender primitives by original project scripts; no external models, textures, or fonts are imported. The scene's eventual distribution license remains pending under docs/licensing.md.

This register is separate from the proposed license for original source code. Before adding any material, record all fields below, including embedded textures, fonts, scripts, model weights, and transitive bundled components. Use one row per item or link a detailed per-item record if necessary.

| ID / repository path | Type / version / SHA-256 | Origin and title | Author / rights holder | Original URL / source | Retrieved date | Exact license / version | Local license text | Modifications | Attribution and redistribution requirements | Review status / reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Admission process

1. Verify terms at the original source and record author, source URL, version, and checksum.
2. Preserve the applicable license text under `assets/third_party/<item>/` for assets, or alongside vendored code, and link it here.
3. Record modifications explicitly, including “none” where applicable.
4. Record attribution wording, share-alike, source-offer, notice, commercial-use, and redistribution conditions as applicable. Identify incompatible restrictions before inclusion.
5. Review the whole bundle, including embedded components. Unknown or unverifiable terms mean do not add the material.
6. Recheck provenance when replacing or updating an item. Include required notices in release packages.

Future dependencies must also have their version, upstream source, and license reviewed. A dependency lockfile alone is not a license record. An empty register does not inventory the contents of a separately installed Blender distribution.
