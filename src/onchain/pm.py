"""Polymarket public APIs (keyless): Gamma, CLOB reads, Data API v2."""
from __future__ import annotations

from . import cache, http

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
DATA = "https://data-api.polymarket.com"


def _get(url, params=None, ttl=300):
    key = url + "?" + "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
    return cache.cached(key, ttl, lambda: http.get_json(url, params))


def search(q: str, limit: int = 10):
    return _get(f"{GAMMA}/public-search", {"q": q, "limit_per_type": limit}, ttl=900)


def markets(**params):
    return _get(f"{GAMMA}/markets", params, ttl=900)


def market_by_slug(slug: str):
    res = _get(f"{GAMMA}/markets", {"slug": slug}, ttl=900)
    return res[0] if res else None


def prices_history(token_id: str, interval: str = "1m", fidelity: int = 60):
    return _get(f"{CLOB}/prices-history", {"market": token_id, "interval": interval, "fidelity": fidelity})


def book(token_id: str):
    return _get(f"{CLOB}/book", {"token_id": token_id}, ttl=30)


def holders(condition_id: str, limit: int = 20):
    return _get(f"{DATA}/v2/holders", {"condition": condition_id, "limit": limit})


def v2(path: str, **params):
    return _get(f"{DATA}/v2/{path}", params)


def builders_leaderboard(period: str = "week", limit: int = 20):
    return v2("builders/leaderboard", time_period=period, limit=limit)


def builder_volume(code: str):
    return v2("builders/volume", builder_code=code)


def builder_trades(code: str, max_pages: int = 200, since_ts: int | None = None):
    """CLOB /builder/trades, newest first, pages of 300 via next_cursor.

    `matchTime` is unix seconds (string). Stops at max_pages or once trades are older than since_ts.
    """
    out, cursor = [], None
    for _ in range(max_pages):
        params = {"builder_code": code}
        if cursor:
            params["next_cursor"] = cursor
        page = http.get_json(f"{CLOB}/builder/trades", params)
        data = page.get("data", [])
        out.extend(data)
        cursor = page.get("next_cursor")
        if not data or not cursor or cursor == "LTE=":
            break
        if since_ts and min(int(d.get("matchTime") or 0) for d in data) < since_ts:
            break
    return out


def summarize_builder_trades(trades: list[dict], since_ts: int | None = None) -> dict:
    t = [x for x in trades if not since_ts or int(x.get("matchTime") or 0) >= since_ts]
    f = lambda k: sum(float(x.get(k) or 0) for x in t)
    notional = f("sizeUsdc")
    bfee = f("builderFee")
    return {"trades": len(t), "notional_usdc": notional, "builder_fee_usdc": bfee,
            "platform_fee_usdc": f("feeUsdc"),
            "take_rate_bps": (bfee / notional * 1e4) if notional else None,
            "taker_trades": sum(1 for x in t if x.get("tradeType") == "TAKER"),
            "first_ts": min((int(x["matchTime"]) for x in t), default=None),
            "last_ts": max((int(x["matchTime"]) for x in t), default=None),
            "reached_window_start": bool(since_ts) and bool(trades) and
            min(int(x.get("matchTime") or 0) for x in trades) < since_ts}
