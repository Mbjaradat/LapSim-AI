# Development setup

## Environment inventory — 2026-09-07

- Windows NT version 10.0, build 26200; registry DisplayVersion 25H2. The registry product label reports Windows 10 Home; this legacy label is not used to infer the marketing edition. CIM OS lookup was denied in the execution environment.
- Git 2.54.0.windows.1; existing repository on `main`, tracking `origin/main`; clean before Phase 0 edits. Remote freshness was not checked and nothing was pushed.
- `python` and `py` are unavailable on the current PATH. No standalone installation was found in checked standard Python folders or PythonCore registry keys; this is not an exhaustive disk search.
- Blender 5.2.1 LTS at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`.
- Blender command-line background launch and `bpy` expression execution succeeded. Bundled Python is 3.13.13. Bare `blender` is not on PATH.

## Python environment

No virtual environment was created: only Blender's bundled Python was detected, and the future CV environment should have its own interpreter. No software or packages were installed. The provisional metadata allows Python 3.11+, but CV package compatibility must be checked before choosing the supported version range.

Once a standalone interpreter is available, run from the repository root (replace the placeholder with its actual path):

```powershell
& 'C:\path\to\python.exe' -m venv .venv
& '.\.venv\Scripts\python.exe' --version
& '.\.venv\Scripts\python.exe' -m pip --version
```

Activation is optional; use the environment's interpreter explicitly. Phase 1A needs no package installation. `pyproject.toml` is the dependency declaration source; add only justified packages when functionality is implemented. Select a lockfile workflow and capture resolved dependencies before the first dependency-bearing release. There is no installable package yet. Phase 1A tests run through Blender's existing runtime; see [phase1a.md](phase1a.md).

## Blender verification

```powershell
$blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
& $blender --version
& $blender --background --factory-startup --python-exit-code 1 --python-expr "import bpy; print(bpy.app.version_string)"
```

These commands do not save a scene. Do not install packages into Blender's bundled Python as part of standalone environment setup.

## Repository hygiene

Main `.blend` files remain versionable; numbered backups are ignored. Keep local recordings, datasets, downloads, temporary assets, and generated outputs in the ignored directories documented by `.gitignore`. Git ignore rules are path-based, not a size or secret scanner; review every staged file. Choose a large-file distribution strategy if real distributable assets later require one.
