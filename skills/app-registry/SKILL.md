---
name: app-registry
description: Use to look up, add or verify which Hyperliquid builder addresses, Polymarket builder codes or DefiLlama slugs belong to an app, wallet or trading frontend.
---
# App registry

The registry is `{REPO_RAW}/{TAG}/registry/apps.yaml`. Read it with `curl -sf`; its field rules are in `registry/SCHEMA.md`.

## Look up
- Search `apps[]` by `id`, `name`, or any `hyperliquid.builders[].address` / `polymarket.builder_codes[]`.
- Toolkit: `onchain registry show <app>`, `onchain registry list`.
- Prefer entries whose `verified` is set. Treat `verified: false` as a lead, not a fact.

## Verify an entry (keyless)
- **HL builder:** `builderRewards` should be > 0.
  ```bash
  # smoke
  curl -s https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' \
    -d '{"type":"referral","user":"0xe966a12bf7b93838096e4519a684519ab22df618"}' | python3 -c "import sys,json;print(float(json.load(sys.stdin)['builderRewards'])>0)"
  ```
  Also check that a recent feed day exists:
  ```bash
  curl -s -o /dev/null -w "%{http_code}" https://stats-data.hyperliquid.xyz/Mainnet/builder_fills/<addr>/<YYYYMMDD>.csv.lz4
  ```
  200 means it exists; 403 means there's no file that day.
- **PM builder code:** it appears in `https://data-api.polymarket.com/v2/builders/leaderboard?time_period=all&limit=100`, or `https://clob.polymarket.com/builder/trades?builder_code=<code>` returns data.
- **DefiLlama slug:** `https://api.llama.fi/summary/fees/<slug>?dataType=dailyFees` returns 200.
- Toolkit: `onchain registry verify [<app>]`.

## Add or correct an entry
1. Find a public source for the identifier: the app's docs, a DefiLlama adapter, an explorer label. Never guess from similar names.
2. Verify it as above.
3. Save it in `~/.onchain/registry.local.yaml` with the same schema (`apps: - id: …`) and record the source URL. Local entries override or extend the bundled file.
4. If it's useful to everyone, suggest the user open a pull request on the repo. Never open one yourself.

## Pitfalls
- Addresses are lowercase 0x + 40 hex characters. PM builder codes are 0x + 64 hex characters.
- Apps rotate builder addresses (e.g. a new main address plus a legacy one). Sum all verified ones.

Skill version: app-registry v0.1.0 (Onchain Analyst)
