"""Metric definitions (see docs/methodology.md). Pure functions over day aggregates."""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from . import timeutil

HIP3_SEP = ":"


def asset_class(coin: str) -> str:
    if not coin:
        return "unknown"
    if HIP3_SEP in coin:
        return "hip3"
    if coin.startswith("@") or "/" in coin:
        return "spot"
    if coin.startswith("#"):
        return "outcome"
    return "perp"


def window_summary(day_aggs: list[dict]) -> dict:
    """Combine builder-day aggregates into window metrics."""
    fee = vol = tvol = 0.0
    fills = 0
    users = defaultdict(float)
    coins = defaultdict(float)
    statuses = defaultdict(int)
    for d in day_aggs:
        fee += d["fee_usd"]
        vol += d["volume"]
        tvol += d["taker_volume"]
        fills += d["fills"]
        statuses[d["status"]] += 1
        for u, v in d["users"].items():
            users[u] += v[0]
        for c, v in d["coins"].items():
            coins[c] += v
    n = len(users)
    return {
        "days": len(day_aggs), "status_counts": dict(statuses),
        "complete_days": statuses.get("complete", 0) + statuses.get("gapfilled", 0) + statuses.get("missing_feed_sqd", 0),
        "revenue_usd": fee, "volume_usd": vol, "taker_volume_usd": tvol, "fills": fills,
        "unique_traders": n,
        "take_rate_bps": (fee / vol * 1e4) if vol else None,
        "revenue_per_trader": (fee / n) if n else None,
        "concentration": concentration(users),
        "asset_mix": asset_mix(coins),
    }


def concentration(user_volume: dict) -> dict:
    vols = sorted(user_volume.values(), reverse=True)
    total = sum(vols)
    n = len(vols)
    if not n or not total:
        return {}

    def share(lo_pct, hi_pct):
        a, b = int(n * lo_pct), max(int(n * hi_pct), int(n * lo_pct) + (1 if lo_pct == 0 else 0))
        return sum(vols[a:b]) / total

    hhi = sum((v / total) ** 2 for v in vols)
    return {"top1pct": share(0, 0.01), "top1_5pct": share(0.01, 0.05), "top5_10pct": share(0.05, 0.10),
            "top10_25pct": share(0.10, 0.25), "top25_50pct": share(0.25, 0.50), "bottom50pct": share(0.50, 1.0),
            "top10_traders": sum(vols[:10]) / total, "hhi": hhi}


def asset_mix(coins: dict) -> dict:
    total = sum(coins.values()) or 1
    out = defaultdict(float)
    for c, v in coins.items():
        out[asset_class(c)] += v / total
    top = sorted(coins.items(), key=lambda kv: -kv[1])[:10]
    return {"by_class": dict(out), "top_coins": [(c, v / total) for c, v in top]}


def new_vs_returning(day_aggs: list[dict], history: list[dict]) -> list[dict]:
    """Per day: new = first-ever fill in `history ∪ window` is that day."""
    first = {}
    for d in sorted(history + day_aggs, key=lambda x: x["day"]):
        for u in d["users"]:
            first.setdefault(u, d["day"])
    out = []
    for d in sorted(day_aggs, key=lambda x: x["day"]):
        new = sum(1 for u in d["users"] if first[u] == d["day"])
        out.append({"day": d["day"], "traders": len(d["users"]), "new": new, "returning": len(d["users"]) - new})
    return out


def weekly_retention(day_aggs: list[dict], max_k: int = 8) -> list[dict]:
    """Cohort = ISO week of a trader's first fill (within the supplied days)."""
    weeks_active = defaultdict(set)
    first_week = {}
    for d in sorted(day_aggs, key=lambda x: x["day"]):
        w = timeutil.iso_week(dt.date.fromisoformat(d["day"]))
        for u in d["users"]:
            weeks_active[u].add(w)
            first_week.setdefault(u, w)
    weeks = sorted({w for s in weeks_active.values() for w in s})
    idx = {w: i for i, w in enumerate(weeks)}
    cohorts = defaultdict(list)
    for u, w in first_week.items():
        cohorts[w].append(u)
    rows = []
    for w in weeks:
        members = cohorts.get(w, [])
        if not members:
            continue
        row = {"cohort": w, "size": len(members)}
        for k in range(0, min(max_k, len(weeks) - idx[w])):
            target = weeks[idx[w] + k]
            row[f"w{k}"] = sum(1 for u in members if target in weeks_active[u]) / len(members)
        rows.append(row)
    return rows


def hl_trader_pnl(fills: list[dict]) -> dict:
    closed = sum(float(f.get("closedPnl", 0)) for f in fills)
    fee = sum(float(f.get("fee", 0)) for f in fills)
    bfee = sum(float(f.get("builderFee", 0) or 0) for f in fills)
    vol = sum(abs(float(f["px"]) * float(f["sz"])) for f in fills)
    taker = sum(abs(float(f["px"]) * float(f["sz"])) for f in fills if f.get("crossed"))
    return {"fills": len(fills), "volume": vol, "taker_share": (taker / vol) if vol else None,
            "closed_pnl": closed, "fees": fee, "builder_fees": bfee, "net_realized_pnl": closed - fee - bfee}


# Polymarket taker fee rates by category (Oct 2026). Prefer per-market Gamma fields when present.
PM_FEE_RATES = {"crypto": 0.07, "sports": 0.05, "politics": 0.04, "finance": 0.04, "tech": 0.04,
                "mentions": 0.04, "economics": 0.05, "culture": 0.05, "weather": 0.05, "other": 0.05,
                "geopolitics": 0.0}


def pm_taker_fee(shares: float, price: float, rate: float) -> float:
    """fee = C × rate × p × (1 − p), rounded to 5 dp (min 0.00001 when positive)."""
    if not 0 <= price <= 1:
        raise ValueError("price must be in [0,1]")
    fee = shares * rate * price * (1 - price)
    if fee <= 0:
        return 0.0
    return max(round(fee, 5), 0.00001)
