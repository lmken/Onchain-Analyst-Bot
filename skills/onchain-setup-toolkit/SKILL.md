---
name: onchain-setup-toolkit
description: Use when the optional onchain toolkit is missing, outdated or failing, or the user wants faster, cached analysis; skills still work without it.
---
# Set up the optional `onchain` toolkit

The toolkit is a shortcut. If any step fails, record `toolkit: unavailable (<reason>)` in memory and keep answering with the raw paths in each skill.

## Steps
1. Check Python: `python3 --version`. It needs 3.11 or newer.
2. Create a private venv:
   ```bash
   python3 -m venv ~/.onchain/venv
   ```
3. Install the pinned release recorded in the memory `onchain-skills-manifest` (`{REPO}`, `{TAG}`):
   ```bash
   ~/.onchain/venv/bin/pip install "git+https://github.com/{REPO}@{TAG}"
   ```
   - Only two dependencies are pinned: `lz4` and `pyyaml`.
   - If pip can't reach PyPI, stop here and use the raw paths.
4. Initialise and check:
   ```bash
   ~/.onchain/venv/bin/onchain setup
   ~/.onchain/venv/bin/onchain doctor --live
   ```
   - Every line should be `ok`.
   - A `fail` on one source means that source is down or rate-limited right now. Its skills fall back to the raw path or say the data is unavailable.
5. Record the result in memory: `toolkit: installed <TAG> at ~/.onchain/venv/bin/onchain`.
6. Tell the user it's ready, in one line. Mention that the cache lives in `~/.onchain/` and that deleting it is safe.

## Notes
- The toolkit reads only public keyless endpoints. It never needs or stores keys.
- To upgrade, use onchain-update-skills, which offers the matching toolkit tag.
- To uninstall: `rm -rf ~/.onchain/venv` (the cache in `~/.onchain/` can go too).

Skill version: onchain-setup-toolkit v0.1.0 (Onchain Analyst)
