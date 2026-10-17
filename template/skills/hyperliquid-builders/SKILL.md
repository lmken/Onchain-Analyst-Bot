---
name: hyperliquid-builders
description: Use for Hyperliquid builder codes and the frontends behind them (wallets, trading apps, terminals) — builder revenue, volume, unique traders, take rate, retention, whale concentration, rankings or comparisons.
---
# Hyperliquid builders (starter)

1. **Find the app's builder address(es)** in the registry: `{REPO_RAW}/{TAG}/registry/apps.yaml`. Sum multiple addresses.
2. **Lifetime rewards:**
   ```bash
   curl -s https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"referral","user":"<addr>"}'
   ```
   Read `builderRewards`.
3. **One UTC day:**
   ```bash
   curl -sfO {REPO_RAW}/{TAG}/docs/snippets/hl_builder_day.py && python3 hl_builder_day.py <addr> <YYYY-MM-DD>
   ```
   It decodes the feed when lz4 is available, detects truncation and gap-fills from SQD. It returns status, builder_fee_usd, volume_usd and unique_traders.
4. **A window:** run each day of the window and sum fees and volume. Traders need the union of users, which the toolkit handles: `onchain hl builder <app> --window 30d`.
5. **Verify:** compare with DefiLlama `https://api.llama.fi/summary/fees/<app>-perps?dataType=dailyFees` for the same days, within about 10%.
6. **Report** revenue, volume, traders and take rate, plus coverage (days complete/gapfilled/partial).

The full version adds raw SQD bodies, cohorts, concentration and asset mix. Say "update skills" to get it.

Skill version: hyperliquid-builders v0.1.0-short (Onchain Analyst)
