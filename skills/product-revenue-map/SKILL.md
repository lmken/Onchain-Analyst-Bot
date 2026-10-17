---
name: product-revenue-map
description: Use when asked how much any on-chain app, wallet, frontend or protocol makes (revenue, fees, volume, users) across all its products and chains. Maps the business model to on-chain footprints, measures each line once, rolls up with dedupe rules and cross-checks aggregators.
---
# Product revenue map (any app)

Work product-first: understand what the app sells, then find where each sale lands on-chain. Never start from one data source.

## 1. Understand the product
Read the app's docs, fee page, site and announcements, plus the DefiLlama parent: `https://api.llama.fi/summary/fees/<slug>` (`childProtocols[].methodology`, `chains`). Write down what it sells, who pays, and when.

## 2. Enumerate every revenue stream
Check each type and record yes / no / unknown: builder-fees (HL, Polymarket), swap-fees (wallet or aggregator cut), spread, protocol-fees (LP/trading share), subscription or points, mev-priority, staking-yield, token-sales, referral, card-interchange, listing-fees, other. Mark lines that are **off-chain** (card, subscriptions, B2B deals). They stay in the table as "not visible".

## 3. Map each stream to its footprint
For each line, record chain, mechanism, identifiers and the best free source:

| Mechanism | Identifier | Free source |
|---|---|---|
| HL builder code | builder address | hyperliquid-builders |
| Polymarket builder | builder code | polymarket-builders |
| Swap fee to a wallet | fee wallet / token account | DefiLlama child per chain; verify on a public RPC |
| Router / program cut | contract or program ID | DefiLlama adapter; explorer |
| Protocol fees | protocol slug | protocol-fees |

Discover identifiers from the DefiLlama adapter source (`github.com/DefiLlama/dimension-adapters`, search the slug), docs, and explorers. You can also make or find one known trade and trace where the fee went. Mark each identifier verified only after you see it in data.

## 4. Measure each line once, then roll up
Split a DefiLlama parent by child **and** chain:
```bash
# smoke
curl -s "https://api.llama.fi/summary/fees/fomo?dataType=dailyFees" | python3 -c "
import sys,json,collections;d=json.load(sys.stdin);t=collections.Counter()
for ts,br in d['totalDataChartBreakdown'][-30:]:
  for ch,m in br.items():
    for c,v in m.items(): t[(c,ch)]+=v
print(sorted(t.items(),key=lambda x:-x[1])[:8])"
```
Verify a Solana fee account with public RPC. Count every signature (`getSignaturesForAddress`, limit 1000), then fetch an evenly spaced sample with `getTransaction` (`encoding: jsonParsed`, `maxSupportedTransactionVersion: 1`). Estimate inflow as mean post−pre token balance × count. The toolkit's `docs/snippets/solana_token_inflow.py` does this.

Dedupe rules:
- **R1** Lines partition activity. Each fill or swap belongs to exactly one line (split by asset class or chain).
- **R2** Count volume on the taker side only.
- **R3** Count fees per fee charged.
- **R4** Never add the parent total on top of its children.
- **R5** Give each line one primary source: on-chain if free, otherwise the aggregator child. The other source is only a cross-check.
- **R6** Union users only inside one address namespace (HL and EVM 0x share one; Solana is separate). Never add users across namespaces.

Toolkit: `onchain app <name> --window 30d` runs the registry's `product_lines` and prints per-line rows, the total and the cross-checks.

## 5. Cross-check and explain the gaps
Compare each line with the matching DefiLlama child, and the total with the parent (also Token Terminal free pages and public dashboards). Explain every gap over 5%:
- scope (e.g. HIP-3 inside or outside "perps")
- missing hours
- fees vs revenue
- attribution (cross-chain fees booked on one chain)

## Save the map
Add the app to `registry.local.yaml` (see app-registry): a `product` block (what, who_pays, sources, mapped date) and a `product_lines[]` list with `id`, `stream`, `chain`, `identifiers`, `measure.source` (`hl-builder` + `asset_class` | `pm-builder` | `defillama` + `parent`/`child`/`chains`/`exclude_chains` | `none`) and `crosscheck`.

## Output
One row per line: stream, chain, fees, revenue, taker volume, users, source, coverage. Then:
- the total
- the % of revenue measured on-chain
- a list of what isn't visible
- a cross-check table

If you also write a report or CSV, deliver it as a chat attachment (see onchain-report). Never link a `file://` URL or local path: those links don't open for the user.

## Pitfalls
- An aggregator's "app" figure may cover only one product. Ask what is missing before trusting it.
- Cross-chain fees are often booked on one chain. Don't re-add them per chain.
- Fresh days get restated. Use complete UTC days at least a day old.

Skill version: product-revenue-map v0.1.1 (Onchain Analyst)
