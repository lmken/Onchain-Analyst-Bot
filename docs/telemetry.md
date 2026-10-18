# Update-check count (anonymous)

There is no server of ours and no telemetry code. The only signal is GitHub's own download counter on release assets.

## What's counted
- Every release has `skills/manifest.json` attached as an asset named `manifest.json`.
- Each bot's weekly routine "Check for skill updates", and every "update skills" run, fetch the manifest from
  `https://github.com/lmken/Onchain-Analyst-Bot/releases/latest/download/manifest.json` (redirects to the latest release's asset; `curl -sfL`).
- GitHub increments that asset's `download_count` by one per download. Nothing else is recorded or available to us:
  no identity, account, IP address or bot id. The count is of checks, not people.
- If the asset is missing, bots fall back to the `releases/latest` API and the raw tag manifest, which are not counted.

## How to read it
```bash
gh release view --repo lmken/Onchain-Analyst-Bot   # latest release --json assets --jq '.assets[]|{name,downloadCount}'
gh api repos/lmken/Onchain-Analyst-Bot/releases --jq '.[] | {tag: .tag_name, assets: [.assets[]|{name,download_count}]}'
```
The releases page on GitHub shows the same numbers.

## Interpreting it
- A copy checks about once a week, so `download_count / weeks since the release became latest` ≈ active copies. Manual
  "update skills" runs and anyone downloading the file by hand add some noise.
- Only the release that is currently latest gets new counts; older releases keep their totals.
- The repository's Insights → Traffic page adds clones and unique visitors for the last 14 days.
