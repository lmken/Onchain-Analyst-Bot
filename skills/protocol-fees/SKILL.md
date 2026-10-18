---
name: protocol-fees
description: Use for a protocol's or app's fees, revenue or holders revenue over time, fee rankings across protocols, or current token prices.
---
# Protocol fees, revenue and prices (DefiLlama)

## Fast path
`onchain fees <slug> --type fees|revenue|holders --window 30d` · `onchain fees-top --top 20` · `onchain price hyperliquid bitcoin`

## Raw path (keyless)
```bash
# smoke
curl -s "https://api.llama.fi/summary/fees/hyperliquid?dataType=dailyRevenue" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['name'],d['total30d'],len(d['totalDataChart']))"
```
- `dataType`: `dailyFees` (everything users pay), `dailyRevenue` (what the protocol keeps), `dailyHoldersRevenue` (buybacks, burns, distributions).
- Response: `total24h/7d/30d/1y`, `totalAllTime`, `totalDataChart` [[unix_ts, usd]], `childProtocols`, `methodology`.
- **Window sum:** add `totalDataChart` values whose UTC date is inside the window.
- **Parent vs child:** for example `fomo` (parent) vs `fomo-perps` (child). Use the child for HL builder comparisons.
- **Rankings:** `https://api.llama.fi/overview/fees?excludeTotalDataChart=true` → `protocols[]` with `total24h`, `total30d`, `category`, `slug`.
- **Prices:**
```bash
# smoke
curl -s "https://coins.llama.fi/prices/current/coingecko:hyperliquid" | python3 -c "import sys,json;print(json.load(sys.stdin)['coins'])"
```
  - Fallback: `https://api.coingecko.com/api/v3/simple/price?ids=<id>&vs_currencies=usd` (keyless, low limits).

## Pitfalls
- The latest day is often restated for about 24h. Prefer complete days that are at least a day old.
- Don't mix fees and revenue. Quote the `methodology` text for the protocol.
- Derivatives endpoints under `pro-api` / `api/…` are paid (HTTP 402). Don't use them.
- Licence: DefiLlama data is for personal/non-commercial use; cite "Source: DefiLlama".

## Output
Show totals for the window plus a short daily or weekly series, and the methodology line. Footer: sources, window (complete UTC days), coverage (latest day may be restated), fetch time.

Skill version: protocol-fees v0.1.1 (Onchain Analyst)
