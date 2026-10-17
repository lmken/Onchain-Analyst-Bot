# Methodology (Onchain Analyst v0.1.0, method 2026.10-1)

Everything is computed from public, keyless sources over **complete UTC days**.

## 1. Time rules
- A window `Nd` is the N complete UTC days ending yesterday (UTC). Explicit windows (`YYYY-MM-DD:YYYY-MM-DD`) are inclusive.
- The current UTC day is never included by default. If it is included, it's labelled `partial day`.
- Labels can be shown in the user's time zone; the maths never is.

## 2. Hyperliquid builder data
### 2.1 Sources
- **Feed:** `https://stats-data.hyperliquid.xyz/Mainnet/builder_fills/{addr_lowercase}/{YYYYMMDD}.csv.lz4`, one LZ4-frame CSV per builder per UTC day.
  - It contains the fills of orders routed with that builder code, maker and taker rows alike.
  - HTTP 403 means there's no file for that day.
  - Columns: `time, user, coin, side, px, sz, crossed, special_trade_type, tif, is_trigger, counterparty, closed_pnl, twap_id, builder_fee`. `time` is ISO-8601 to the second.
  - There's no fee-token column; feed fees are assumed USDC.
- **SQD Portal:** `POST https://portal.sqd.dev/datasets/hyperliquid-fills/stream` with `"fills":[{"builder":["<addr>"]}]`. It returns JSON lines (`header` + `fills`) with `time` in ms and `builderFee`, `feeToken`, `crossed`, `px`, `sz`, `user`, `coin`. The dataset starts at block 750,000,000, and blocks arrive at roughly 14 per second.
- **Lifetime check:** `POST https://api.hyperliquid.xyz/info {"type":"referral","user":"<addr>"}` → `builderRewards` (= claimed + unclaimed). It updates in batches.

### 2.2 Coverage and gap-fill
Observed in Oct 2026: many feed files stop around **12:00 UTC**. For one large builder, 15 of 16 days in early October had only hours 00–12. The toolkit and the snippet:
1. Compute `feed_hours` (distinct hours with rows) and `last_feed_time`.
2. Define the gaps:
   - **Tail gap:** from `last_feed_time` + 1 s to the end of the day, if the last row isn't in hour 23.
   - **Internal gaps:** empty whole hours before the last hour, only when the day has ≥500 rows. Quieter builders can legitimately have empty hours.
   - **Whole day:** if there's no file.
3. Fetch SQD fills for exactly those time ranges, keeping only fills whose `time` falls inside a gap, so nothing is double-counted against the feed. Any fill in the same second as the last feed row is not re-fetched; this boundary loss is negligible.
4. Label the day:

| Status | Meaning |
|---|---|
| `complete` | feed covers the day; no gaps |
| `gapfilled` | feed + SQD for the gaps |
| `missing_feed_sqd` | no feed file; whole day from SQD |
| `partial` | gaps remain (SQD unavailable or failed); totals are a lower bound |
| `missing` | no file and gap-fill disabled |

### 2.3 Builder metrics (per builder, window W)
Let F be the set of fill rows attributed to the builder in W.

| Metric | Definition |
|---|---|
| Revenue (USD) | Σ_F builder_fee for USDC-type tokens (USDC, USDT0, USDE, USDH); other tokens are reported separately |
| Routed volume | Σ_F abs(px × sz) |
| Taker volume | Σ_F abs(px × sz) where crossed = true |
| Fills | count(F) |
| Unique traders | count(distinct user in F), a set union across days |
| Take rate (bps) | revenue / routed volume × 10,000 |
| Revenue per trader | revenue / unique traders |
| Asset mix | volume share by class: perp; spot (`@n` or `BASE/QUOTE`); HIP-3 (`dex:COIN`); outcome (`#…`) |
| Concentration | traders sorted by volume; share from top 1%, 1–5%, 5–10%, 10–25%, 25–50%, bottom 50%; top-10 share; HHI = Σ s_i² |
| New vs returning (day d) | new = traders whose first fill with this builder (history from the registry `first_seen`) is on d |
| Weekly retention | cohort = ISO week of first fill; r[c][k] = share of cohort c active in week c+k |

Apps with several builder addresses are summed per day before any distinct counts.

## 3. Hyperliquid trader metrics
- Fills come from `userFillsByTime` (≤2,000 per call; only the last 10,000 fills are retrievable).
- **Volume** = Σ |px×sz|. **Taker share** = crossed volume / volume.
- **Net realized PnL** = Σ closedPnl − Σ fee − Σ builderFee. Maker rebates make `fee` negative.
- Positions and account value come from `clearinghouseState` at the fetch time.

## 4. Polymarket
- **Taker fee per fill** = C × rate × p × (1 − p): C = shares, p = price in [0,1], rounded to 5 dp (minimum 0.00001). Makers pay 0.
  - Category rates (Oct 2026): crypto 0.07; sports 0.05 (some leagues 0.03 in-season); politics, finance, tech, mentions 0.04; economics, culture, weather, other 0.05; geopolitics 0.
  - Prefer the market's own Gamma `feesEnabled` / `feeSchedule`.
- **Builder fees:** a builder may charge up to 100 bps on takers and 50 bps on makers.
  - **Revenue** = Σ `builderFee` from CLOB `/builder/trades`. **Notional** = Σ `sizeUsdc`. **Platform fees** = Σ `feeUsdc`.
  - The leaderboard `volume` is in **shares**, and `active_users` counts distinct makers.
- **Wallet PnL:** `/v2/positions` (realized, unrealized, total per position), `/v2/user-pnl` (series), `/v2/user-stats` (`all_time_pnl` snapshot object).

## 5. DefiLlama
- `dailyFees`, `dailyRevenue` and `dailyHoldersRevenue` follow DefiLlama's own `methodology` for each protocol, quoted verbatim.
- Window totals are sums of `totalDataChart` values on complete UTC days. The latest day can be restated for about 24h.

## 6. Reconciliation (how we check ourselves)
1. **Builder fills vs DefiLlama `<app>-perps`:** same UTC days, tolerance ±10%. DefiLlama's Hyperliquid builder adapter reads its own indexer (builder daily summaries, `hl-indexer.llama.rip`), so it's a largely independent check. A shortfall of about 40–50% usually means feed truncation wasn't filled.
2. **Builder fills vs `builderRewards`:** the lifetime sum of fills since `first_seen` must be ≤ the lifetime rewards and close to them. Rewards update in batches.
3. **Polymarket:** builder notional (USDC) vs leaderboard shares × average price, as a sanity check (±15%).
