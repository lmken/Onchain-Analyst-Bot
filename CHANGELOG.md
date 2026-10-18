# Changelog

## v0.1.3 (2026-10-17)
- Optional auto-updates: setup asks each owner once whether to install updates automatically or ask first (default ask), saved as `update_mode: auto|ask` in `onchain-skills-manifest`; switch anytime ("update automatically" / "ask before updating"). In auto mode the weekly routine installs changed, new and `-short` upgrades after sha256 and byte checks, then sends a short note. Even in auto mode, skills the user edited are never overwritten, and removed skills never deleted, without asking.
- `onchain-update-skills` (full v0.1.2, short v0.1.2-short): handles `update_mode`; routines change skills only in auto mode; each run refreshes the routine prompt if it differs from getting-started.
- Anonymous update-check count: the check downloads `releases/latest/download/manifest.json` (a counted release asset; no identity), with the `releases/latest` API and raw-tag manifest as fallback. Every release now attaches `skills/manifest.json` (`scripts/release.sh`, `CONTRIBUTING.md`, `docs/telemetry.md`).
- `onchain-getting-started` (v0.1.3): asks the update-mode question, new routine prompt, keeps an existing routine's prompt current; pinned `TAG` is now v0.1.3. Profile describes both modes; toolkit version 0.1.3.

## v0.1.2 (2026-10-17)
- Fix: report files were sometimes delivered as a Markdown link to a `file://` or local path, which doesn't open in chat. `onchain-report` (v0.1.1) gains a "Delivering files" rule: attach every memo, CSV or chart in chat, never link a local path (mention it only as plain code text). `product-revenue-map` (full v0.1.1, short v0.1.1-short) points its file output to the same rule. Profile states it too.
- `onchain-getting-started`: pinned `TAG` is now v0.1.2; toolkit version 0.1.2.

## v0.1.1 (2026-10-17)
- Weekly update check: every copy of the bot gets a read-only routine, "Check for skill updates" (Mondays ~9am, user's time zone). It tells the user when a newer release is out and offers to run `onchain-update-skills`. It never installs, overwrites or deletes skills without a yes in chat.
- `onchain-update-skills` (full and short): new check-only mode for routines (steps 1–3, silent when up to date); applying changes still needs the user's yes in chat. Each run recreates the routine if it's missing.
- `onchain-getting-started`: new step 7 creates the routine on first run if it's missing (repo hardcoded so it works without memory); pinned `TAG` is now v0.1.1.
- Profile mentions the update routine; toolkit version 0.1.1.

## v0.1.0 (2026-10-17)
- First release: 15 skills (skills-first; raw `curl` + Python-stdlib paths), with short versions of 7 core skills.
- Product-first method for any app: `product-revenue-map` skill, registry `product_lines`, `onchain app <name>` rollup with dedupe rules R1–R6 and DefiLlama cross-checks; worked examples for a social trading app, a wallet, and a Polymarket builder frontend.
- Registry seed: 11 verified Hyperliquid builder addresses (10 apps) and the Polymarket contracts and builders.
- Optional `onchain` toolkit covering:
  - Hyperliquid builders, with SQD gap-fill and completeness labels
  - Hyperliquid traders
  - Polymarket markets, wallets and builders
  - DefiLlama fees and prices
