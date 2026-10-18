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


def test_metric_skills_instruct_data_trust_footer():
    from lint_skills import METRIC, has_footer
    from skilllib import full_skills, short_skills
    fulls, shorts = full_skills(), short_skills()
    assert METRIC <= set(fulls)
    for slug in METRIC:
        assert has_footer(fulls[slug].read_text()), slug
        if slug in shorts:
            assert has_footer(shorts[slug].read_text()), f"short/{slug}"
    assert not has_footer("Footer: source, window, fetch time.")  # coverage missing → rule fires


def test_getting_started_starters_and_opt_in_digest():
    gs = (ROOT / "template" / "getting-started" / "SKILL.md").read_text()
    start = gs.index("## 11. Starter questions")
    assert gs.index("## 10. Demo") < start
    assert sum(1 for l in gs[start:].splitlines() if l.startswith('- "')) >= 5
    assert "off by default" in gs and "Only on yes" in gs and "Weekly digest" in gs
    rep = (ROOT / "skills" / "onchain-report" / "SKILL.md").read_text()
    assert "Weekly onchain digest" in rep and "opt-in" in rep and "Turn it off" in rep


def test_registry_contribution_is_user_submitted():
    import yaml
    t = (ROOT / "skills" / "app-registry" / "SKILL.md").read_text()
    assert "https://github.com/{REPO}/issues/new?title=" in t and "&body=" in t
    assert "Never file issues yourself" in t
    form = yaml.safe_load((ROOT / ".github" / "ISSUE_TEMPLATE" / "registry-addition.yml").read_text())
    assert form["name"] == "Registry addition" and form["body"]


def test_example_report_is_labelled_snapshot():
    t = (ROOT / "docs" / "examples" / "fomo-30d.md").read_text()
    for s in ("Snapshot", "2026-09-17 → 2026-10-16 UTC", "22,713,208", "21,459,785", "22,531,680", "+0.8%",
              "1,379,560", "204,072", "25,452", "Sources:", "Coverage:"):
        assert s in t, s
    assert "docs/examples/fomo-30d.md" in (ROOT / "README.md").read_text()
