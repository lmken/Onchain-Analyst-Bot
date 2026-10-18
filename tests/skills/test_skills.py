import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(script, *args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], capture_output=True, text=True)


def test_lint_passes():
    r = run("lint_skills.py")
    assert r.returncode == 0, r.stdout + r.stderr


def test_manifest_current():
    r = run("build_manifest.py", "--check")
    assert r.returncode == 0, r.stdout


def test_manifest_covers_all_skills():
    import json
    m = json.loads((ROOT / "skills" / "manifest.json").read_text())
    slugs = {s["slug"] for s in m["skills"]}
    assert len(slugs) == 15 and "onchain-getting-started" in slugs
    assert sum(1 for s in m["skills"] if "short" in s) == 7


def test_every_data_skill_has_a_smoke_snippet():
    need = ["hyperliquid-builders", "hyperliquid-trader", "polymarket-markets", "polymarket-wallets",
            "polymarket-builders", "protocol-fees", "app-registry"]
    for s in need:
        assert "# smoke" in (ROOT / "skills" / s / "SKILL.md").read_text(), s


def _routine_prompt():
    import re
    t = (ROOT / "template" / "getting-started" / "SKILL.md").read_text()
    m = re.search(r'^- prompt: "(.*)"$', t, re.M)
    assert m, "routine prompt line missing from getting-started step 7"
    return m.group(1)


def test_short_skills_fit_size_limits():
    from lint_skills import FULL_MAX, SHORT_MAX
    from skilllib import full_skills, short_skills
    for slug, p in short_skills().items():
        n = len(p.read_bytes())
        assert n <= SHORT_MAX, f"short/{slug}: {n} > {SHORT_MAX}"
    for slug, p in full_skills().items():
        n = len(p.read_bytes())
        assert n <= FULL_MAX, f"{slug}: {n} > {FULL_MAX}"


def test_routine_prompt_handles_update_mode_and_counted_asset():
    p = _routine_prompt()
    assert "update_mode" in p
    assert "If update_mode is ask" in p and "If update_mode is auto" in p
    assert "curl -sfL https://github.com/lmken/Onchain-Analyst-Bot/releases/latest/download/manifest.json" in p
    assert "api.github.com/repos/lmken/Onchain-Analyst-Bot/releases/latest" in p  # fallback kept
    assert "edited" in p and "removed" in p  # auto never overwrites edits / deletes without asking
    assert '"' not in p


def test_update_skill_handles_update_mode():
    for p in (ROOT / "skills" / "onchain-update-skills" / "SKILL.md",
              ROOT / "template" / "skills" / "onchain-update-skills" / "SKILL.md"):
        t = p.read_text()
        assert "update_mode" in t and "auto" in t and "releases/latest/download/manifest.json" in t, p
        assert "Never install, overwrite or delete anything from a routine" not in t, p


def test_pins_match_release():
    import re
    from build_manifest import RELEASE
    v = RELEASE.lstrip("v")
    gs = (ROOT / "template" / "getting-started" / "SKILL.md").read_text()
    assert f"- `TAG = {RELEASE}`" in gs
    assert f'version = "{v}"' in (ROOT / "pyproject.toml").read_text()
    assert f'__version__ = "{v}"' in (ROOT / "src" / "onchain" / "__init__.py").read_text()
    assert f"Onchain-Analyst-Bot@{RELEASE}" in (ROOT / "README.md").read_text()
    assert re.search(rf"^## {re.escape(RELEASE)} \(", (ROOT / "CHANGELOG.md").read_text(), re.M)
