---
name: app-compare
description: Use for side-by-side comparisons of apps or frontends ("A vs B vs C") or a one-page app snapshot across Hyperliquid builder data, Polymarket builder data and DefiLlama fees.
---
# Compare apps

## Steps
1. Resolve each app through app-registry: HL builder addresses, PM builder codes and DefiLlama slugs.
2. Fix **one** window for all apps: complete UTC days, 30d by default.
3. For each app and each source it has, run the matching skill:
   - **HL:** hyperliquid-builders. Toolkit: `onchain compare <app1> <app2> … --window 30d`. That covers the HL comparison, with gap-fill.
   - **PM:** polymarket-builders (volume in shares, builder fees in USDC).
   - **Fees:** protocol-fees on the app's `defillama.slug`, and on the `perps` child when comparing with HL.
4. Build one comps table:
   - app
   - HL revenue, HL volume, HL traders, revenue per trader, take rate (bps)
   - PM builder volume (shares), PM builder fees
   - DefiLlama 30d fees/revenue
   - coverage

   Put "n/a" where an app has no presence on a source.
5. Add the previous equal window (Δ%) when trends matter.
6. Interpret in 3 lines at most: who leads, what drives it (concentration, asset mix), and caveats.

## Pitfalls
- Never compare windows of different lengths, or partial days against complete ones.
- Multi-address apps: sum their addresses and say so.
- "Share" means share among the compared apps, not of the whole venue.
- Apply the onchain-methodology traps (shares vs USD, fees vs revenue).

## Output
Show the comps table, then the interpretation, then the footer with every source, the window and coverage per app.

Skill version: app-compare v0.1.0 (Onchain Analyst)
