---
name: polymarket-markets
description: Use for finding Polymarket markets or events and their prices, price history, order book, liquidity, open interest, top holders or recent trades.
---
# Polymarket markets

## Fast path
`onchain pm markets --q "<text>"` · `onchain pm market <slug> --holders 10 --history 1m`

## Raw path (keyless)
```bash
# smoke
curl -s "https://gamma-api.polymarket.com/public-search?q=fed&limit_per_type=3" | python3 -c "import sys,json;d=json.load(sys.stdin);print([m['slug'] for e in d.get('events',[]) for m in e.get('markets',[])][:3])"
```
- **Market by slug:** `https://gamma-api.polymarket.com/markets?slug=<slug>`. Key fields: `conditionId`, `clobTokenIds` (JSON string, one per outcome), `outcomes`, `outcomePrices`, `volume`, `volume24hr`, `liquidityNum`, `endDate`, `negRisk`, `feesEnabled`, `feeSchedule`.
- **Price history:** `https://clob.polymarket.com/prices-history?market=<token_id>&interval=1d|1w|1m|max&fidelity=60` → `history[{t,p}]`.
- **Order book:** `https://clob.polymarket.com/book?token_id=<token_id>`.
- **Top holders:** `https://data-api.polymarket.com/v2/holders?condition=<conditionId>&limit=20`. The parameter is `condition`, not `market`.
- **Open interest:** `https://data-api.polymarket.com/v2/oi?condition=<conditionId>`.
- **Recent trades:** `https://data-api.polymarket.com/v2/trades?condition=<conditionId>&limit=50` (add `taker_only=true` to avoid double counting).
- **Active markets by 24h volume:** `https://gamma-api.polymarket.com/markets?active=true&closed=false&order=volume24hr&ascending=false&limit=20`.

## Pitfalls
- Prices are probabilities in [0,1]. An event can hold several markets; neg-risk events share collateral.
- Use `clobTokenIds[i]` for the outcome you mean. Index 0 is usually "Yes".
- Volume fields are USDC notional on Gamma. That's different from the builder leaderboard, which uses shares.

## Output
Show the market table (question, price, 24h volume, liquidity, end date), then holders or history if asked. Footer: sources and fetch time (UTC).

Skill version: polymarket-markets v0.1.0 (Onchain Analyst)
