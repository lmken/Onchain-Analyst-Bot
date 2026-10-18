# Onchain Analyst

A **Grok Bot template plus skills** for on-chain analysis from **free, keyless, public data**:

- Hyperliquid builder codes and traders
- Polymarket markets, wallets and builders
- protocol fees and revenue from DefiLlama
- token prices

Every number comes with its **sources** and a **coverage** label. The bot is read-only: it never trades, signs, posts or sends anything.

## How it works
- **No infrastructure of ours.** Each copy of the bot queries public sources straight from its own computer. This repo holds static files only: skills, registry and docs, plus an optional toolkit.
- **Skills come first.** `skills/<slug>/SKILL.md` is the guide for each question type:
  - which source to use, with exact endpoints and request bodies
  - pitfalls and methodology checks
  - how to verify a result
  - raw `curl` + Python-standard-library snippets, so the skills work even without the toolkit
- **Optional toolkit.** `onchain` is a small Python CLI the skills can call as a shortcut. It adds caching, pagination, pacing, lz4 decoding, SQD gap-fill and cohort maths.

| Source | Used for | Key? |
|---|---|---|
| Hyperliquid info API | builder rewards, traders, positions, fills | none |
| Hyperliquid builder_fills feed (`stats-data.hyperliquid.xyz`) | per-builder daily fills | none |
| SQD Portal `hyperliquid-fills` | filling hours missing from the feed | none (public tier) |
| Polymarket Gamma / CLOB / Data API v2 | markets, prices, holders, wallets, builders | none |
| DefiLlama API + coins API | fees, revenue, holders revenue, prices | none |

## Install the bot
1. Add the **Onchain Analyst** template in Grok Bot.
2. Its getting-started skill checks your skills against the pinned release here (`skills/manifest.json`, sha256-checked).
3. It asks before adding or upgrading anything.
4. To refresh later, say **"update skills"**.

## Install the optional toolkit by hand
```bash
python3 -m venv ~/.onchain/venv
~/.onchain/venv/bin/pip install "git+https://github.com/lmken/Onchain-Analyst-Bot@v0.1.2"
~/.onchain/venv/bin/onchain setup && ~/.onchain/venv/bin/onchain doctor --live
```
Some examples:
```bash
onchain hl builders --window 30d --top 20          # HL builder leaderboard (SQD gap-fill on by default)
onchain hl builder fomo --window 30d --cohorts     # one app: revenue, traders, concentration, retention
onchain hl reconcile fomo --window 30d             # fills vs DefiLlama vs lifetime builderRewards
onchain pm builders --period week --revenue        # Polymarket builders + builder-fee revenue
onchain fees hyperliquid --type revenue --window 90d
onchain price hyperliquid bitcoin
```

## Data notes
- **Complete UTC days only.** A `30d` window means the last 30 complete UTC days.
- **The Hyperliquid builder_fills feed is often truncated.** Many days stop around 12:00 UTC. The toolkit and skills detect this and fill the gap from SQD Portal. Each day is labelled `complete`, `gapfilled`, `partial` or `missing`.
- **Polymarket units.** The builder leaderboard reports volume in **shares**, not USD. Builder revenue comes from CLOB `/builder/trades` (`builderFee`, USDC).

## Licences and attribution
- **This repo:** MIT.
- **Data:** each source keeps its own terms.
  - DefiLlama data is free for personal/non-commercial use with attribution.
  - Polymarket's API terms apply. Capital-markets entities must contact Polymarket.
  - SQD's public portal is for non-commercial use.
- **Layout:** see `docs/sources.md`.

## Repo layout
```
skills/      14 skills + manifest.json (onboarded into each bot)
template/    getting-started skill, short versions of 7 core skills, profile/memory text
registry/    apps.yaml: app → HL builder addresses, Polymarket builder codes, DefiLlama slugs
docs/        methodology.md, sources.md, snippets/ (stdlib scripts)
src/onchain/ optional toolkit (`onchain` CLI)
scripts/     build_manifest.py, lint_skills.py
tests/       unit, skills, snippets (live, opt-in)
```
