"""DefiLlama free API (keyless): fees / revenue / holders revenue, overviews, prices."""
from __future__ import annotations

import datetime as dt

from . import cache, http

API = "https://api.llama.fi"
COINS = "https://coins.llama.fi"
TYPES = {"fees": "dailyFees", "revenue": "dailyRevenue", "holders": "dailyHoldersRevenue"}


def summary(slug: str, kind: str = "fees") -> dict:
    dt_ = TYPES.get(kind, kind)
    return cache.cached(f"llama:{slug}:{dt_}", 3600,
                        lambda: http.get_json(f"{API}/summary/fees/{slug}", {"dataType": dt_}))


def series(slug: str, kind: str = "fees", start: dt.date | None = None, end: dt.date | None = None):
    s = summary(slug, kind)
    out = []
    for ts, v in s.get("totalDataChart", []):
        d = dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).date()
        if (start and d < start) or (end and d > end):
            continue
        out.append((d, float(v)))
    return out


def window_total(slug: str, kind: str, start: dt.date, end: dt.date) -> float:
    return sum(v for _, v in series(slug, kind, start, end))


def overview(kind: str = "fees"):
    return cache.cached(f"llama:overview:{kind}", 3600,
                        lambda: http.get_json(f"{API}/overview/{kind}",
                                              {"excludeTotalDataChart": "true", "excludeTotalDataChartBreakdown": "true"}))


def prices(ids: list[str]) -> dict:
    ids = [i if ":" in i else f"coingecko:{i}" for i in ids]
    return cache.cached("llama:price:" + ",".join(ids), 300,
                        lambda: http.get_json(f"{COINS}/prices/current/" + ",".join(ids)))
