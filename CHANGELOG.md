# Changelog

## v0.1.4 (2026-10-17)
Everything new since v0.1.2 (v0.1.3 shipped the first two items).

**Automatic updates, your choice.** During setup your bot asks once: install new Onchain Analyst releases automatically, or ask you first? The default is **ask first**. In ask mode, the weekly check tells you what's new and waits for your yes. In auto mode, it installs updates after checking every file's fingerprint (sha256 and size), then sends you a short note on what changed. Either way, a skill you edited yourself is never overwritten, and no skill is ever deleted, without asking you. Switch anytime by saying "update automatically" or "ask before updating".

**Anonymous update-check count.** The weekly check now downloads the release's `manifest.json` file from GitHub, and GitHub counts those downloads. That gives a rough count of active copies. Nothing identifies you: no account, address or bot id is sent or stored, and there is no server of ours. Details in `docs/telemetry.md`.

**Starter questions.** At the end of setup, the bot suggests five good first questions, e.g. how much an app makes across all its products, comparing two frontends, looking up a wallet, this week's top Polymarket builders, or a protocol's fee trend.

**Suggest registry additions.** Found a new app, Hyperliquid builder address, Polymarket builder code or DefiLlama slug? The bot verifies what it can and gives you a prefilled GitHub issue link. You open it and submit it yourself; the bot never files anything. There's also a "Registry addition" issue form.

**Optional weekly digest.** Setup offers a Monday digest of the apps you follow: revenue, volume, users and week-over-week change, with sources. It's off unless you say yes. Change the list with "add/remove <app> from my digest", or turn it off by asking the bot to stop the digest.

**Example report.** The README now links a real example: FOMO's 30-day rollup across all products (Sep 17–Oct 16, 2026), in `docs/examples/fomo-30d.md`.

**Data-trust footer, enforced.** Every skill that produces numbers must end its answers with sources, the time window and a coverage label. A new lint check fails the build if any skill drops it, and several skills were tightened to match.

**How to update:** say "update skills" to your bot, or wait for Monday's check (auto mode installs it for you).

## v0.1.3 (2026-10-17)
**Automatic updates, your choice.** Setup asks once whether to install new releases automatically or ask you first (default: ask first). Auto mode installs only fingerprint-verified files and sends a short note; skills you edited are never overwritten, and none deleted, without asking. Switch anytime: "update automatically" / "ask before updating".

**Anonymous update-check count.** The weekly check downloads the release's `manifest.json` from GitHub, which counts downloads anonymously (no identity, no server of ours). See `docs/telemetry.md`.

**How to update:** say "update skills" to your bot, or wait for Monday's check.

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
