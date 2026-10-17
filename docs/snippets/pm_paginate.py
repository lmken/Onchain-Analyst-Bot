#!/usr/bin/env python3
"""Page Polymarket CLOB /builder/trades (newest first, 300 per page) and total a time window. Stdlib only.

Usage:  python3 pm_paginate.py <builder_code_bytes32> [hours=24] [max_pages=200]
Prints trades, notional (USDC), builder fees (USDC), platform fees and whether the window was fully covered.
"""
import json, sys, time, urllib.parse, urllib.request

code = sys.argv[1]; hours = float(sys.argv[2]) if len(sys.argv) > 2 else 24; max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 200
since = time.time() - hours * 3600
cursor, n, notional, bfee, pfee, oldest = None, 0, 0.0, 0.0, 0.0, None
for _ in range(max_pages):
    q = {"builder_code": code, **({"next_cursor": cursor} if cursor else {})}
    with urllib.request.urlopen(urllib.request.Request("https://clob.polymarket.com/builder/trades?" + urllib.parse.urlencode(q),
                                                       headers={"User-Agent": "onchain-analyst-snippet"}), timeout=60) as f:
        page = json.load(f)
    for t in page.get("data", []):
        ts = int(t["matchTime"]); oldest = ts if oldest is None else min(oldest, ts)
        if ts >= since:
            n += 1; notional += float(t.get("sizeUsdc") or 0); bfee += float(t.get("builderFee") or 0); pfee += float(t.get("feeUsdc") or 0)
    cursor = page.get("next_cursor")
    if not page.get("data") or not cursor or cursor == "LTE=" or (oldest and oldest < since):
        break
    time.sleep(0.1)
print(json.dumps({"builder_code": code, "hours": hours, "trades": n, "notional_usdc": round(notional, 2),
                  "builder_fee_usdc": round(bfee, 2), "platform_fee_usdc": round(pfee, 2),
                  "full_window": bool(oldest and oldest < since)}, indent=1))
