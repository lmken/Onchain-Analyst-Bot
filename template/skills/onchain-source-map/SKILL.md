---
name: onchain-source-map
description: Use before answering any on-chain, Hyperliquid, Polymarket or protocol-fee question, to pick the right free public source and respect its limits.
---
# Source map (starter)

All sources are free and keyless.

| Question | Endpoint |
|---|---|
| HL builder lifetime rewards | `POST https://api.hyperliquid.xyz/info` `{"type":"referral","user":"<addr>"}` → `builderRewards` |
| HL builder daily fills | `https://stats-data.hyperliquid.xyz/Mainnet/builder_fills/<addr_lowercase>/<YYYYMMDD>.csv.lz4` (lz4; 403 = no file) |
| Fill missing feed hours | `POST https://portal.sqd.dev/datasets/hyperliquid-fills/stream` (builder filter) |
| HL trader | HL info `clearinghouseState`, `userFillsByTime` |
| PM markets / prices | `https://gamma-api.polymarket.com/public-search?q=`, `https://clob.polymarket.com/prices-history?market=<token>` |
| PM wallets / holders | `https://data-api.polymarket.com/v2/positions?user=`, `/v2/user-stats?user=`, `/v2/holders?condition=` |
| PM builders | `https://data-api.polymarket.com/v2/builders/leaderboard?time_period=week`; revenue `https://clob.polymarket.com/builder/trades?builder_code=` |
| Fees / revenue | `https://api.llama.fi/summary/fees/<slug>?dataType=dailyFees|dailyRevenue|dailyHoldersRevenue` |
| Prices | `https://coins.llama.fi/prices/current/coingecko:<id>` |
| Whole-company revenue (any app) | follow product-revenue-map |

- **Pace:** about 1 request per second to HL info and DefiLlama. Retry SQD on `overloaded`.
- **Don't use:** Dune Sim, Flipside, Goldsky Polymarket subgraphs.
- The full version adds per-source limits, licences and more endpoints. Say "update skills" to get it.

Skill version: onchain-source-map v0.1.0-short (Onchain Analyst)
