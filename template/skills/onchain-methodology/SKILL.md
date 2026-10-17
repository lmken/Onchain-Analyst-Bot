---
name: onchain-methodology
description: Use before reporting any on-chain metric (revenue, volume, traders, retention, PnL, fees), or when asked how a number was computed or whether it can be trusted.
---
# Methodology checks (starter)

1. **Complete UTC days only.** "Last 30 days" = the 30 complete UTC days ending yesterday.
2. **The HL builder feed is often truncated.** Many days stop around 12:00 UTC. Check the last fill's hour.
   - If it isn't 23, fill the rest of the day from SQD (builder filter), or label the day `partial`.
   - Day labels: `complete` / `gapfilled` / `partial` / `missing`.
   - If any day is partial, call the totals a lower bound.
3. **Formulas:**
   - **Builder revenue** = Σ builder_fee.
   - **Volume** = Σ |px×sz|. Taker volume uses `crossed = true` only.
   - **Unique traders** = distinct users across the window: a set union, not a sum of days.
   - **Take rate (bps)** = revenue / volume × 10,000.
4. **Polymarket:**
   - Leaderboard volume is in **shares**, and `active_users` counts distinct makers.
   - Builder revenue = Σ `builderFee` from CLOB `/builder/trades`.
   - Taker fee = shares × rate × p × (1 − p).
5. **DefiLlama:** fees ≠ revenue ≠ holders revenue. The latest day may be restated.
6. **Verify:** compare core-perps builder revenue (excluding HIP-3 `dex:COIN` fills) with DefiLlama `<app>-perps` for the same days, within about 10%.
7. **Footer:** `Sources | Window (UTC, complete days) | Coverage N/N | Onchain Analyst version`.

Full formulas (cohorts, concentration, PnL) are in the full version. Say "update skills" to get it.

Skill version: onchain-methodology v0.1.0-short (Onchain Analyst)
