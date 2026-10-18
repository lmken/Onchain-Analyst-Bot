#!/usr/bin/env python3
"""Regenerate skills/manifest.json from the skill files (sha256, bytes, versions).

Usage: python3 scripts/build_manifest.py [--check]   (--check fails if the file is stale)
"""
from __future__ import annotations

import json
import sys

from skilllib import CORE, ROOT, full_skills, parse, short_skills

RELEASE = "v0.1.3"
TEMPLATE_MODE = "full"  # preferred; switch to "core" if the template size measurement (M0) requires it


def build() -> dict:
    shorts = short_skills()
    skills = []
    for slug, p in full_skills().items():
        s = parse(p)
        e = {"slug": slug, "name": s["name"], "description": s["description"],
             "version": s["marker"]["version"] if s["marker"] else None,
             "tier": "onboarding" if slug == "onchain-getting-started" else ("core" if slug in CORE else "extended"),
             "path": str(p.relative_to(ROOT)), "sha256": s["sha256"], "bytes": s["bytes"]}
        if slug in shorts:
            sh = parse(shorts[slug])
            e["short"] = {"path": str(shorts[slug].relative_to(ROOT)), "version": sh["marker"]["version"] if sh["marker"] else None,
                          "sha256": sh["sha256"], "bytes": sh["bytes"]}
        skills.append(e)
    total_full = sum(x["bytes"] for x in skills)
    total_core = sum(x["bytes"] for x in skills if x["tier"] == "onboarding") + sum(x["short"]["bytes"] for x in skills if "short" in x)
    return {"release": RELEASE, "template_mode": TEMPLATE_MODE, "repo": "lmken/Onchain-Analyst-Bot",
            "totals": {"skills": len(skills), "full_template_bytes": total_full, "core_template_bytes": total_core},
            "skills": skills}


def main() -> int:
    m = build()
    out = ROOT / "skills" / "manifest.json"
    text = json.dumps(m, indent=2) + "\n"
    if "--check" in sys.argv:
        if not out.exists() or out.read_text() != text:
            print("manifest.json is stale: run python3 scripts/build_manifest.py")
            return 1
        print("manifest ok")
        return 0
    out.write_text(text)
    print(f"wrote {out.relative_to(ROOT)}: {m['totals']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
