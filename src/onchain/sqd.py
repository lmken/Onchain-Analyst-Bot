"""SQD Portal (public, keyless) access to the `hyperliquid-fills` dataset.

Used to fill the hours that the Hyperliquid builder_fills feed is missing.
Docs: https://docs.sqd.dev  •  Public limits: ~20 requests / 10 s; retry on `overloaded`.
"""
from __future__ import annotations

import json

from . import http

BASE = "https://portal.sqd.dev/datasets/hyperliquid-fills"
FILL_FIELDS = ["user", "coin", "px", "sz", "time", "crossed", "builderFee", "feeToken",
               "side", "closedPnl", "tid"]
_anchor_cache: dict[int, int] = {}


def head() -> int:
    return int(http.get_json(f"{BASE}/head")["number"])


def stream(from_block: int, to_block: int, *, builders=None, users=None, fields=None):
    """Yield (block_number, block_ts_ms, fill_dict). Continues across response cut-offs."""
    fields = fields or FILL_FIELDS
    cur = from_block
    while cur <= to_block:
        q = {"type": "hyperliquidFills", "fromBlock": cur, "toBlock": to_block,
             "fields": {"block": {"number": True, "timestamp": True},
                        "fill": {f: True for f in fields}}}
        flt = {}
        if builders:
            flt["builder"] = [b.lower() for b in builders]
        if users:
            flt["user"] = [u.lower() for u in users]
        q["fills"] = [flt] if flt else [{}]
        raw = http.request("POST", f"{BASE}/stream", body=q, timeout=120, retries=10)
        last = None
        for line in raw.splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            if "error" in obj:
                raise http.HTTPError(503, BASE, json.dumps(obj))
            h = obj["header"]
            last = int(h["number"])
            _anchor_cache[last] = int(h["timestamp"])
            for f in obj.get("fills", []):
                yield last, int(h["timestamp"]), f
        if last is None:
            # Empty body: the range is beyond the dataset head or has no blocks.
            break
        cur = last + 1


def block_ts(n: int) -> int:
    if n in _anchor_cache:
        return _anchor_cache[n]
    q = {"type": "hyperliquidFills", "fromBlock": n, "toBlock": n,
         "fields": {"block": {"number": True, "timestamp": True}}}
    raw = http.request("POST", f"{BASE}/stream", body=q, timeout=60, retries=10)
    for line in raw.splitlines():
        if line.strip():
            h = json.loads(line)["header"]
            _anchor_cache[int(h["number"])] = int(h["timestamp"])
            return int(h["timestamp"])
    raise LookupError(f"block {n} not available")


def block_at_or_after(ts_ms: int, hi: int | None = None) -> int:
    """First block with timestamp >= ts_ms (secant search, then bisection)."""
    hi = hi or head()
    lo = 750_000_000  # dataset start
    t_hi = block_ts(hi)
    if ts_ms > t_hi:
        return hi + 1
    t_lo = block_ts(lo)
    for _ in range(40):
        if hi - lo <= 1:
            break
        # interpolate, clamp into (lo, hi)
        guess = lo + int((ts_ms - t_lo) * (hi - lo) / max(1, (t_hi - t_lo)))
        guess = min(max(guess, lo + 1), hi - 1)
        if hi - lo < 64:
            guess = (lo + hi) // 2
        t = block_ts(guess)
        if t >= ts_ms:
            hi, t_hi = guess, t
        else:
            lo, t_lo = guess, t
    return hi if block_ts(lo) < ts_ms else lo
