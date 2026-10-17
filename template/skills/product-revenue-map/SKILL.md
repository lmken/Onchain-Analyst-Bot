---
name: product-revenue-map
description: Use when asked how much any on-chain app, wallet, frontend or protocol makes (revenue, fees, volume, users) across all its products and chains. Maps the business model to on-chain footprints, measures each line once, rolls up with dedupe rules and cross-checks aggregators.
---
# Product revenue map (short)

Short version. Run onchain-update-skills to get the full one.

1. **Product:** read docs, fee page and the DefiLlama parent (`https://api.llama.fi/summary/fees/<slug>`, see `childProtocols[].methodology`). Note what it sells and who pays.
2. **Streams:** check each type: builder-fees, swap-fees, spread, protocol-fees, subscription, mev-priority, staking-yield, token-sales, referral, card-interchange, listing-fees, other. Flag off-chain lines as not visible.
3. **Footprint:** for each line note the chain and identifiers (HL builder address, Polymarket builder code, fee wallet, contract or program ID). Find them via DefiLlama adapters, docs, explorers, or a traced trade.
4. **Measure, then roll up:** one primary source per line, using the free on-chain source when one exists. Otherwise use the DefiLlama child split by chain via `totalDataChartBreakdown`.
   - Volume on the taker side only.
   - Never add a parent on top of its children, or an aggregator figure on top of an on-chain one for the same line.
   - Union users only within one address namespace.
5. **Cross-check:** compare each line with its DefiLlama child and the total with the parent. Explain gaps over 5% (scope, missing hours, fees vs revenue, attribution).

Toolkit: `onchain app <name> --window 30d`.

Skill version: product-revenue-map v0.1.0-short (Onchain Analyst)
