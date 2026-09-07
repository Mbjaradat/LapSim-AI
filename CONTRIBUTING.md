# Contributing

The repository is in Phase 0. Discuss changes against the roadmap before expanding scope. License selection must be resolved before accepting outside code contributions or a public release.

## Workflow

1. Open an issue describing the problem, scope, and expected behavior.
2. Use a focused branch and small, reviewable changes.
3. Keep independent logic separate from Blender API calls and camera access.
4. Add meaningful tests when behavior is implemented; record what was actually tested.
5. Update documentation and provenance records with the change.
6. Submit a pull request describing behavior, validation, and limitations.

Do not commit environments, credentials, personal recordings, generated outputs, datasets, or large temporary assets. Check `git status` and staged diffs before committing. Main `.blend` sources are intentionally trackable; review binary size before adding them.

## Originality and third-party material

Submit only material you have authority to contribute. Never copy code or assets merely because they are publicly downloadable. Before adding third-party material, complete the register in THIRD_PARTY_LICENSES.md and retain required license and attribution files. Unknown licensing blocks inclusion. Asset terms do not become Apache-2.0 through inclusion here.

## AI-assisted development

Disclose substantial AI assistance in pull requests, including the tool/model when known. Explain human review and verification; do not claim generated code is automatically original, correct, licensed, or clinically valid. Do not include private prompts or secrets. Review generated code and assets for provenance concerns.

## Research claims

Keep claims proportional to evidence. Simulator metrics are not surgical competency certification. Document limitations and proposed validation methods; camera data collection and any human-subject study require a separately reviewed protocol before implementation.
