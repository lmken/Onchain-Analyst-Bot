---
name: polymarket-builders
description: Use for Polymarket builder codes (apps that route orders to Polymarket) — rankings by volume, active makers, builder-fee revenue, notional and take rate over a day, week or month.
---
# Polymarket builders (starter)

1. **Ranking:** `https://data-api.polymarket.com/v2/builders/leaderboard?time_period=day|week|month|all&limit=20`.
   - `volume` is in **shares**, not USD.
   - `active_users` = distinct makers.
2. **Revenue:** page `https://clob.polymarket.com/builder/trades?builder_code=<bytes32>` (newest first, 300 per page, `next_cursor` until `LTE=`; `matchTime` = unix seconds).
   - Sum `builderFee` (USDC) for revenue, `sizeUsdc` for notional, `feeUsdc` for platform fees.
   - Script: `curl -sfO {REPO_RAW}/{TAG}/docs/snippets/pm_paginate.py && python3 pm_paginate.py <code> 168`
3. Many builders charge a 0 builder fee, so 0 revenue with high volume is normal.
4. If paging didn't reach the window start, revenue is a lower bound. Say so.
5. Footer: sources, window (period), coverage (lower bound if paging stopped early).

The full version adds daily series and more pitfalls. Say "update skills" to get it.

Skill version: polymarket-builders v0.1.1-short (Onchain Analyst)
