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
    assert len(slugs) == 14 and "onchain-getting-started" in slugs
    assert sum(1 for s in m["skills"] if "short" in s) == 6


def test_every_data_skill_has_a_smoke_snippet():
    need = ["hyperliquid-builders", "hyperliquid-trader", "polymarket-markets", "polymarket-wallets",
            "polymarket-builders", "protocol-fees", "app-registry"]
    for s in need:
        assert "# smoke" in (ROOT / "skills" / s / "SKILL.md").read_text(), s
