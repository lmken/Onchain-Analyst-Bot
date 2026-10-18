#!/usr/bin/env python3
"""Lint skills against the skill-authoring rules and project conventions. Stdlib only.

Checks: frontmatter (name == folder slug, description says when to use), size budget,
version marker, no secrets, no personal details, pinned repo links, short↔full drift.
"""
from __future__ import annotations

import re
import sys

from skilllib import CORE, endpoints, full_skills, parse, short_skills

FULL_MAX, SHORT_MAX = 6144, 2560
SECRET = re.compile(r"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_|xox[bpas]-|AKIA[0-9A-Z]{16}|-----BEGIN|"
                    r"(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,})", re.I)
PERSONAL = re.compile(r"\b(luke|wavegod|moonpay|revi)\b|/home/box|/workspace/|@[a-z0-9_]{3,}\.(com|io)", re.I)
REPO_LITERAL = re.compile(r"lmken|Onchain-Analyst-Bot")
REPO_LITERAL_ALLOWED = {"onchain-getting-started"}
# Skills that produce metrics must instruct the data-trust footer: sources, window and coverage.
METRIC = {"app-compare", "hyperliquid-builders", "hyperliquid-trader", "onchain-methodology", "onchain-report",
          "polymarket-builders", "polymarket-markets", "polymarket-wallets", "product-revenue-map", "protocol-fees"}


def has_footer(text: str) -> bool:
    """True if some 'footer' mention is followed (within 300 chars) by source, window and coverage."""
    low = text.lower()
    i = low.find("footer")
    while i != -1:
        span = low[i:i + 300]
        if all(w in span for w in ("source", "window", "coverage")):
            return True
        i = low.find("footer", i + 1)
    return False


def lint(slug, s, short=False) -> list[str]:
    e = []
    if s["name"] != slug:
        e.append(f"name '{s['name']}' must equal folder slug '{slug}'")
    d = s["description"] or ""
    if not d.startswith("Use "):
        e.append("description must say when to use (start with 'Use ')")
    if len(d) > 300:
        e.append(f"description too long ({len(d)} > 300)")
    limit = SHORT_MAX if short else FULL_MAX
    if s["bytes"] > limit:
        e.append(f"{s['bytes']} bytes > budget {limit}")
    if not s["marker"]:
        e.append("last line must be 'Skill version: <slug> v<semver>[-short] (Onchain Analyst)'")
    else:
        if s["marker"]["slug"] != slug:
            e.append("version marker slug mismatch")
        if short != s["marker"]["version"].endswith("-short"):
            e.append("short skills must use a -short version and full skills must not")
    if SECRET.search(s["text"]):
        e.append("possible secret")
    m = PERSONAL.search(s["text"])
    if m:
        e.append(f"personal/assistant-specific detail: {m.group(0)!r}")
    if slug not in REPO_LITERAL_ALLOWED and REPO_LITERAL.search(s["text"]):
        e.append("literal repo reference; use {REPO}/{REPO_RAW}/{TAG} from memory")
    for u in re.findall(r"raw\.githubusercontent\.com[^\s)`]*", s["text"]):
        if slug in REPO_LITERAL_ALLOWED:
            continue  # defines REPO_RAW; its fetches use {REPO_RAW}/{TAG}
        if "{TAG}" not in u and "<" not in u:
            e.append(f"unpinned raw link {u}")
    if slug in METRIC and not has_footer(s["text"]):
        e.append("metric skill must instruct the footer: sources, window, coverage")
    for req in ("# ",):
        if req not in s["body"]:
            e.append("missing markdown heading")
    return e


def main() -> int:
    errors = 0
    fulls = {slug: parse(p) for slug, p in full_skills().items()}
    shorts = {slug: parse(p) for slug, p in short_skills().items()}
    all_full_endpoints = set().union(*(endpoints(s["text"]) for s in fulls.values()))
    for slug, s in fulls.items():
        for msg in lint(slug, s):
            print(f"FAIL {slug}: {msg}"); errors += 1
    if set(shorts) != set(CORE):
        print(f"FAIL short set {sorted(shorts)} != core {sorted(CORE)}"); errors += 1
    for slug, s in shorts.items():
        for msg in lint(slug, s, short=True):
            print(f"FAIL short/{slug}: {msg}"); errors += 1
        f = fulls.get(slug)
        if f:
            if (s["name"], s["description"]) != (f["name"], f["description"]):
                print(f"FAIL short/{slug}: name/description differ from full version"); errors += 1
            extra = endpoints(s["text"]) - all_full_endpoints
            if extra:
                print(f"FAIL short/{slug}: endpoints not in any full skill: {sorted(extra)}"); errors += 1
    total = sum(s["bytes"] for s in fulls.values())
    core = fulls["onchain-getting-started"]["bytes"] + sum(s["bytes"] for s in shorts.values())
    print(f"{len(fulls)} full skills = {total:,} bytes; core template (getting-started + {len(shorts)} short) = {core:,} bytes")
    print("lint ok" if not errors else f"{errors} lint error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
