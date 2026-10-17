---
name: hyperliquid-builders
description: Use for Hyperliquid builder codes and the frontends behind them (wallets, trading apps, terminals) — builder revenue, volume, unique traders, take rate, retention, whale concentration, rankings or comparisons.
---
# Hyperliquid builders

Follow onchain-source-map for limits and onchain-methodology for rules.

## 1. Resolve the app to builder addresses
- Look up the app in `{REPO_RAW}/{TAG}/registry/apps.yaml` (`hyperliquid.builders[].address`).
- Use only entries with `verified`. If an app has several addresses, sum them.
- If the app isn't listed, see app-registry.

## 2. Fast path (toolkit installed)
```bash
onchain hl builders --window 30d --top 20           # leaderboard over registry builders
onchain hl builder <app> --window 30d --cohorts     # one app; history from first_seen for new vs returning
onchain hl reconcile <app> --window 30d             # vs DefiLlama and lifetime builderRewards
```
Gap-fill from SQD is on by default. A cold 30-day run for a large builder can take about 30 minutes; results are cached in `~/.onchain/days/`.

## 3. Raw path (no toolkit)
**a. Lifetime rewards (a quick sanity number):**
```bash
# smoke
curl -s https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' \
  -d '{"type":"referral","user":"0x7975cafdff839ed5047244ed3a0dd82a89866081"}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['builderRewards'])"
```
**b. One UTC day with coverage + gap-fill.** Uses the stdlib script, plus `lz4` if available; without lz4 it uses SQD only:
```bash
curl -sfO {REPO_RAW}/{TAG}/docs/snippets/hl_builder_day.py
python3 hl_builder_day.py <builder_addr> 2026-10-15        # JSON: status, builder_fee_usd, volume_usd, unique_traders, …
```
Loop over the days of the window and sum. Unique traders across a window need a set union of `user`, not a sum of daily counts. To get that, keep users per day, or use the toolkit.

**c. Inspect the feed yourself (needs `pip install lz4`):**
```bash
curl -s -o d.csv.lz4 https://stats-data.hyperliquid.xyz/Mainnet/builder_fills/<addr_lowercase>/<YYYYMMDD>.csv.lz4
python3 -c "import lz4.frame;open('d.csv','wb').write(lz4.frame.decompress(open('d.csv.lz4','rb').read()))"
```
- Columns: `time` (ISO, seconds), `user`, `coin`, `side`, `px`, `sz`, `crossed`, `special_trade_type`, `tif`, `is_trigger`, `counterparty`, `closed_pnl`, `twap_id`, `builder_fee`.
- There's no fee-token column, so assume USDC.

**d. SQD gap-fill body** (blocks run about 14 per second; bisect `header.timestamp` in ms to find the hour bounds):
```json
{"type":"hyperliquidFills","fromBlock":B0,"toBlock":B1,
 "fields":{"block":{"number":true,"timestamp":true},"fill":{"user":true,"coin":true,"px":true,"sz":true,"time":true,"crossed":true,"builderFee":true,"feeToken":true}},
 "fills":[{"builder":["<addr_lowercase>"]}]}
```
- The response is JSON lines.
- If the last `header.number` is below `toBlock`, continue from last+1.
- Keep only fills with `time` inside the gap, so nothing is double-counted with the feed.

## 4. Metrics to report
- Revenue, routed volume, taker volume, unique traders, fills, take rate (bps), revenue per trader.
- Asset mix: perps; spot (`@…`); HIP-3 (`dex:COIN`).
- Concentration (top 1% / 10% share).
- New vs returning and weekly retention when asked.
- Compare with the previous equal window when useful.

## 5. Verify
- DefiLlama `https://api.llama.fi/summary/fees/<app>-perps?dataType=dailyFees` (if the registry lists `defillama.perps`) for the same UTC days includes HIP-3 (`dex:COIN`) fills. Compare **day by day**: matching days agree within about 1%. DefiLlama's own indexer misses data on some days, which shows up as DefiLlama 10–40% lower. Report the number of matching days and the gap; a window total alone can hide offsetting errors.
- The sum since `first_seen` must be ≤ `builderRewards`.
- If either check fails, say so and show both numbers.

## Output
Lead with the table, then add 2–3 lines of interpretation and the methodology footer, including coverage, e.g. "30/30 days complete (12 complete, 18 gapfilled)".

Skill version: hyperliquid-builders v0.1.0 (Onchain Analyst)
