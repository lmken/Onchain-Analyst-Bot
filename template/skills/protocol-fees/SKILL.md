---
name: protocol-fees
description: Use for a protocol's or app's fees, revenue or holders revenue over time, fee rankings across protocols, or current token prices.
---
# Protocol fees and prices (starter)

1. **Fees:** `https://api.llama.fi/summary/fees/<slug>?dataType=dailyFees` (or `dailyRevenue` / `dailyHoldersRevenue`).
   - The response has `total24h/7d/30d`, `totalDataChart` [[ts, usd]] and `methodology`.
   - Sum `totalDataChart` over complete UTC days for any window.
2. **Parent vs child slugs:** e.g. `fomo` vs `fomo-perps`. Use the child to compare with HL builder data.
3. **Rankings:** `https://api.llama.fi/overview/fees?excludeTotalDataChart=true` → `protocols[]`.
4. **Prices:** `https://coins.llama.fi/prices/current/coingecko:<id>`.
5. **Pitfalls:**
   - The latest day may be restated for about 24h.
   - Don't mix fees and revenue.
   - Paid (`402`) endpoints are off-limits.
   - Cite "Source: DefiLlama".

Skill version: protocol-fees v0.1.0-short (Onchain Analyst)
