---
name: polymarket-builders
description: Use for Polymarket builder codes (apps that route orders to Polymarket) — rankings by volume, active makers, builder-fee revenue, notional and take rate over a day, week or month.
---
# Polymarket builders

## Fast path
`onchain pm builders --period week --top 20 --revenue` (revenue pages through CLOB trades; a busy builder can take minutes)

## Raw path (keyless)
```bash
# smoke
curl -s "https://data-api.polymarket.com/v2/builders/leaderboard?time_period=week&limit=5" | python3 -c "import sys,json;print([(b['builder_name'],b['volume']) for b in json.load(sys.stdin)['data']])"
```
- **Daily series:** `https://data-api.polymarket.com/v2/builders/volume?builder_code=<bytes32>`.
- **Revenue:** page `https://clob.polymarket.com/builder/trades?builder_code=<bytes32>` (newest first, 300 per page, `next_cursor` until `LTE=`).
  - `matchTime` is unix seconds.
  - Sum `builderFee` (USDC) for builder revenue, `sizeUsdc` for notional and `feeUsdc` for platform fees.
  - Script: `curl -sfO {REPO_RAW}/{TAG}/docs/snippets/pm_paginate.py && python3 pm_paginate.py <code> 168` (168 hours = 7 days).

## Pitfalls
- Leaderboard `volume` is in **shares**, not USD. `active_users` = distinct **makers**. Label both exactly.
- Many builders charge 0 builder fee, so revenue can legitimately be 0 while volume is large.
- Builder fee caps: taker ≤100 bps, maker ≤50 bps.
- Leaderboard periods are rolling. State the fetch time (UTC).
- If paging stops before the window start (`full_window: false`), the revenue is a lower bound. Say so.

## Output
Show a ranking table: rank, builder, volume (shares), active makers, and when asked notional (USDC), builder fees (USDC) and take rate (bps). Footer: sources, period, fetch time and units note.

Skill version: polymarket-builders v0.1.0 (Onchain Analyst)
