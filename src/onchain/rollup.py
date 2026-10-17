"""Whole-company rollup: measure every product line of an app once, then add them up.

Product lines come from the registry (`apps[].product_lines`). Each line names ONE primary
measurement source; other sources are cross-checks only. See docs/methodology.md §7.

Dedupe rules (enforced here):
  R1 Each fill/swap/trade is counted once, in exactly one line (lines partition by asset class / chain).
  R2 Volume is taker-side only (a trade between two of the app's own users counts once).
  R3 Fees/revenue are counted per fee charged (both sides of a self-crossed trade really pay).
  R4 Never add a DefiLlama parent total on top of its children; use children per line.
  R5 Never add an on-chain measurement AND the DefiLlama child for the same line; one is primary.
  R6 Users are unioned only within one address namespace (e.g. Hyperliquid/EVM 0x addresses);
     Solana and EVM identities are not linked, so cross-namespace user totals are not summed.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from . import hl, llama, pm, registry, timeutil

NAMESPACE = {"hyperliquid": "evm", "polygon": "evm", "solana": "solana"}


# ---------------- measurers ----------------

def _hl_days(app, window, gapfill, cache_):
    key = ("hl", tuple(registry.hl_builders(app)), window, gapfill)
    if key not in cache_:
        cache_[key] = [hl.builder_day(a, d, gapfill=gapfill)
                       for d in timeutil.days(*window) for a in registry.hl_builders(app)]
    return cache_[key]


def measure_hl_builder(app, line, window, gapfill, cache_):
    cls = line["measure"]["asset_class"]
    days = _hl_days(app, window, gapfill, cache_)
    fee = vol = tvol = 0.0
    fills = 0
    users, statuses = set(), defaultdict(int)
    for d in days:
        statuses[d["status"]] += 1
        c = (d.get("classes") or {}).get(cls)
        if not c:
            continue
        fee += c["fee"]; vol += c["volume"]; tvol += c["taker_volume"]; fills += c["fills"]
        users.update(c["users"])
    bad = statuses.get("partial", 0) + statuses.get("missing", 0)
    return {"fees_usd": fee, "revenue_usd": fee, "volume_usd": tvol, "routed_volume_usd": vol, "fills": fills,
            "users": users, "user_namespace": "evm",
            "coverage": f"{len(days) - bad}/{len(days)} builder-days complete",
            "source": "HL builder_fills feed + SQD gap-fill", "measured": "on-chain"}


def measure_pm_builder(app, line, window, gapfill, cache_):
    codes = (app.get("polymarket") or {}).get("builder_codes", [])
    s_ms, _ = timeutil.day_bounds_ms(window[0])
    _, e_ms = timeutil.day_bounds_ms(window[1])
    s, e = s_ms // 1000, e_ms // 1000
    fee = taker_notional = notional = 0.0
    trades = 0
    reached = True
    for code in codes:
        rows = pm.builder_trades(code, max_pages=line["measure"].get("max_pages", 3000), since_ts=s)
        reached = reached and bool(rows) and min(int(r["matchTime"]) for r in rows) < s
        for r in rows:
            t = int(r["matchTime"])
            if not (s <= t < e):
                continue
            trades += 1
            fee += float(r.get("builderFee") or 0)
            n = float(r.get("sizeUsdc") or 0)
            notional += n
            if r.get("tradeType") == "TAKER":
                taker_notional += n
    return {"fees_usd": fee, "revenue_usd": fee, "volume_usd": taker_notional, "routed_volume_usd": notional,
            "fills": trades, "users": None, "user_namespace": None,
            "coverage": "full window" if reached else "lower bound (paging stopped early)",
            "source": "Polymarket CLOB /builder/trades", "measured": "on-chain"}


def _llama_breakdown(parent, kind, window, child, chains, exclude_chains):
    """Sum a parent's per-chain/per-child daily breakdown for one child over the window."""
    if kind == "volume":
        data = llama.dexs(parent)
    else:
        data = llama.summary(parent, kind)
    tot = 0.0
    found = False
    for ts, br in data.get("totalDataChartBreakdown", []):
        d = dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).date()
        if not window[0] <= d <= window[1]:
            continue
        for ch, m in br.items():
            if chains and ch not in chains:
                continue
            if exclude_chains and ch in exclude_chains:
                continue
            if child in m:
                found = True
                tot += float(m[child])
    return tot if found else None


def measure_defillama(app, line, window, gapfill, cache_):
    m = line["measure"]
    parent, child = m["parent"], m["child"]
    chains, excl = m.get("chains"), m.get("exclude_chains")
    fees = _llama_breakdown(parent, "fees", window, child, chains, excl)
    rev = _llama_breakdown(parent, "revenue", window, child, chains, excl)
    try:
        vol = _llama_breakdown(parent, "volume", window, child, chains, excl)
    except Exception:
        vol = None
    return {"fees_usd": fees or 0.0, "revenue_usd": rev if rev is not None else (fees or 0.0),
            "volume_usd": vol, "routed_volume_usd": None, "fills": None, "users": None, "user_namespace": None,
            "coverage": "DefiLlama child (daily)" if fees is not None else "child not found in DefiLlama breakdown",
            "source": f"DefiLlama {parent} → {child}" + (f" [{', '.join(chains)}]" if chains else "") +
                      (f" [excl. {', '.join(excl)}]" if excl else ""), "measured": "aggregator"}


def measure_none(app, line, window, gapfill, cache_):
    return {"fees_usd": None, "revenue_usd": None, "volume_usd": None, "routed_volume_usd": None, "fills": None,
            "users": None, "user_namespace": None, "coverage": "not visible on-chain",
            "source": line.get("note", "off-chain / not measurable keyless"), "measured": "not measured"}


MEASURERS = {"hl-builder": measure_hl_builder, "pm-builder": measure_pm_builder,
             "defillama": measure_defillama, "none": measure_none}


# ---------------- rollup ----------------

def rollup(app: dict, window, *, gapfill: bool = True) -> dict:
    lines = app.get("product_lines") or []
    if not lines:
        raise ValueError(f"{app['id']}: no product_lines in the registry; map the product first (product-revenue-map skill)")
    cache_ = {}
    rows = []
    users_by_ns = defaultdict(set)
    for line in lines:
        src = line["measure"]["source"]
        r = MEASURERS[src](app, line, window, gapfill, cache_)
        cc = line.get("crosscheck") or {}
        r.update({"line": line["id"], "stream": line.get("stream"), "chain": line.get("chain"),
                  "crosscheck": cc.get("defillama_child"), "maybe_in": cc.get("maybe_in")})
        if r["users"] is not None:
            users_by_ns[r["user_namespace"]].update(r["users"])
            r["unique_users"] = len(r["users"])
        else:
            r["unique_users"] = None
        r.pop("users")
        rows.append(r)
    num = lambda k: sum(r[k] for r in rows if isinstance(r.get(k), (int, float)))
    total = {"fees_usd": num("fees_usd"), "revenue_usd": num("revenue_usd"), "volume_usd": num("volume_usd"),
             "unique_users_by_namespace": {ns: len(u) for ns, u in users_by_ns.items()},
             "onchain_share_of_revenue": (sum(r["revenue_usd"] or 0 for r in rows if r["measured"] == "on-chain") /
                                          (num("revenue_usd") or 1)),
             "lines_not_measured": [r["line"] for r in rows if r["measured"] == "not measured"]}
    return {"app": app["id"], "window": window, "lines": rows, "total": total,
            "crosscheck": crosscheck(app, rows, window)}


def crosscheck(app: dict, rows: list[dict], window) -> list[dict]:
    parent = (app.get("defillama") or {}).get("slug")
    if not parent:
        return []
    out = []
    try:
        s = llama.summary(parent, "fees")
    except Exception as e:
        return [{"check": f"DefiLlama {parent}", "note": str(e)[:80]}]
    children = sorted({c for _, br in s.get("totalDataChartBreakdown", []) for m in br.values() for c in m})
    ours_by_child, maybe_by_child = defaultdict(float), defaultdict(float)
    for r in rows:
        if r["crosscheck"] and r["measured"] != "aggregator":
            ours_by_child[r["crosscheck"]] += r["fees_usd"] or 0
        if r.get("maybe_in") and r["measured"] != "aggregator":
            maybe_by_child[r["maybe_in"]] += r["fees_usd"] or 0
    for c in children or [None]:
        if c is None:
            break
        theirs = _llama_breakdown(parent, "fees", window, c, None, None) or 0.0
        ours = ours_by_child.get(c)
        used_as_primary = any(r["measured"] == "aggregator" and r["source"].split("→ ")[-1].split(" [")[0] == c for r in rows)
        out.append({"check": f"child {c}", "defillama_fees_usd": theirs,
                    "ours_onchain_usd": ours, "delta": (f"{(ours - theirs) / theirs:+.1%}" if ours is not None and theirs else
                                                         ("used as primary source" if used_as_primary else "n/a"))})
        if c in maybe_by_child and ours is not None:
            alt = ours + maybe_by_child[c]
            out.append({"check": f"child {c} if it includes the maybe_in lines (e.g. HIP-3)", "defillama_fees_usd": theirs,
                        "ours_onchain_usd": alt, "delta": f"{(alt - theirs) / theirs:+.1%}" if theirs else "n/a"})
    parent_total = sum(float(v) for ts, v in s.get("totalDataChart", [])
                       if window[0] <= dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).date() <= window[1])
    ours_total = sum(r["fees_usd"] or 0 for r in rows)
    out.append({"check": f"parent {parent} total (not added to rollup)", "defillama_fees_usd": parent_total,
                "ours_onchain_usd": ours_total, "note": "our rollup total incl. aggregator-sourced lines", "delta": f"{(ours_total - parent_total) / parent_total:+.1%}" if parent_total else "n/a"})
    return out
