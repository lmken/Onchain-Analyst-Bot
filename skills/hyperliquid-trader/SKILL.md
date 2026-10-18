---
name: hyperliquid-trader
description: Use when asked about a specific Hyperliquid address — open positions, account value, recent fills, realized PnL net of fees, fee tier, or which frontends (builder codes) it trades through.
---
# Hyperliquid trader profile

## Fast path
`onchain hl trader <address> --window 30d`

## Raw path (keyless)
```bash
# smoke
curl -s https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' \
  -d '{"type":"clearinghouseState","user":"0x7975cafdff839ed5047244ed3a0dd82a89866081"}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['marginSummary']['accountValue'],len(d['assetPositions']))"
```
**Fills for a window.** Repeat with `startTime` = last fill `time` + 1 until a page returns fewer than 2,000:
```bash
curl -s https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' \
  -d '{"type":"userFillsByTime","user":"<addr>","startTime":<ms>,"endTime":<ms>,"aggregateByTime":false}'
```
- Fill fields: `coin, px, sz, side, dir, crossed, fee, feeToken, builderFee, closedPnl, startPosition, time, tid, oid, hash`.
- Other info types: `{"type":"userFees","user":…}` (fee tier, volume) and `{"type":"approvedBuilders","user":…}` (frontends the address has approved).

## Compute
- **Volume** = Σ |px×sz|. **Taker share** = crossed volume / volume.
- **Net realized PnL** = Σ closedPnl − Σ fee − Σ builderFee.
- **Frontends used:** fills with `builderFee > 0` were routed through a builder. Map approved builders to apps via the registry.

## Pitfalls
- Only the most recent **10,000 fills** are available. For very active traders, say the window may be cut off.
- Agent/API wallets trade on behalf of the master address. Use the master `user`.
- Unrealized PnL comes from `clearinghouseState` and is a point-in-time value. Give the time it was fetched (UTC).

## Output
Show a profile card (account value, positions table), then the window stats and PnL. End with the footer: sources, window, fetch time, and coverage (complete, or the 10k-fill caveat if it applies).

Skill version: hyperliquid-trader v0.1.1 (Onchain Analyst)
