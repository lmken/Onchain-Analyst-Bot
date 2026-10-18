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

## Weekly digest (opt-in, off by default)
Only when the user says yes (onchain-getting-started offers it):
1. Save `digest_apps: [<app ids>]` in the memory `onchain-preferences`.
2. Create the routine `Weekly onchain digest` with UpdateRoutine: schedule `0 10 * * 1` (Mondays ~10am, user's time zone), flexible timing, prompt: "Weekly onchain digest. Read digest_apps from the memory onchain-preferences; if it is empty or missing, stay silent. For each app, measure the last 7 complete UTC days and the 7 before with product-revenue-map (or the app's skill): revenue, volume, users and week-over-week change. Send one short table plus 2-3 lines of notes, ending with the footer: sources, window, coverage. Read-only: never trade, post or send anything else."
3. Change the list: the user says "add/remove <app> from my digest"; update `digest_apps`. Turn it off: delete the routine and clear `digest_apps`.

## Rules
- End every report with the footer (onchain-methodology): sources, window (UTC), coverage.
- Every number in a report must come from a query in this session. Never estimate a figure silently.
- Don't post or send reports anywhere. Hand the file to the user.

Skill version: onchain-report v0.1.2 (Onchain Analyst)
