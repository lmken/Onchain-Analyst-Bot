# Sources (all keyless, public). Checked 2026-10-17

| Source | Base URL | Main endpoints | Limits | Freshness | Terms |
|---|---|---|---|---|---|
| Hyperliquid info | `https://api.hyperliquid.xyz/info` (POST JSON) | `referral`, `clearinghouseState`, `userFillsByTime`, `userFees`, `approvedBuilders`, `meta` | 1,200 weight/min/IP; most calls 20, `allMids`/`clearinghouseState` 2 | real time | Hyperliquid terms |
| Hyperliquid builder fills | `https://stats-data.hyperliquid.xyz/Mainnet/builder_fills/{addr}/{YYYYMMDD}.csv.lz4` | daily CSV (LZ4 frame) | be polite | next day; often truncated (see methodology) | Hyperliquid terms |
| SQD Portal | `https://portal.sqd.dev/datasets/hyperliquid-fills` | `GET /head`, `POST /stream` | public tier about 20 req/10 s; retry on `overloaded` (HTTP 529); usage caps may apply | near real time | non-commercial public tier |
| Polymarket Gamma | `https://gamma-api.polymarket.com` | `/public-search`, `/markets`, `/events` | 4,000/10 s overall; `/markets` 300/10 s | real time | Polymarket API terms |
| Polymarket CLOB | `https://clob.polymarket.com` | `/book`, `/prices-history`, `/sampling-markets`, `/builder/trades` | 9,000/10 s | real time | Polymarket API terms |
| Polymarket Data API v2 | `https://data-api.polymarket.com/v2` | `trades`, `positions`, `user-pnl`, `user-stats`, `activity`, `holders` (param `condition`), `oi`, `leaderboard`, `builders/leaderboard`, `builders/volume` | 800/10 s | real time | Polymarket API terms; capital-markets entities must contact Polymarket |
| DefiLlama | `https://api.llama.fi` | `/summary/fees/{slug}?dataType=` (`totalDataChartBreakdown` = per chain × child), `/summary/dexs/{slug}`, `/overview/fees`, `/overview/dexs` | free tier; about 1 req/s is safe | daily; last day restated | personal/non-commercial, attribution |
| Solana public RPC | `https://api.mainnet-beta.solana.com` (POST JSON-RPC) | `getSignaturesForAddress` (1,000 per call), `getTransaction` (`jsonParsed`, `maxSupportedTransactionVersion: 1`, since v1 transactions exist), `getTokenAccountsByOwner` | about 10 req/s per IP; heavy calls lower; limited history | real time | Solana Foundation public endpoint, not for production; spot checks only |
| DefiLlama coins | `https://coins.llama.fi` | `/prices/current/{ids}` | as above | about 5 min | as above |
| CoinGecko (fallback) | `https://api.coingecko.com/api/v3` | `/simple/price` | very low keyless limits | about 1 min | attribution required |
| GitHub (skills/registry) | `https://raw.githubusercontent.com/lmken/Onchain-Analyst-Bot/{tag}/…` | static files | raw: generous; API 60/h unauthenticated | per release | MIT |

## Not used (dead, deprecated or paid)
- Dune Sim (sunset Aug 2026)
- Flipside (shut down Jun 2026)
- Goldsky Polymarket subgraphs (`ENDPOINT_DEPRECATED`)
- DefiLlama Pro/derivatives endpoints (HTTP 402)
- Paid providers, as later optional add-ons only: Dune, Nansen, Allium, Helius and others.
