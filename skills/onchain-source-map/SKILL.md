---
name: onchain-source-map
description: Use before answering any on-chain, Hyperliquid, Polymarket or protocol-fee question, to pick the right free public source and respect its limits.
---
# Source map

All sources below are free, public and keyless. Query them directly from this computer. Never ask the user for a key to answer an MVP question.

## Which source answers which question
| Question | Source | Endpoint (exact) |
|---|---|---|
| HL builder lifetime rewards | HL info | `POST https://api.hyperliquid.xyz/info` `{"type":"referral","user":"<addr>"}` → `builderRewards` |
| HL builder daily fills, revenue, traders | HL builder_fills feed | `GET https://stats-data.hyperliquid.xyz/Mainnet/builder_fills/<addr_lowercase>/<YYYYMMDD>.csv.lz4` (lz4 frame; 403 = no file) |
| Missing hours of the feed; any HL fills by builder/user | SQD Portal | `POST https://portal.sqd.dev/datasets/hyperliquid-fills/stream`, `GET …/head` |
| HL trader positions / fills / fees | HL info | `clearinghouseState`, `userFillsByTime` (≤2,000 per call, last 10k fills only), `userFees` |
| Polymarket market search / metadata | Gamma | `https://gamma-api.polymarket.com/public-search?q=`, `/markets?slug=` |
| PM price history / order book | CLOB | `https://clob.polymarket.com/prices-history?market=<token_id>&interval=1m&fidelity=60`, `/book?token_id=` |
| PM holders, OI, trades, wallets | Data API v2 | `https://data-api.polymarket.com/v2/holders?condition=`, `/v2/oi`, `/v2/trades`, `/v2/positions?user=`, `/v2/user-stats?user=`, `/v2/user-pnl?user=` |
| PM builder rankings | Data API v2 | `/v2/builders/leaderboard?time_period=day|week|month|all`, `/v2/builders/volume?builder_code=` |
| PM builder revenue | CLOB | `/builder/trades?builder_code=<bytes32>` (300 per page, `next_cursor`) |
| Protocol fees / revenue / holders revenue | DefiLlama | `https://api.llama.fi/summary/fees/<slug>?dataType=dailyFees|dailyRevenue|dailyHoldersRevenue` |
| Fee rankings | DefiLlama | `https://api.llama.fi/overview/fees` |
| Token prices | DefiLlama coins | `https://coins.llama.fi/prices/current/coingecko:<id>`; fallback `https://api.coingecko.com/api/v3/simple/price?ids=<id>&vs_currencies=usd` |
| Whole-company revenue of any app (all products, chains) | product-revenue-map | DefiLlama `totalDataChartBreakdown` split by chain and child, plus on-chain lines |
| Solana fee wallet / token account spot check | Solana public RPC | `POST https://api.mainnet-beta.solana.com` `getSignaturesForAddress`, `getTransaction` (`maxSupportedTransactionVersion: 1`) |
| Which address/code belongs to an app | Registry | `{REPO_RAW}/{TAG}/registry/apps.yaml` (see app-registry) |

`{REPO_RAW}` and `{TAG}` are recorded in the memory `onchain-skills-manifest`.

## Limits (stay well under them)
- **HL info:** 1,200 weight/min per IP. Most calls weigh 20, so about one call per second.
- **SQD public:** about 20 requests per 10 s. A JSON body containing `"overloaded"` (or HTTP 429/529) means wait and retry with backoff.
- **Polymarket:** Gamma 300/10 s on `/markets`; Data v2 800/10 s; CLOB 9,000/10 s. Cloudflare slows requests down rather than rejecting them.
- **DefiLlama free:** keep it under about 1 request per second. `/api/…` derivatives endpoints are paid (HTTP 402), so don't use them.
- **CoinGecko keyless:** a few calls per minute only.

## Dead or wrong sources (don't use)
- Dune Sim (sunset), Flipside (shut down), Goldsky Polymarket subgraphs (deprecated).
- Polymarket leaderboard `volume` used as USD. It is in **shares**.

## Licences to mention when relevant
- DefiLlama: personal/non-commercial use, with attribution.
- SQD public portal: non-commercial.
- Polymarket: capital-markets entities must contact Polymarket.

## Optional toolkit
If the memory says `toolkit: installed`, the `onchain` commands named in each skill are faster shortcuts. They hit the same sources. `onchain doctor --live` checks all of them.

Skill version: onchain-source-map v0.1.0 (Onchain Analyst)
