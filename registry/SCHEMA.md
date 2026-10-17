# Registry schema (`registry/apps.yaml`)

| Field | Type | Notes |
|---|---|---|
| `id` | slug | Unique, lowercase, `[a-z0-9-]+` |
| `name` | string | Display name |
| `category` | enum | `trading-app`, `wallet`, `terminal`, `exchange`, `dex`, `prediction-market`, `protocol` |
| `hyperliquid.builders[]` | list | `address` (lowercase 0x + 40 hex), optional `label`, `first_seen` (date), `verified` (object or `false`) |
| `polymarket.builder_codes[]` | list | bytes32 (0x + 64 hex) |
| `defillama.slug` / `defillama.perps` | string | Fee-dashboard slug (parent) / perps child slug |
| `polygon.contracts` | map | Name → address (checksummed as published) |
| `solana.programs` / `solana.fee_wallets` | list | Base58, informational (post-MVP) |
| `sources[]` | list | Where the identifiers were found |
| `notes` | string | Free text |

## Verifying an entry (all keyless)
- **HL builder:** `POST https://api.hyperliquid.xyz/info {"type":"referral","user":"<addr>"}` and check `builderRewards > 0`. Also check that `https://stats-data.hyperliquid.xyz/Mainnet/builder_fills/<addr>/<YYYYMMDD>.csv.lz4` returns 200 for a recent day (403 means there's no file).
- **PM builder code:** it appears in `https://data-api.polymarket.com/v2/builders/leaderboard?time_period=all`, or `https://clob.polymarket.com/builder/trades?builder_code=<code>` returns trades.
- **DefiLlama slug:** `https://api.llama.fi/summary/fees/<slug>?dataType=dailyFees` returns 200.

Local additions belong in `~/.onchain/registry.local.yaml` (same schema). They override or extend this file and are never committed.
