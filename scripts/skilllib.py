"""Shared helpers for skill tooling (stdlib only)."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = re.compile(r"^Skill version: (?P<slug>[a-z0-9-]+) v(?P<version>\d+\.\d+\.\d+(?:-short)?) \(Onchain Analyst\)$")
CORE = ["onchain-source-map", "onchain-methodology", "hyperliquid-builders", "polymarket-builders",
        "protocol-fees", "onchain-update-skills"]


def parse(path: Path) -> dict:
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path}: missing YAML frontmatter")
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    body = m.group(2)
    last = body.rstrip().splitlines()[-1].strip() if body.strip() else ""
    mk = MARKER.match(last)
    return {"path": path, "text": text, "name": fm.get("name"), "description": fm.get("description"),
            "body": body, "marker": mk.groupdict() if mk else None,
            "bytes": len(text.encode()), "sha256": hashlib.sha256(text.encode()).hexdigest()}


def full_skills() -> dict[str, Path]:
    out = {p.parent.name: p for p in sorted((ROOT / "skills").glob("*/SKILL.md"))}
    out["onchain-getting-started"] = ROOT / "template" / "getting-started" / "SKILL.md"
    return out


def short_skills() -> dict[str, Path]:
    return {p.parent.name: p for p in sorted((ROOT / "template" / "skills").glob("*/SKILL.md"))}


URL = re.compile(r"https?://[A-Za-z0-9.-]+(?:/[A-Za-z0-9_./{}<>-]*)?")


def endpoints(text: str) -> set[str]:
    out = set()
    for u in URL.findall(text):
        u = re.sub(r"[<{][^>}]*[>}]", "*", u).rstrip("/.")
        out.add(u)
    return out
