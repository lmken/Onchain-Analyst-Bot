---
name: polymarket-wallets
description: Use when asked about a Polymarket wallet or trader — open and closed positions, realized/unrealized PnL, PnL over time, biggest wins, volume, or recent activity.
---
# Polymarket wallet profile

## Fast path
`onchain pm wallet <proxy_wallet>`

## Raw path (keyless)
```bash
# smoke
curl -s "https://data-api.polymarket.com/v2/user-stats?user=0x56687bf447db6ffa42ffe2204a05edaa20f55839" | python3 -c "import sys,json;d=json.load(sys.stdin)['data'];print(d['trades'],d['biggest_win'])"
```
- **Positions:** `https://data-api.polymarket.com/v2/positions?user=<wallet>&limit=50` (`status=open|closed`). Fields include `avg_price, current_value, realized_pnl, unrealized_pnl, total_pnl, entry_fees_usdc`.
- **PnL series:** `https://data-api.polymarket.com/v2/user-pnl?user=<wallet>&interval=1m&fidelity=1d`.
- **Activity:** `https://data-api.polymarket.com/v2/activity?user=<wallet>&limit=50` (type, usdc_size).
- **Trades:** `https://data-api.polymarket.com/v2/trades?user=<wallet>&limit=100`.
- **Leaderboard context:** `https://data-api.polymarket.com/v2/leaderboard`.
- **Pagination:** responses are `{data, pagination}`. Pass `cursor` from `pagination.next_cursor`.

## Pitfalls
- Use the **proxy wallet** (the address on the profile page), not the signer EOA.
- `user-stats.all_time_pnl` is an object. Report `realized_pnl`, `unrealized_pnl`, `settled_pnl` and its `timestamp`, because it is a snapshot.
- Resolved markets move value from unrealized to realized. Don't add the two across different snapshot times.

## Output
Show the stats card, a positions table sorted by current value, and the PnL trend. Footer: sources, window (fetch time, UTC) and coverage (complete, or partial if paging stopped early).

Skill version: polymarket-wallets v0.1.1 (Onchain Analyst)
