"""Hyperliquid: info API (keyless) and the public builder_fills feed.

The builder_fills feed is often truncated (many days stop around 12:00 UTC).
`builder_day()` detects coverage and, by default, fills the missing tail of the day
from SQD Portal so totals are complete, labelling every day with its status.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
from collections import defaultdict

from . import METHOD_VERSION, cache, http, sqd, timeutil

INFO = "https://api.hyperliquid.xyz/info"
FEED = "https://stats-data.hyperliquid.xyz/Mainnet/builder_fills/{addr}/{ymd}.csv.lz4"
INTERNAL_GAP_MIN_ROWS = 500  # below this, empty hours are plausibly just quiet
USD_TOKENS = {"USDC", "USDT0", "USDE", "USDH", None, ""}


def info(body: dict):
    return http.post_json(INFO, body)


def referral(addr: str) -> dict:
    return info({"type": "referral", "user": addr.lower()})


def clearinghouse(addr: str) -> dict:
    return info({"type": "clearinghouseState", "user": addr.lower()})


def user_fees(addr: str) -> dict:
    return info({"type": "userFees", "user": addr.lower()})


def user_fills_by_time(addr: str, start_ms: int, end_ms: int | None = None, max_pages: int = 10):
    """Pages userFillsByTime (≤2,000 per page; the API keeps only the last 10,000 fills)."""
    out, cur = [], start_ms
    for _ in range(max_pages):
        body = {"type": "userFillsByTime", "user": addr.lower(), "startTime": cur, "aggregateByTime": False}
        if end_ms:
            body["endTime"] = end_ms
        page = info(body)
        if not page:
            break
        out.extend(page)
        if len(page) < 2000:
            break
        cur = int(page[-1]["time"]) + 1
    seen, uniq = set(), []
    for f in out:
        if f["tid"] not in seen:
            seen.add(f["tid"])
            uniq.append(f)
    return uniq


# ---------------- builder feed ----------------

def feed_rows(addr: str, day: dt.date) -> list[dict] | None:
    """Rows of one UTC day's builder_fills file, or None if no file (HTTP 403/404)."""
    import lz4.frame  # optional dependency; skills document an SQD-only path without it

    ymd = day.strftime("%Y%m%d")
    raw_p = cache.path("raw", "hl_builder_fills", addr.lower(), f"{ymd}.csv.lz4")
    if raw_p.exists():
        blob = raw_p.read_bytes()
    else:
        try:
            blob = http.get_bytes(FEED.format(addr=addr.lower(), ymd=ymd), retries=3)
        except http.HTTPError as e:
            if e.status in (403, 404):
                return None
            raise
        raw_p.write_bytes(blob)
    text = lz4.frame.decompress(blob).decode()
    return list(csv.DictReader(io.StringIO(text)))


def _iso_to_ms(s: str) -> int:
    return int(dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp() * 1000)


def coverage(rows: list[dict]) -> dict:
    hours = sorted({r["time"][11:13] for r in rows})
    last = max((r["time"] for r in rows), default=None)
    return {"feed_hours": len(hours), "hours": hours, "last_feed_time": last,
            "truncated": bool(rows) and last[11:13] != "23"}


class DayAgg:
    def __init__(self):
        self.fee = 0.0
        self.fee_other = defaultdict(float)
        self.volume = 0.0
        self.taker_volume = 0.0
        self.fills = 0
        self.users = defaultdict(lambda: [0.0, 0.0, 0])   # user -> [volume, fee, fills]
        self.coins = defaultdict(float)
        self.coin_fees = defaultdict(float)
        self.hours = set()

    def add(self, user, coin, px, sz, crossed, fee, token, hour):
        n = abs(px * sz)
        self.fills += 1
        self.volume += n
        if crossed:
            self.taker_volume += n
        if token in USD_TOKENS:
            self.fee += fee
        else:
            self.fee_other[token] += fee
        u = self.users[user]
        u[0] += n
        u[1] += fee
        u[2] += 1
        if coin:
            self.coins[coin] += n
            if token in USD_TOKENS:
                self.coin_fees[coin] += fee
        self.hours.add(hour)


def builder_day(addr: str, day: dt.date, *, gapfill: bool = True) -> dict:
    """Aggregate one complete UTC day for a builder, with coverage + gap-fill."""
    addr = addr.lower()
    cp = cache.path("days", addr, f"{day.isoformat()}.json")
    old_enough = (timeutil.last_complete_day() - day).days >= 2
    hit = cache.read_json(cp)
    if hit and hit.get("method_version") != METHOD_VERSION:
        hit = None  # computed by an older method; recompute
    if hit and old_enough and (hit["status"] in ("complete", "gapfilled", "missing_feed_sqd")
                               or (hit["status"] == "partial" and not gapfill)):
        return hit

    agg = DayAgg()
    rows = feed_rows(addr, day)
    cov = {"feed_hours": 0, "hours": [], "last_feed_time": None, "truncated": False}
    start_ms, end_ms = timeutil.day_bounds_ms(day)
    tail_from = start_ms
    if rows:
        cov = coverage(rows)
        for r in rows:
            agg.add(r["user"], r["coin"], float(r["px"]), float(r["sz"]), r["crossed"] == "true",
                    float(r["builder_fee"] or 0), "USDC", r["time"][11:13])
        # feed times are whole seconds; take SQD fills from the next whole second
        tail_from = _iso_to_ms(cov["last_feed_time"]) + 1000

    # Gaps to fill: the tail after the last feed second, plus empty whole hours inside a busy day.
    gaps = []
    if rows:
        if cov["truncated"]:
            gaps.append((tail_from, end_ms))
        if len(rows) >= INTERNAL_GAP_MIN_ROWS:
            last_h = int(cov["last_feed_time"][11:13])
            present = {int(h) for h in cov["hours"]}
            for h in range(0, last_h):
                if h not in present:
                    gaps.append((start_ms + h * 3_600_000, start_ms + (h + 1) * 3_600_000))
    else:
        gaps.append((start_ms, end_ms))
    status = "complete" if rows and not gaps else ("partial" if rows else "missing")
    sqd_rows = 0
    sqd_error = None
    if gapfill and gaps:
        try:
            for g0, g1 in _merge(gaps):
                b0 = sqd.block_at_or_after(g0)
                b1 = sqd.block_at_or_after(g1) - 1
                if b1 < b0:
                    continue
                for _, _, f in sqd.stream(b0, b1, builders=[addr]):
                    t = int(f["time"])
                    if not (g0 <= t < g1):
                        continue
                    hour = timeutil.ms_to_iso(t)[11:13]
                    agg.add(f["user"], f.get("coin"), float(f["px"]), float(f["sz"]), bool(f.get("crossed")),
                            float(f.get("builderFee") or 0), f.get("feeToken"), hour)
                    sqd_rows += 1
            status = "gapfilled" if rows else "missing_feed_sqd"
        except Exception as e:  # keep what we have, label it partial
            sqd_error = str(e)[:300]
    gap_hours = round(sum(b - a for a, b in gaps) / 3_600_000, 2)
    out = {
        "builder": addr, "day": day.isoformat(), "status": status,
        "feed_rows": len(rows or []), "sqd_rows": sqd_rows, "sqd_error": sqd_error,
        "feed_hours": cov["feed_hours"], "last_feed_time": cov["last_feed_time"],
        "hours_with_fills": len(agg.hours), "gap_hours": gap_hours,
        "fee_usd": agg.fee, "fee_other": dict(agg.fee_other),
        "volume": agg.volume, "taker_volume": agg.taker_volume, "fills": agg.fills,
        "users": {u: v for u, v in agg.users.items()}, "coins": dict(agg.coins), "coin_fees": dict(agg.coin_fees),
        "sources": ["hyperliquid builder_fills feed"] + (["SQD Portal hyperliquid-fills"] if sqd_rows else []),
        "method_version": METHOD_VERSION,
        "fetched_at": timeutil.utc_now().isoformat(timespec="seconds"),
    }
    cache.write_json(cp, out)
    return out


def _merge(gaps):
    out = []
    for a, b in sorted(gaps):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out
