# Example output: FOMO, 30-day product rollup

> **Snapshot.** Window **2026-09-17 → 2026-10-16 UTC** (30 complete UTC days), produced on 2026-10-17 with
> `onchain app fomo --window 30d` (toolkit 0.1.0, method 2026.10-3). Numbers are not updated; rerun for current data.
> FOMO is one worked example; the same method applies to any on-chain app (`product-revenue-map`).

**Bottom line:** across all products FOMO booked about **$22.7M in fees** and **$21.5M in revenue** in the window. Wallet swaps
(Solana ~$13.06M, EVM via Relay ~$8.06M in fees) dominate; Hyperliquid builder fees add $1.58M. Our total is within **0.8%** of
DefiLlama's parent figure ($22,531,680), which is a cross-check and is not added on top.

| Line | Chain | Fees (USD) | Revenue (USD) | Taker volume (USD) | Users | Source | Coverage |
|---|---|---:|---:|---:|---:|---|---|
| HL core perps (builder fees) | Hyperliquid | 1,379,560 | 1,379,560 | 2,949,048,395 | 21,569 | HL builder_fills feed + SQD gap-fill | 60/60 builder-days complete |
| HL HIP-3 perps (builder fees) | Hyperliquid | 204,072 | 204,072 | 407,313,782 | 9,530 | HL builder_fills feed + SQD gap-fill | 60/60 builder-days complete |
| HL spot / outcome | Hyperliquid | ~0 | ~0 | 66 | 2 | HL builder_fills feed + SQD gap-fill | 60/60 builder-days complete |
| Wallet swaps, Solana | Solana | 13,064,642 | 13,059,002 | 3,764,747,520 | — | DefiLlama `fomo` → Wallet [Solana] (daily) | aggregator |
| Wallet swaps, EVM via Relay | EVM | 8,064,935 | 6,817,151 | — | — | DefiLlama `fomo` → Wallet [excl. Solana] (daily) | aggregator |
| Off-chain | — | not measured | not measured | — | — | not visible on-chain | — |
| **Total** | | **22,713,208** | **21,459,785** | **7,121,109,763** | **25,452 HL users** | | 7% of revenue measured on-chain |

Users are unioned only within one address namespace (dedupe rule R6): 25,452 unique Hyperliquid traders across both FOMO builder
addresses. Wallet-swap users aren't measured keyless.

## Cross-checks (not added to the total)
| Check | DefiLlama (USD) | Ours (USD) | Delta |
|---|---:|---:|---:|
| Parent `fomo` total | 22,531,680 | 22,713,208 | +0.8% |
| Child "fomo Perps" vs HL core perps + HIP-3 | 1,402,103 | 1,583,632 | +12.9% |

DefiLlama's Hyperliquid `-perps` series includes HIP-3 but misses data on some days, so it runs low over a 30-day window
(see `docs/methodology.md`). A full-day SQD stream is the independent check for the builder lines.

## How it was measured
- Product first: list every revenue line (HL builder fees by asset class, wallet swaps by chain, off-chain), give each one primary source, then add the lines up with dedupe rules R1–R6 (`docs/methodology.md` §7): taker-side volume only, each fee once, never a parent on top of its children.
- Hyperliquid builder feed days that stopped early (25 of 30 days) were gap-filled from SQD Portal; all 30 days are complete.

---
Sources: Hyperliquid builder_fills feed (stats-data.hyperliquid.xyz), SQD Portal hyperliquid-fills, DefiLlama fees API (`fomo`, `fomo-perps`) | Window: 2026-09-17 → 2026-10-16 UTC (complete days) | Coverage: HL 30/30 days complete (5 feed-only, 25 gap-filled); wallet lines aggregator-sourced; off-chain not measured | Snapshot 2026-10-17
