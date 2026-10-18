# Contributing / release checklist

1. Edit or add skills in `skills/<slug>/SKILL.md` (and the short version in `template/skills/` for core skills). Bump each touched skill's `Skill version:` line.
2. Bump `RELEASE` in `scripts/build_manifest.py`, `version` in `pyproject.toml`, `__version__` in `src/onchain/__init__.py`, the README install pin and `TAG` in `template/getting-started/SKILL.md`.
3. Add a `## vX.Y.Z (date)` entry to `CHANGELOG.md`.
4. `python3 scripts/build_manifest.py`, then `python3 scripts/lint_skills.py`, `python3 scripts/build_manifest.py --check`, `pytest` and `pytest -m live`.
5. Commit and push `main`, then run `scripts/release.sh vX.Y.Z`. It tags, pushes and creates the GitHub release with the CHANGELOG notes, and **always attaches `skills/manifest.json` as the asset `manifest.json`**. Bots fetch `releases/latest/download/manifest.json`; without the asset they fall back to uncounted URLs (see `docs/telemetry.md`).
6. If the persona, routines or baked-in skills changed, re-export the template.
