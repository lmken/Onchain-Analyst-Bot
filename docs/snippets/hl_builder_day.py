#!/usr/bin/env python3
"""One complete UTC day of Hyperliquid builder-code activity, using only the stdlib (+ optional lz4).

Usage:  python3 hl_builder_day.py <builder_address> <YYYY-MM-DD> [--no-gapfill] [--sqd-only]

1. Download the builder_fills feed file for the day (needs `pip install lz4`; skipped if missing).
2. Detect coverage: the feed is often truncated (e.g. stops ~12:00 UTC).
3. Fill the missing tail (and empty hours on busy days) from SQD Portal, keyless.
Prints JSON totals with a status label: complete | gapfilled | partial | missing.
"""
import csv, datetime as dt, io, json, sys, time, urllib.request, urllib.error

FEED = "https://stats-data.hyperliquid.xyz/Mainnet/builder_fills/{a}/{d}.csv.lz4"
SQD = "https://portal.sqd.dev/datasets/hyperliquid-fills"
UA = {"User-Agent": "onchain-analyst-snippet", "Content-Type": "application/json"}


def req(url, body=None, tries=8):
    delay = 1
    for i in range(tries):
        try:
            r = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=UA)
            with urllib.request.urlopen(r, timeout=120) as f:
                b = f.read()
            if b[:9] == b'{"error"' and b"overloaded" in b[:200]:
                raise urllib.error.HTTPError(url, 529, "overloaded", None, None)
            return b
        except urllib.error.HTTPError as e:
            if e.code in (403, 404) or i == tries - 1:
                raise
        except urllib.error.URLError:
            if i == tries - 1:
                raise
        time.sleep(delay); delay = min(delay * 2, 30)


def block_ts(n):
    q = {"type": "hyperliquidFills", "fromBlock": n, "toBlock": n, "fields": {"block": {"number": True, "timestamp": True}}}
    line = req(SQD + "/stream", q).splitlines()[0]
    return json.loads(line)["header"]["timestamp"]


def block_at(ts):
    lo, hi = 750_000_000, json.loads(req(SQD + "/head"))["number"]
    tlo, thi = block_ts(lo), block_ts(hi)
    if ts > thi:
        return hi + 1
    while hi - lo > 1:
        g = lo + int((ts - tlo) * (hi - lo) / max(1, thi - tlo)) if hi - lo > 64 else (lo + hi) // 2
        g = min(max(g, lo + 1), hi - 1)
        t = block_ts(g)
        if t >= ts: hi, thi = g, t
        else: lo, tlo = g, t
    return hi


def sqd_fills(builder, t0, t1):
    b, end = block_at(t0), block_at(t1) - 1
    fields = {f: True for f in ["user", "coin", "px", "sz", "time", "crossed", "builderFee", "feeToken"]}
    while b <= end:
        q = {"type": "hyperliquidFills", "fromBlock": b, "toBlock": end,
             "fields": {"block": {"number": True, "timestamp": True}, "fill": fields}, "fills": [{"builder": [builder]}]}
        last = None
        for line in req(SQD + "/stream", q).splitlines():
            o = json.loads(line); last = o["header"]["number"]
            for f in o.get("fills", []):
                if t0 <= f["time"] < t1:
                    yield f
        if last is None: break
        b = last + 1


def main():
    a = sys.argv[1].lower(); day = dt.date.fromisoformat(sys.argv[2])
    gap = "--no-gapfill" not in sys.argv; sqd_only = "--sqd-only" in sys.argv
    s_ms = int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp() * 1000); e_ms = s_ms + 86_400_000
    T = {"fee": 0.0, "volume": 0.0, "taker_volume": 0.0, "fills": 0}; users = set(); hours = set()
    def add(u, px, sz, crossed, fee, h):
        n = abs(px * sz); T["fee"] += fee; T["volume"] += n; T["fills"] += 1
        T["taker_volume"] += n if crossed else 0; users.add(u); hours.add(h)
    rows, last = [], None
    if not sqd_only:
        try:
            import lz4.frame
            blob = req(FEED.format(a=a, d=day.strftime("%Y%m%d")))
            rows = list(csv.DictReader(io.StringIO(lz4.frame.decompress(blob).decode())))
        except ImportError:
            sqd_only = True
        except urllib.error.HTTPError as e:
            if e.code not in (403, 404): raise  # 403 = no file for that day
    for r in rows:
        add(r["user"], float(r["px"]), float(r["sz"]), r["crossed"] == "true", float(r["builder_fee"] or 0), r["time"][11:13])
    feed_hours = sorted(hours)
    gaps = []
    if rows:
        last = max(r["time"] for r in rows)
        lt = int(dt.datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
        if last[11:13] != "23": gaps.append((lt + 1000, e_ms))
        if len(rows) >= 500:
            gaps += [(s_ms + h * 3_600_000, s_ms + (h + 1) * 3_600_000) for h in range(int(last[11:13])) if f"{h:02d}" not in feed_hours]
    else:
        gaps.append((s_ms, e_ms))
    status = "complete" if rows and not gaps else ("partial" if rows else "missing")
    sqd_n = 0
    if gap and gaps:
        for g0, g1 in sorted(gaps):
            for f in sqd_fills(a, g0, g1):
                add(f["user"], f["px"], f["sz"], f.get("crossed"), f.get("builderFee") or 0,
                    dt.datetime.fromtimestamp(f["time"] / 1000, dt.timezone.utc).strftime("%H")); sqd_n += 1
        status = "gapfilled" if rows else ("sqd_only" if sqd_only else "missing_feed_sqd")
    print(json.dumps({"builder": a, "day": str(day), "status": status, "feed_rows": len(rows), "sqd_rows": sqd_n,
                      "feed_hours": len(feed_hours), "last_feed_time": last, "hours_with_fills": len(hours),
                      "builder_fee_usd": round(T["fee"], 2), "volume_usd": round(T["volume"]),
                      "taker_volume_usd": round(T["taker_volume"]), "fills": T["fills"], "unique_traders": len(users)}, indent=1))


if __name__ == "__main__":
    main()
