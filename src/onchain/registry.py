"""App registry loader: bundled registry/apps.yaml + optional ~/.onchain/registry.local.yaml."""
from __future__ import annotations

import re
from importlib import resources
from pathlib import Path

import yaml

from . import cache

ADDR = re.compile(r"^0x[0-9a-f]{40}$")
CODE = re.compile(r"^0x[0-9a-f]{64}$")


def _bundled_text() -> str:
    repo = Path(__file__).resolve().parents[2] / "registry" / "apps.yaml"
    if repo.exists():
        return repo.read_text()
    return resources.files("onchain").joinpath("data/apps.yaml").read_text()


def load() -> list[dict]:
    apps = yaml.safe_load(_bundled_text())["apps"]
    local = cache.home() / "registry.local.yaml"
    if local.exists():
        extra = (yaml.safe_load(local.read_text()) or {}).get("apps", [])
        ids = {a["id"]: i for i, a in enumerate(apps)}
        for a in extra:
            if a["id"] in ids:
                apps[ids[a["id"]]] = a
            else:
                apps.append(a)
    return apps


def validate(apps: list[dict]) -> list[str]:
    errs, seen_ids, seen_addr = [], set(), {}
    for a in apps:
        i = a.get("id", "?")
        if not re.fullmatch(r"[a-z0-9-]+", str(i)):
            errs.append(f"{i}: bad id")
        if i in seen_ids:
            errs.append(f"{i}: duplicate id")
        seen_ids.add(i)
        for k in ("name", "category"):
            if not a.get(k):
                errs.append(f"{i}: missing {k}")
        for b in (a.get("hyperliquid") or {}).get("builders", []):
            ad = b.get("address", "")
            if not ADDR.match(ad):
                errs.append(f"{i}: bad HL address {ad}")
            if ad in seen_addr:
                errs.append(f"{i}: address {ad} also in {seen_addr[ad]}")
            seen_addr[ad] = i
        for c in (a.get("polymarket") or {}).get("builder_codes", []):
            if not CODE.match(c):
                errs.append(f"{i}: bad PM builder code {c}")
        lines = a.get("product_lines") or []
        ids = [ln.get("id") for ln in lines]
        if len(ids) != len(set(ids)):
            errs.append(f"{i}: duplicate product_line id")
        for ln in lines:
            src = (ln.get("measure") or {}).get("source")
            if src not in LINE_SOURCES:
                errs.append(f"{i}/{ln.get('id')}: measure.source must be one of {sorted(LINE_SOURCES)}")
            if src == "hl-builder" and (ln["measure"].get("asset_class") not in ("perp", "hip3", "spot", "outcome")):
                errs.append(f"{i}/{ln.get('id')}: hl-builder needs asset_class perp|hip3|spot|outcome")
            if src == "defillama" and not {"parent", "child"} <= set(ln["measure"]):
                errs.append(f"{i}/{ln.get('id')}: defillama needs parent and child")
            if ln.get("stream") not in STREAMS:
                errs.append(f"{i}/{ln.get('id')}: stream must be one of {sorted(STREAMS)}")
        # R1: two lines must not measure the same thing
        keys = [repr(sorted((ln.get("measure") or {}).items())) for ln in lines if (ln.get("measure") or {}).get("source") != "none"]
        if len(keys) != len(set(keys)):
            errs.append(f"{i}: two product lines share the same measurement (double count)")
    return errs


LINE_SOURCES = {"hl-builder", "pm-builder", "defillama", "none"}
STREAMS = {"builder-fees", "swap-fees", "protocol-fees", "spread", "subscription", "mev-priority", "staking-yield",
           "token-sales", "referral", "card-interchange", "listing-fees", "other"}


def find(query: str) -> dict | None:
    q = query.lower()
    for a in load():
        if q in (a["id"], a["name"].lower()):
            return a
        for b in (a.get("hyperliquid") or {}).get("builders", []):
            if b["address"] == q:
                return a
        if q in [c.lower() for c in (a.get("polymarket") or {}).get("builder_codes", [])]:
            return a
    return None


def hl_builders(app: dict, verified_only: bool = True) -> list[str]:
    out = []
    for b in (app.get("hyperliquid") or {}).get("builders", []):
        if verified_only and not b.get("verified"):
            continue
        out.append(b["address"])
    return out
