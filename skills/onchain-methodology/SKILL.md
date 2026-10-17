---
name: onchain-methodology
description: Use before reporting any on-chain metric (revenue, volume, traders, retention, PnL, fees), or when asked how a number was computed or whether it can be trusted.
---
# Methodology checks

Apply every rule here before you state a number. Full definitions and worked examples are in `{REPO_RAW}/{TAG}/docs/methodology.md`.

## Time
1. **Use complete UTC days only.** "Last 30 days" means the 30 complete UTC days ending yesterday (UTC). Never include today unless asked, and then label it "partial day".
2. Give dates in UTC. Add the user's local time only as a label.

## Coverage (Hyperliquid builder feed)
3. The builder_fills feed is often **truncated**: many days stop around 12:00 UTC.
   - For each day, record `feed_hours` (distinct UTC hours with fills) and `last_feed_time`.
   - If the last fill isn't in hour 23, or a busy day (≥500 rows) has empty hours, the day is incomplete.
4. Fill those gaps from SQD Portal (builder-filtered). Label each day:
   - `complete`: the feed covers 24h
   - `gapfilled`: feed + SQD
   - `partial`: still missing hours
   - `missing`: no file and no gap-fill
5. If any day in the window is `partial` or `missing`, say so and call totals a **lower bound**.

## Formulas
- **Builder revenue** = Σ `builder_fee` (USDC-type tokens; report other tokens separately).
- **Routed volume** = Σ |px × sz| over all builder fill rows. **Taker volume** = the same but only `crossed = true`. Use taker volume when comparing with venue-wide totals.
- **Unique traders** = distinct `user`. **Take rate (bps)** = revenue / volume × 10,000.
- **Whale concentration:** share of volume from the top 1%, 1–5%, 5–10%, 10–25%, 25–50% and bottom 50% of traders, plus HHI = Σ share².
- **New vs returning:** a trader is new on the day of their first-ever fill with that builder. That needs history back to the builder's `first_seen`; otherwise say "new within the window".
- **Weekly retention:** cohort = ISO week of first fill; value = share of the cohort active in week k.
- **HL trader net realized PnL** = Σ closedPnl − Σ fee − Σ builderFee. `fee` is negative for maker rebates.
- **Polymarket taker fee** = shares × rate × p × (1 − p). Makers pay 0.
  - Rates (Oct 2026): crypto 0.07; sports 0.05; politics/finance/tech/mentions 0.04; economics/culture/weather/other 0.05; geopolitics 0.
  - Prefer the market's own `feeSchedule` / `feesEnabled`.
- **PM builder revenue** = Σ `builderFee` from CLOB `/builder/trades`. **Notional** = Σ `sizeUsdc`.

## Traps
- PM leaderboard `volume` is **shares**, and `active_users` counts distinct makers. Never label either as USD or "users".
- An app can have several builder addresses (registry). Sum them, and say that you did.
- DefiLlama restates the latest day for about 24h. Fees ≠ revenue ≠ holders revenue: quote their `methodology`.
- `userFillsByTime` only returns a trader's last 10,000 fills.
- A "registry cohort share" is a share among listed builders, not of all of Hyperliquid.

## Verify before answering
- Cross-check builder revenue against DefiLlama `<app>-perps` (if listed) for the same UTC window, comparing day by day. DefiLlama's `-perps` includes HIP-3 (`dex:COIN`) fills. Expect about 1% agreement on most days, plus some days where DefiLlama is low (gaps in its indexer). An independent check is a full-day SQD stream for the builder.
- Check that lifetime totals don't exceed `referral.builderRewards`.
- Explain any gap rather than hiding it.

## Footer on every answer
`Sources: … | Window: YYYY-MM-DD → YYYY-MM-DD UTC (complete days) | Coverage: N/N days complete (statuses) | Method: Onchain Analyst v0.1.0`

Skill version: onchain-methodology v0.1.0 (Onchain Analyst)
