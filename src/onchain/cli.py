"""`onchain` command line. Every command is a shortcut for a recipe in the skills."""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

from . import METHOD_VERSION, __version__, hl, http, llama, metrics, output, pm, registry, timeutil


def _err(*a):
    print(*a, file=sys.stderr, flush=True)


def _footer(sources, window=None, extra=None):
    f = {"sources": ", ".join(sources), "method": METHOD_VERSION, "toolkit": __version__}
    if window:
        f["window_utc"] = f"{window[0]} → {window[1]} (complete UTC days)"
    f.update(extra or {})
    return f


def _coverage_label(s):
    c = s["status_counts"]
    bad = c.get("partial", 0) + c.get("missing", 0)
    return (f"{s['complete_days']}/{s['days']} days complete" +
            (f"; {bad} partial/missing, so totals are understated" if bad else "") +
            f"; statuses {c}")


def _builder_days(addrs, window, gapfill):
    out = []
    for d in timeutil.days(*window):
        for a in addrs:
            r = hl.builder_day(a, d, gapfill=gapfill)
            out.append(r)
            _err(f"  {a[:8]}… {d} {r['status']} fee=${r['fee_usd']:,.0f}")
    return out


def _merge_days(days):
    """Sum several builder addresses (e.g. an app with two codes) per day."""
    by = {}
    for d in days:
        m = by.setdefault(d["day"], {"day": d["day"], "status": d["status"], "fee_usd": 0.0, "volume": 0.0,
                                     "taker_volume": 0.0, "fills": 0, "users": {}, "coins": {}, "coin_fees": {}})
        if d["status"] in ("partial", "missing"):
            m["status"] = d["status"]
        for k in ("fee_usd", "volume", "taker_volume", "fills"):
            m[k] += d[k]
        for u, v in d["users"].items():
            x = m["users"].setdefault(u, [0.0, 0.0, 0])
            x[0] += v[0]; x[1] += v[1]; x[2] += v[2]
        for c, v in d["coins"].items():
            m["coins"][c] = m["coins"].get(c, 0) + v
        for c, v in d.get("coin_fees", {}).items():
            m["coin_fees"][c] = m["coin_fees"].get(c, 0) + v
    return list(by.values())


def cmd_doctor(a):
    checks = [
        ("hyperliquid info", lambda: hl.info({"type": "meta"})["universe"][0]["name"]),
        ("hyperliquid builder feed", lambda: len(hl.http.get_bytes(hl.FEED.format(
            addr="0xb84168cf3be63c6b8dad05ff5d755e97432ff80b",
            ymd=(timeutil.last_complete_day() - dt.timedelta(days=1)).strftime("%Y%m%d")), retries=1))),
        ("sqd portal", lambda: hl.sqd.head()),
        ("polymarket gamma", lambda: len(pm.markets(limit=1))),
        ("polymarket data v2", lambda: len(pm.builders_leaderboard("day", 1)["data"])),
        ("polymarket clob", lambda: len(http.get_json(f"{pm.CLOB}/sampling-markets").get("data", []))),
        ("defillama", lambda: llama.summary("hyperliquid")["total24h"]),
        ("defillama coins", lambda: llama.prices(["hyperliquid"])["coins"]["coingecko:hyperliquid"]["price"]),
    ]
    rows = []
    try:
        import lz4  # noqa: F401
        rows.append({"check": "python lz4", "status": "ok", "detail": ""})
    except ImportError:
        rows.append({"check": "python lz4", "status": "missing", "detail": "feed decode unavailable; SQD-only path"})
    errs = registry.validate(registry.load())
    rows.append({"check": "registry", "status": "ok" if not errs else "error", "detail": "; ".join(errs)[:80]})
    if a.live:
        for name, fn in checks:
            try:
                rows.append({"check": name, "status": "ok", "detail": str(fn())[:60]})
            except Exception as e:  # report, don't crash
                rows.append({"check": name, "status": "fail", "detail": str(e)[:80]})
    output.render(rows, a.format, _footer(["local"] + (["live endpoints"] if a.live else []),
                                          extra={"home": str(hl.cache.home())}))
    return 0 if all(r["status"] in ("ok",) for r in rows if r["check"] != "python lz4") else 1


def cmd_setup(a):
    h = hl.cache.home()
    for sub in ("raw", "days", "http", "out"):
        (h / sub).mkdir(exist_ok=True)
    print(f"onchain home: {h}\nregistry apps: {len(registry.load())}\nnext: onchain doctor --live")
    return 0


def cmd_keys(a):
    names = sorted(k for k in os.environ if k.startswith("ONCHAIN_") and k.endswith("_KEY"))
    rows = [{"env_var": n, "present": "yes"} for n in names] or [{"env_var": "(none)", "present": "MVP needs no keys"}]
    output.render(rows, a.format)
    return 0


def cmd_hl_builders(a):
    window = timeutil.parse_window(a.window)
    apps = [x for x in registry.load() if registry.hl_builders(x)]
    if a.apps:
        apps = [x for x in apps if x["id"] in a.apps.split(",")]
    rows = []
    for app in apps:
        days = _merge_days(_builder_days(registry.hl_builders(app), window, not a.no_gapfill))
        s = metrics.window_summary(days)
        rows.append({"app": app["name"], "revenue_usd": s["revenue_usd"], "volume_usd": s["volume_usd"],
                     "traders": s["unique_traders"], "fills": s["fills"], "take_bps": s["take_rate_bps"],
                     "rev_per_trader": s["revenue_per_trader"],
                     "coverage": f"{s['complete_days']}/{s['days']}"})
    key = {"revenue": "revenue_usd", "volume": "volume_usd", "traders": "traders"}[a.sort]
    rows.sort(key=lambda r: -(r[key] or 0))
    total = sum(r["volume_usd"] for r in rows) or 1
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        r["cohort_share"] = f"{r['volume_usd'] / total:.1%}"
    output.render(rows[: a.top], a.format, _footer(["HL builder_fills feed", "SQD Portal (gap-fill)"], window,
                                                    {"note": "cohort_share = share of volume among listed registry builders"}))
    return 0


def cmd_hl_builder(a):
    window = timeutil.parse_window(a.window)
    app = registry.find(a.target)
    addrs = registry.hl_builders(app) if app else [a.target.lower()]
    days = _merge_days(_builder_days(addrs, window, not a.no_gapfill))
    s = metrics.window_summary(days)
    name = app["name"] if app else a.target
    summary = [{"metric": k, "value": v} for k, v in s.items() if k not in ("concentration", "asset_mix", "status_counts")]
    summary += [{"metric": f"concentration.{k}", "value": v} for k, v in s["concentration"].items()]
    summary += [{"metric": f"asset_mix.{k}", "value": v} for k, v in s["asset_mix"]["by_class"].items()]
    print(f"# {name}: Hyperliquid builder summary")
    output.render(summary, a.format)
    print("\n# Daily")
    output.render([{"day": d["day"], "status": d["status"], "revenue_usd": d["fee_usd"], "volume_usd": d["volume"],
                    "traders": len(d["users"]), "fills": d["fills"]} for d in sorted(days, key=lambda x: x["day"])], a.format)
    if a.cohorts:
        hist = []
        if a.history:
            first = None
            for b in (app or {}).get("hyperliquid", {}).get("builders", []):
                if b.get("first_seen"):
                    fs = dt.date.fromisoformat(str(b["first_seen"]))
                    first = fs if not first or fs < first else first
            if first and first < window[0]:
                hist = _merge_days(_builder_days(addrs, (first, window[0] - dt.timedelta(days=1)), not a.no_gapfill))
        nvr = metrics.new_vs_returning(days, hist)
        print("\n# New vs returning" + ("" if hist else " (new = first seen within this window)"))
        output.render(nvr, a.format)
        print("\n# Weekly retention (share of cohort active in week k)")
        output.render(metrics.weekly_retention(hist + days), a.format)
    output.render([], "table", _footer(["HL builder_fills feed"] + ([] if a.no_gapfill else ["SQD Portal (gap-fill)"]),
                                       window, {"coverage": _coverage_label(s)}))
    return 0


def cmd_hl_trader(a):
    window = timeutil.parse_window(a.window)
    s_ms, _ = timeutil.day_bounds_ms(window[0])
    _, e_ms = timeutil.day_bounds_ms(window[1])
    st = hl.clearinghouse(a.address)
    fills = hl.user_fills_by_time(a.address, s_ms, e_ms)
    p = metrics.hl_trader_pnl(fills)
    builders = {}
    for f in fills:
        if float(f.get("builderFee") or 0) > 0:
            builders["builder-routed fills"] = builders.get("builder-routed fills", 0) + 1
    rows = [{"metric": "account_value", "value": float(st["marginSummary"]["accountValue"])},
            {"metric": "withdrawable", "value": float(st["withdrawable"])},
            {"metric": "open_positions", "value": len(st["assetPositions"])}]
    rows += [{"metric": k, "value": v} for k, v in p.items()]
    rows += [{"metric": k, "value": v} for k, v in builders.items()]
    output.render(rows, a.format)
    pos = [{"coin": x["position"]["coin"], "size": float(x["position"]["szi"]),
            "entry": float(x["position"]["entryPx"] or 0), "value": float(x["position"]["positionValue"]),
            "upnl": float(x["position"]["unrealizedPnl"]), "lev": x["position"]["leverage"].get("value")}
           for x in st["assetPositions"]]
    if pos:
        print("\n# Positions")
        output.render(pos, a.format)
    output.render([], "table", _footer(["HL info clearinghouseState", "HL info userFillsByTime"], window,
                                       {"caveat": "userFillsByTime exposes only the most recent 10,000 fills"}))
    return 0


def cmd_hl_reconcile(a):
    window = timeutil.parse_window(a.window)
    app = registry.find(a.target)
    if not app:
        _err("unknown app; add it to the registry first")
        return 2
    addrs = registry.hl_builders(app)
    days = _merge_days(_builder_days(addrs, window, True))
    s = metrics.window_summary(days)
    rows = [{"check": "builder fills (feed + SQD gap-fill)", "revenue_usd": s["revenue_usd"],
             "volume_usd": s["volume_usd"], "traders": s["unique_traders"], "coverage": _coverage_label(s)}]
    rc = s.get("revenue_by_class", {})
    if rc:
        rows.append({"check": "  of which core perps (excl. HIP-3/spot/outcome)", "revenue_usd": rc.get("perp", 0.0)})
        rows.append({"check": "  of which HIP-3 (builder-deployed perps)", "revenue_usd": rc.get("hip3", 0.0)})
    perps = (app.get("defillama") or {}).get("perps")
    if perps:
        try:
            v = llama.window_total(perps, "fees", *window)
            core = rc.get("perp") if rc else None
            rows.append({"check": f"DefiLlama {perps} dailyFees", "revenue_usd": v,
                         "delta_vs_fills": f"{(s['revenue_usd'] - v) / v:+.1%} all; "
                                           + (f"{(core - v) / v:+.1%} core perps" if core is not None else "") if v else None})
        except Exception as e:
            rows.append({"check": f"DefiLlama {perps}", "revenue_usd": None, "delta_vs_fills": str(e)[:60]})
    lifetime = sum(float(hl.referral(x)["builderRewards"]) for x in addrs)
    rows.append({"check": "HL referral builderRewards (lifetime, all time)", "revenue_usd": lifetime})
    output.render(rows, a.format, _footer(["HL feed", "SQD Portal", "DefiLlama", "HL info referral"], window))
    return 0


def cmd_pm_builders(a):
    lb = pm.builders_leaderboard(a.period, a.top)["data"]
    rows = []
    since = None
    if a.revenue:
        since = int((timeutil.utc_now() - dt.timedelta(days={"day": 1, "week": 7, "month": 30}.get(a.period, 7))).timestamp())
    for b in lb:
        r = {"rank": b.get("rank"), "builder": b.get("builder_name"), "volume_shares": float(b.get("volume") or 0),
             "active_makers": b.get("active_users"), "verified": b.get("verified")}
        if a.revenue:
            t = pm.summarize_builder_trades(pm.builder_trades(b["builder_code"], a.max_pages, since), since)
            r.update({"notional_usdc": t["notional_usdc"], "builder_fee_usdc": t["builder_fee_usdc"],
                      "trades": t["trades"],
                      "trades_from_utc": timeutil.ms_to_iso(t["first_ts"] * 1000) if t["first_ts"] else None,
                      "full_period": t["reached_window_start"]})
        rows.append(r)
    output.render(rows, a.format, _footer(["Polymarket Data API v2 builders/leaderboard"] +
                                          (["CLOB /builder/trades"] if a.revenue else []),
                                          extra={"units": "volume_shares is in SHARES, not USD; notional_usdc is USDC",
                                                 "period": a.period}))
    return 0


def cmd_pm_markets(a):
    if a.q:
        res = pm.search(a.q, a.top)
        mk = [m for e in res.get("events", []) for m in e.get("markets", [])]
    else:
        mk = pm.markets(active="true", closed="false", order="volume24hr", ascending="false", limit=a.top)
    rows = [{"question": (m.get("question") or "")[:70], "slug": m.get("slug"),
             "price": m.get("outcomePrices"), "vol_24h": float(m.get("volume24hr") or 0),
             "liquidity": float(m.get("liquidityNum") or m.get("liquidity") or 0), "end": (m.get("endDate") or "")[:10]}
            for m in mk[: a.top]]
    output.render(rows, a.format, _footer(["Polymarket Gamma"]))
    return 0


def cmd_pm_market(a):
    m = pm.market_by_slug(a.slug)
    if not m:
        _err("market not found")
        return 2
    import json as _j
    toks = _j.loads(m.get("clobTokenIds") or "[]")
    outs = _j.loads(m.get("outcomes") or "[]")
    rows = [{"field": k, "value": m.get(k)} for k in ("question", "conditionId", "outcomePrices", "volume", "volume1wk",
                                                        "liquidityNum", "endDate", "feesEnabled", "feeType", "negRisk")]
    output.render(rows, a.format)
    h = pm.holders(m["conditionId"], a.holders)
    hold = []
    for grp in (h.get("data") if isinstance(h, dict) else h) or []:
        for x in grp.get("holders", [])[: a.holders]:
            hold.append({"wallet": x.get("proxy_wallet") or x.get("proxyWallet"),
                         "name": x.get("name") or x.get("pseudonym"), "amount": x.get("amount"), "outcome_index": x.get("outcome_index", x.get("outcomeIndex"))})
    if hold:
        print("\n# Top holders")
        output.render(hold, a.format)
    if toks:
        ph = pm.prices_history(toks[0], a.history)
        hist = ph.get("history", [])
        if hist:
            print(f"\n# Price history ({outs[0] if outs else 'token 0'}, {a.history}): first {hist[0]['p']}, last {hist[-1]['p']}, points {len(hist)}")
    output.render([], "table", _footer(["Gamma", "Data API v2 holders", "CLOB prices-history"]))
    return 0


def cmd_pm_wallet(a):
    st = pm.v2("user-stats", user=a.address).get("data", {})
    pos = pm.v2("positions", user=a.address, limit=a.top).get("data", [])
    print("# Stats")
    flat = {}
    for k, v in st.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if k2 in ("realized_pnl", "unrealized_pnl", "settled_pnl", "position_pnl", "fees_refunded", "maker_rebate", "reward_income"):
                    flat[f"{k}.{k2}"] = v2
        else:
            flat[k] = v
    output.render([{"metric": k, "value": v} for k, v in flat.items()], a.format)
    if pos:
        print("\n# Positions")
        output.render([{"title": (p.get("title") or "")[:50], "outcome": p.get("outcome"), "size": p.get("total_size", p.get("size")),
                        "avg_price": p.get("avg_price"), "value": p.get("current_value"),
                        "realized": p.get("realized_pnl"), "unrealized": p.get("unrealized_pnl")} for p in pos], a.format)
    output.render([], "table", _footer(["Polymarket Data API v2 user-stats, positions"],
                                       extra={"note": "use the proxy wallet (the profile address), not the EOA"}))
    return 0


def cmd_pm_fee(a):
    rate = a.rate if a.rate is not None else metrics.PM_FEE_RATES[a.category]
    fee = metrics.pm_taker_fee(a.shares, a.price, rate)
    output.render([{"shares": a.shares, "price": a.price, "rate": rate, "taker_fee_usdc": fee}], a.format,
                  _footer(["formula C×rate×p×(1−p)"], extra={"note": "makers pay 0; prefer the market's own feeSchedule"}))
    return 0


def cmd_fees(a):
    window = timeutil.parse_window(a.window)
    s = llama.summary(a.slug, a.type)
    ser = llama.series(a.slug, a.type, *window)
    total = sum(v for _, v in ser)
    rows = [{"day": d.isoformat(), a.type + "_usd": v} for d, v in ser]
    if a.format == "table" and not a.daily:
        rows = rows[-7:]
    output.render(rows, a.format, _footer([f"DefiLlama /summary/fees/{a.slug} {llama.TYPES[a.type]}"], window,
                                          {"window_total_usd": f"{total:,.0f}", "total30d_usd": f"{(s.get('total30d') or 0):,.0f}",
                                           "children": ", ".join(c if isinstance(c, str) else c.get("name", "") for c in (s.get("childProtocols") or []))[:120],
                                           "methodology": str(s.get("methodology") or "")[:200],
                                           "caveat": "DefiLlama may restate the most recent day for about 24h"}))
    return 0


def cmd_fees_top(a):
    o = llama.overview("fees")
    ps = [p for p in o.get("protocols", []) if not a.category or p.get("category") == a.category]
    ps.sort(key=lambda p: -(p.get("total30d") or 0))
    rows = [{"name": p.get("name"), "slug": p.get("slug"), "category": p.get("category"),
             "fees_24h": p.get("total24h"), "fees_30d": p.get("total30d")} for p in ps[: a.top]]
    output.render(rows, a.format, _footer(["DefiLlama /overview/fees"]))
    return 0


def cmd_price(a):
    p = llama.prices(a.ids)["coins"]
    rows = [{"id": k, "symbol": v.get("symbol"), "price_usd": v.get("price"),
             "as_of_utc": timeutil.ms_to_iso(int(v.get("timestamp", 0)) * 1000)} for k, v in p.items()]
    output.render(rows, a.format, _footer(["DefiLlama coins API"]))
    return 0


def cmd_registry(a):
    apps = registry.load()
    if a.action == "validate":
        errs = registry.validate(apps)
        print("\n".join(errs) or f"ok: {len(apps)} apps")
        return 1 if errs else 0
    if a.action == "show":
        app = registry.find(a.target or "")
        if not app:
            _err("not found")
            return 2
        import yaml
        print(yaml.safe_dump(app, sort_keys=False))
        return 0
    if a.action == "verify":
        rows = []
        for app in apps:
            if a.target and app["id"] != a.target:
                continue
            for b in (app.get("hyperliquid") or {}).get("builders", []):
                try:
                    r = float(hl.referral(b["address"])["builderRewards"])
                except Exception as e:
                    r = f"error {e}"[:40]
                rows.append({"app": app["id"], "address": b["address"], "builderRewards": r,
                             "registry_verified": bool(b.get("verified"))})
        output.render(rows, a.format, _footer(["HL info referral"]))
        return 0
    rows = [{"id": x["id"], "name": x["name"], "category": x["category"],
             "hl_builders": len((x.get("hyperliquid") or {}).get("builders", [])),
             "pm_codes": len((x.get("polymarket") or {}).get("builder_codes", [])),
             "llama": (x.get("defillama") or {}).get("slug")} for x in apps]
    output.render(rows, a.format)
    return 0


def cmd_app_compare(a):
    a.apps = ",".join(x.lower() for x in a.ids)
    a.sort = "revenue"
    a.top = 50
    return cmd_hl_builders(a)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="onchain", description="Onchain Analyst toolkit (read-only, keyless).")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--format", default="table", choices=["table", "json", "csv", "md"])
    p.add_argument("--offline", action="store_true", help="use cache only")
    p.add_argument("--refresh", action="store_true", help="bypass short-lived caches")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("doctor"); s.add_argument("--live", action="store_true"); s.set_defaults(fn=cmd_doctor)
    sub.add_parser("setup").set_defaults(fn=cmd_setup)
    k = sub.add_parser("keys"); k.add_argument("action", choices=["status"]); k.set_defaults(fn=cmd_keys)

    h = sub.add_parser("hl").add_subparsers(dest="sub", required=True)
    x = h.add_parser("builders"); x.add_argument("--window", default="30d"); x.add_argument("--top", type=int, default=20)
    x.add_argument("--sort", default="revenue", choices=["revenue", "volume", "traders"])
    x.add_argument("--apps", help="comma-separated registry ids"); x.add_argument("--no-gapfill", action="store_true")
    x.set_defaults(fn=cmd_hl_builders)
    x = h.add_parser("builder"); x.add_argument("target"); x.add_argument("--window", default="30d")
    x.add_argument("--cohorts", action="store_true"); x.add_argument("--no-gapfill", action="store_true")
    x.add_argument("--history", action=argparse.BooleanOptionalAction, default=True,
                   help="backfill from the builder's first_seen for new-vs-returning (default on)")
    x.set_defaults(fn=cmd_hl_builder)
    x = h.add_parser("trader"); x.add_argument("address"); x.add_argument("--window", default="30d"); x.set_defaults(fn=cmd_hl_trader)
    x = h.add_parser("reconcile"); x.add_argument("target"); x.add_argument("--window", default="30d"); x.set_defaults(fn=cmd_hl_reconcile)

    m = sub.add_parser("pm").add_subparsers(dest="sub", required=True)
    x = m.add_parser("builders"); x.add_argument("--period", default="week", choices=["day", "week", "month", "all"])
    x.add_argument("--top", type=int, default=20); x.add_argument("--revenue", action="store_true")
    x.add_argument("--max-pages", type=int, default=200); x.set_defaults(fn=cmd_pm_builders)
    x = m.add_parser("markets"); x.add_argument("--q"); x.add_argument("--top", type=int, default=20); x.set_defaults(fn=cmd_pm_markets)
    x = m.add_parser("market"); x.add_argument("slug"); x.add_argument("--holders", type=int, default=10)
    x.add_argument("--history", default="1m"); x.set_defaults(fn=cmd_pm_market)
    x = m.add_parser("wallet"); x.add_argument("address"); x.add_argument("--top", type=int, default=20); x.set_defaults(fn=cmd_pm_wallet)
    x = m.add_parser("fee"); x.add_argument("--shares", type=float, required=True); x.add_argument("--price", type=float, required=True)
    x.add_argument("--category", default="other", choices=sorted(metrics.PM_FEE_RATES)); x.add_argument("--rate", type=float)
    x.set_defaults(fn=cmd_pm_fee)

    f = sub.add_parser("fees"); f.add_argument("slug"); f.add_argument("--type", default="fees", choices=list(llama.TYPES))
    f.add_argument("--window", default="30d"); f.add_argument("--daily", action="store_true"); f.set_defaults(fn=cmd_fees)
    f = sub.add_parser("fees-top"); f.add_argument("--category"); f.add_argument("--top", type=int, default=20); f.set_defaults(fn=cmd_fees_top)
    x = sub.add_parser("price"); x.add_argument("ids", nargs="+"); x.set_defaults(fn=cmd_price)
    r = sub.add_parser("registry"); r.add_argument("action", choices=["list", "show", "validate", "verify"])
    r.add_argument("target", nargs="?"); r.set_defaults(fn=cmd_registry)
    c = sub.add_parser("compare"); c.add_argument("ids", nargs="+"); c.add_argument("--window", default="30d")
    c.add_argument("--no-gapfill", action="store_true"); c.set_defaults(fn=cmd_app_compare)
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    if a.offline:
        os.environ["ONCHAIN_OFFLINE"] = "1"
    if a.refresh:
        os.environ["ONCHAIN_REFRESH"] = "1"
    try:
        return a.fn(a) or 0
    except http.HTTPError as e:
        _err(f"error: {e}")
        return 3
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
