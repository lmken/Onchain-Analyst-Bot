"""Live, opt-in: run every `# smoke` snippet from the skills with plain python3 (no pip packages).

    pytest -m live tests/snippets
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BLOCK = re.compile(r"```bash\n# smoke\n(.*?)```", re.S)
SNIPPETS = [(p.parent.name, i, b) for p in sorted((ROOT / "skills").glob("*/SKILL.md"))
            for i, b in enumerate(BLOCK.findall(p.read_text()))]
CLEAN_PY = shutil.which("python3", path="/usr/bin:/bin:/usr/local/bin")


@pytest.mark.live
@pytest.mark.parametrize("skill,idx,code", SNIPPETS, ids=[f"{s}-{i}" for s, i, _ in SNIPPETS])
def test_snippet(skill, idx, code, tmp_path):
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(tmp_path)}
    r = subprocess.run(["bash", "-euo", "pipefail", "-c", code], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-500:]
    assert r.stdout.strip(), "no output"


@pytest.mark.live
def test_stdlib_builder_day_script_without_lz4(tmp_path):
    """hl_builder_day.py with a python that lacks lz4 must fall back to SQD only."""
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(tmp_path)}
    r = subprocess.run([CLEAN_PY, str(ROOT / "docs" / "snippets" / "hl_builder_day.py"),
                        "0x7975cafdff839ed5047244ed3a0dd82a89866081", "2026-10-15", "--sqd-only"],
                       env=env, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr[-500:]
    assert '"status"' in r.stdout
