---
name: onchain-report
description: Use when the user wants an on-chain analysis delivered as a CSV, a chart, or a short Markdown memo rather than a chat answer.
---
# Reports

## CSV
- **Toolkit:** add `--format csv` to any `onchain` command and save the output, e.g. `onchain --format csv hl builders --window 30d > ~/.onchain/out/builders_30d.csv`.
- **Raw path:** write rows with Python `csv.DictWriter`. Include a header row, plus `window_start_utc`, `window_end_utc` and `source` columns.

## Chart (optional)
- If `matplotlib` is available (`python3 -c "import matplotlib"`), plot the daily series as lines or bars, with UTC dates on the x-axis and the source in the caption. Save a PNG under `~/.onchain/out/`.
- If it isn't, give a small Markdown table instead of installing anything without asking.

## Memo (Markdown, one page)
```
# <Title> — <window> (UTC)
**Bottom line:** 2–3 sentences with the key numbers.
## Key metrics
<table>
## What drives it
3–5 bullets (concentration, asset mix, trend vs prior window)
## Caveats
coverage status, unit notes, estimates
## Sources & method
each source + endpoint, fetch time (UTC), "complete UTC days", Onchain Analyst version
```
- Toolkit shortcut: `onchain --format md <command>` produces the tables to paste in.
- Save the memo to `~/.onchain/out/<slug>-<date>.md` and attach the file in chat.

## Delivering files
- Deliver every file (memo, CSV, chart) as a chat attachment. A file saved under `~/.onchain/out/` must be attached, not linked.
- Never put a `file://` URL or local path in a Markdown link: those links don't open for the user. Mention a path only as plain code text, if at all.

## Rules
- Every number in a report must come from a query in this session. Never estimate a figure silently.
- Don't post or send reports anywhere. Hand the file to the user.

Skill version: onchain-report v0.1.1 (Onchain Analyst)
