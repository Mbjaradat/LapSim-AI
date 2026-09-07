# Licensing proposal — awaiting maintainer decision

## Original source code

Propose Apache License 2.0 for original independent source code. No root LICENSE or license metadata has been finalized. Confirm the copyright holder and intended scope before adding the canonical license text and appropriate source notices. Do not describe the repository as already Apache-licensed until that is done.

Apache-2.0 permits reuse, modification, and redistribution, including commercial use. It includes an express contributor patent grant with a patent-litigation termination provision. Redistribution requires preserving applicable notices and the license, identifying modifications, and carrying relevant NOTICE attributions if present. It provides no trademark grant and disclaims warranties. These obligations also matter when incorporating Apache-licensed code from others. See the [official Apache 2.0 terms](https://www.apache.org/licenses/LICENSE-2.0).

## Blender integration

Blender is GPL-licensed. Blender's [official FAQ](https://www.blender.org/support/faq/) states that published scripts using its Python API must be available under the GPL. Review the precise distribution and applicable GPL version before publishing integration code; an Apache-only blanket declaration is not sufficient planning for that component.

Proposed decision: retain Apache-2.0 for independent original modules, and separately select GPL-compatible distribution terms for Blender API scripts. Record directory-level scope and notices once approved. Architectural separation alone does not settle whether a combined work has additional obligations. Obtain specialist review if distribution boundaries remain uncertain.

Blender's application license does not automatically determine the license of artwork created with it; scene assets and embedded scripts need their own provenance and terms. See [Blender licensing](https://www.blender.org/about/license/).

## Third-party assets

Do not relicense third-party assets as original code. Track them in the root THIRD_PARTY_LICENSES.md and preserve each applicable license and attribution alongside the material. No third-party assets have been added.

## Pending approval

- Confirm Apache-2.0 for original independent source and the copyright holder wording.
- Agree on separate GPL-compatible licensing for future Blender API integration before implementation/distribution.
- Decide the license for future original scene/art assets before public release.

After these decisions, add the official LICENSE text, component-specific license files/notices as needed, and matching metadata. This is a project licensing plan, not a legal opinion.
