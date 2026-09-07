# Phase 1A verification record

Executed on 2026-09-07 using Blender 5.2.1 LTS on Windows, against the saved `blender/scenes/lapsim_ai_phase1a.blend`. Build and verification commands are in [phase1a.md](phase1a.md).

| Check | Result |
| --- | --- |
| Control contract unit tests | 4 passed, including NaN/infinity rejection |
| Saved-scene animation | All 241 frames checked for both instruments |
| Seeded randomized inputs | 200 passed |
| Direct-property boundary inputs | 4 passed; native drivers clamp independently of API |
| Fixed pivot / shaft line tolerance | 1e-6 m |
| Maximum measured pivot error | 3.161013638317052e-8 m |
| Insertion, pitch, yaw, axial rotation limits | Passed |
| Opposite internal/external lever relation | Passed |
| Left/right independence | Passed in both directions |
| Saved scene versus fresh script regeneration | Semantic signature matched |
| Background verifier exit code | 0 |

Semantic SHA-256 for this configuration:

```text
0ab5e5afec9cb4387709296e07f1ccd82525cc27c29e22a326995b5a48da4fd3
```

The machine-readable result is regenerated locally at `outputs/phase1a/validation.json` and is ignored by Git. The signature compares the selected scene content described in the verification script; it is not a file checksum or a promise of bit-identical rendering across hardware/Blender versions.

Blender reported denied writes to its user extension cache and a failed OS thumbnail-cache write in the restricted execution environment. These did not prevent saving the scene, reopening it, executing its drivers, or passing verification. No permissions or user preferences were changed to bypass those warnings.

These checks establish only the implemented rigid kinematic relationships. They do not establish physical, biomechanical, or clinical validity. Interactive playback performance has not been benchmarked.
