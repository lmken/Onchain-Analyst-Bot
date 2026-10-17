import datetime as dt

import pytest

from onchain import metrics, timeutil


def day(d, users, fee=10.0, vol=1000.0, status="complete"):
    return {"day": d, "status": status, "fee_usd": fee, "volume": vol, "taker_volume": vol * 0.9, "fills": len(users),
            "users": {u: [v, 0.0, 1] for u, v in users.items()}, "coins": {"BTC": vol * 0.5, "@1": vol * 0.2, "xyz:TSLA": vol * 0.3}}


def test_window_summary_union_of_traders():
    s = metrics.window_summary([day("2026-10-01", {"a": 600, "b": 400}), day("2026-10-02", {"a": 500, "c": 500}, status="partial")])
    assert s["unique_traders"] == 3                     # union, not 4
    assert s["revenue_usd"] == 20 and s["volume_usd"] == 2000
    assert s["take_rate_bps"] == pytest.approx(100.0)
    assert s["complete_days"] == 1 and s["status_counts"] == {"complete": 1, "partial": 1}
    assert s["asset_mix"]["by_class"] == pytest.approx({"perp": 0.5, "spot": 0.2, "hip3": 0.3})


def test_concentration_and_hhi():
    vols = {f"u{i}": 1.0 for i in range(99)}
    vols["whale"] = 99.0
    c = metrics.concentration(vols)
    assert c["top1pct"] == pytest.approx(0.5)
    assert c["hhi"] == pytest.approx(0.5 ** 2 + 99 * (1 / 198) ** 2)
    assert sum(c[k] for k in ("top1pct", "top1_5pct", "top5_10pct", "top10_25pct", "top25_50pct", "bottom50pct")) == pytest.approx(1.0)


def test_new_vs_returning_uses_history():
    hist = [day("2026-09-01", {"a": 1})]
    w = [day("2026-10-01", {"a": 1, "b": 1}), day("2026-10-02", {"b": 1, "c": 1})]
    r = metrics.new_vs_returning(w, hist)
    assert r == [{"day": "2026-10-01", "traders": 2, "new": 1, "returning": 1},
                 {"day": "2026-10-02", "traders": 2, "new": 1, "returning": 1}]


def test_weekly_retention():
    w = [day("2026-10-05", {"a": 1, "b": 1}), day("2026-10-12", {"a": 1, "c": 1}), day("2026-10-19", {"a": 1, "b": 1})]
    r = {x["cohort"]: x for x in metrics.weekly_retention(w)}
    first = r[timeutil.iso_week(dt.date(2026, 10, 5))]
    assert first["size"] == 2 and first["w0"] == 1.0 and first["w1"] == 0.5 and first["w2"] == 1.0


def test_trader_pnl():
    fills = [{"px": "100", "sz": "1", "closedPnl": "10", "fee": "0.5", "builderFee": "0.1", "crossed": True},
             {"px": "100", "sz": "2", "closedPnl": "-4", "fee": "-0.2", "crossed": False}]
    p = metrics.hl_trader_pnl(fills)
    assert p["net_realized_pnl"] == pytest.approx(10 - 4 - 0.3 - 0.1)
    assert p["taker_share"] == pytest.approx(1 / 3)


@pytest.mark.parametrize("p,expected", [(0.5, 100 * 0.07 * 0.25), (0.01, 100 * 0.07 * 0.01 * 0.99), (0.99, 100 * 0.07 * 0.99 * 0.01)])
def test_pm_fee(p, expected):
    assert metrics.pm_taker_fee(100, p, 0.07) == pytest.approx(round(expected, 5))


def test_pm_fee_edges():
    assert metrics.pm_taker_fee(100, 0.5, 0.0) == 0.0
    assert metrics.pm_taker_fee(0.001, 0.5, 0.04) == 0.00001
    with pytest.raises(ValueError):
        metrics.pm_taker_fee(1, 1.5, 0.04)


def test_asset_class():
    assert [metrics.asset_class(c) for c in ("BTC", "@107", "PURR/USDC", "xyz:GOOGL", "#12")] == ["perp", "spot", "spot", "hip3", "outcome"]


def test_revenue_by_class():
    d = day("2026-10-01", {"a": 1})
    d["coin_fees"] = {"BTC": 6.0, "xyz:TSLA": 3.0, "@1": 1.0}
    s = metrics.window_summary([d])
    assert s["revenue_by_class"] == {"perp": 6.0, "hip3": 3.0, "spot": 1.0}
