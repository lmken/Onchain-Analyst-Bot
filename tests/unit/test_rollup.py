import datetime as dt

from onchain import registry, rollup

W = (dt.date(2026, 10, 1), dt.date(2026, 10, 2))


def _app():
    return {"id": "demo", "name": "Demo", "category": "wallet", "defillama": {"slug": "demo"},
            "hyperliquid": {"builders": [{"address": "0x" + "1" * 40, "verified": {"at": "x"}}]},
            "product_lines": [
                {"id": "hl-perps", "stream": "builder-fees", "chain": "hyperliquid",
                 "measure": {"source": "hl-builder", "asset_class": "perp"}, "crosscheck": {"defillama_child": "Demo Perps"}},
                {"id": "hl-hip3", "stream": "builder-fees", "chain": "hyperliquid",
                 "measure": {"source": "hl-builder", "asset_class": "hip3"}, "crosscheck": {"maybe_in": "Demo Perps"}},
                {"id": "swaps", "stream": "swap-fees", "chain": "solana",
                 "measure": {"source": "defillama", "parent": "demo", "child": "Demo Wallet"}},
                {"id": "card", "stream": "card-interchange", "measure": {"source": "none"}}]}


def _day(d):
    return {"day": str(d), "status": "complete", "classes": {
        "perp": {"fee": 10.0, "volume": 2000.0, "taker_volume": 1000.0, "fills": 4, "users": ["0xa", "0xb"]},
        "hip3": {"fee": 5.0, "volume": 500.0, "taker_volume": 300.0, "fills": 2, "users": ["0xb", "0xc"]}}}


BREAK = {"totalDataChart": [[1790812800, 130.0], [1790899200, 130.0]],
         "totalDataChartBreakdown": [[1790812800, {"Hyperliquid": {"Demo Perps": 10.0}, "Solana": {"Demo Wallet": 120.0}}],
                                     [1790899200, {"Hyperliquid": {"Demo Perps": 10.0}, "Solana": {"Demo Wallet": 120.0}}]]}


def test_rollup_dedupe_and_crosscheck(monkeypatch):
    monkeypatch.setattr(rollup.hl, "builder_day", lambda a, d, gapfill=True: _day(d))
    monkeypatch.setattr(rollup.llama, "summary", lambda slug, kind="fees": BREAK)
    monkeypatch.setattr(rollup.llama, "dexs", lambda slug: (_ for _ in ()).throw(RuntimeError("404")))
    r = rollup.rollup(_app(), W)
    by = {x["line"]: x for x in r["lines"]}
    assert by["hl-perps"]["fees_usd"] == 20 and by["hl-hip3"]["fees_usd"] == 10
    assert by["hl-perps"]["volume_usd"] == 2000            # taker-side only (R2): 2 days x 1000 taker, not 2 x 2000 routed
    assert by["swaps"]["fees_usd"] == 240 and by["swaps"]["measured"] == "aggregator"
    assert by["card"]["measured"] == "not measured"
    t = r["total"]
    assert t["fees_usd"] == 270                              # parent (260) NOT added on top (R4)
    assert t["unique_users_by_namespace"] == {"evm": 3}      # 0xb counted once across lines (R6)
    assert t["lines_not_measured"] == ["card"]
    cc = {c["check"]: c for c in r["crosscheck"]}
    assert cc["child Demo Perps"]["delta"] == "+0.0%"
    assert cc["child Demo Perps if it includes the maybe_in lines (e.g. HIP-3)"]["delta"] == "+50.0%"
    assert cc["child Demo Wallet"]["delta"] == "used as primary source"   # R5: not compared with itself


def test_registry_rejects_double_counted_lines():
    a = _app()
    a["product_lines"].append(dict(a["product_lines"][0], id="dup"))
    assert any("double count" in e for e in registry.validate([a]))


def test_registry_rejects_unknown_source_and_stream():
    a = _app()
    a["product_lines"][0]["measure"] = {"source": "magic"}
    a["product_lines"][1]["stream"] = "vibes"
    errs = registry.validate([a])
    assert any("measure.source" in e for e in errs) and any("stream must be" in e for e in errs)


def test_bundled_registry_product_maps_valid():
    apps = registry.load()
    assert registry.validate(apps) == []
    mapped = [a["id"] for a in apps if a.get("product_lines")]
    assert {"fomo", "rabby", "traderline"} <= set(mapped)
