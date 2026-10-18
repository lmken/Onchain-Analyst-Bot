---
name: onchain-getting-started
description: Use on the first conversation after this bot is added, or when Onchain Analyst skills are missing, outdated or short starter versions.
---
# Getting started with Onchain Analyst

Release source:
- `REPO = lmken/Onchain-Analyst-Bot`
- `TAG = v0.1.2`
- `REPO_RAW = https://raw.githubusercontent.com/lmken/Onchain-Analyst-Bot`

## 1. Greet (one line)
"I answer on-chain questions (Hyperliquid builder codes, Polymarket, protocol fees) from free public data, with sources and coverage on every number. I never trade, sign, post or send."

## 2. Take stock
1. List this bot's skills.
2. Onchain skills end with a line `Skill version: <slug> v<version>[-short] (Onchain Analyst)`. Note each one's slug, version and id.
3. Fetch the release manifest byte-exact:
   ```bash
   curl -sf {REPO_RAW}/{TAG}/skills/manifest.json
   ```
   If `curl` can't reach GitHub, try WebFetch for the manifest only.

## 3. Plan
- **Up to date:** every manifest skill is present at the manifest version. Record the ids and skip to step 6.
- **Otherwise:**
  - **upgrade:** installed skills marked `-short` or older
  - **add:** manifest skills not present
- **Clash:** a skill with the same name but no Onchain version line belongs to the user. Never overwrite it. Offer to skip it, or to save ours as `<name>-onchain`.

## 4. Ask once
Ask: "Upgrade N starter skills and add M skills from release {TAG}? Skills are saved to your library and every one of your bots can see them."
- Choices: yes / pick / not now.
- On "not now", the starter skills keep working. The user can say "update skills" later.

## 5. Apply only what was approved
For each skill:
1. Fetch it: `curl -sf {REPO_RAW}/{TAG}/skills/<slug>/SKILL.md`.
2. Check `sha256sum` and the byte count against the manifest. On a mismatch, skip the skill and tell the user.
3. Split the frontmatter (`name`, `description`) from the body.
4. Save it:
   - **upgrade:** UpdateSkill `write` with the existing id, the same name, the description and the body
   - **add:** UpdateSkill `write` without an id

Record every returned id.

## 6. Record
Write the memory `onchain-skills-manifest` with:
- `repo`, `tag`, `REPO_RAW`, `template_mode` (from the manifest)
- per skill: `{slug, name, id, version, source, installed_sha256}`
- the date

Other skills read `{REPO}`, `{TAG}` and `{REPO_RAW}` from this record.

## 7. Keep the weekly update check
Do this on first run and whenever onchain-update-skills runs. List this bot's routines. If none is named "Check for skill updates", create it with UpdateRoutine, then tell the user in one line that it checks weekly and never installs anything without asking:
- name: `Check for skill updates`; schedule `0 9 * * 1` (Mondays ~9am, user's time zone); flexible timing
- prompt: "Read-only update check for Onchain Analyst skills. Read the memory onchain-skills-manifest for the installed tag (repo: lmken/Onchain-Analyst-Bot if the memory is missing). Get the latest release from https://api.github.com/repos/lmken/Onchain-Analyst-Bot/releases/latest. If it isn't newer and no skill is a -short starter, stay silent. Otherwise fetch https://raw.githubusercontent.com/lmken/Onchain-Analyst-Bot/<tag>/CHANGELOG.md, tell the user in one or two sentences what's new, and offer to run onchain-update-skills. Never install, overwrite or delete skills from this routine."

## 8. Optional toolkit
Ask: "Install the optional speed-up toolkit (Python, about 1–2 minutes)?"
- If yes, run onchain-setup-toolkit.
- Record the result either way: `toolkit: installed / declined / unavailable`.

## 9. Set up, one question at a time
1. Which apps or markets should I watch? Suggest a few from the registry: wallets, trading apps, Polymarket builders.
2. Preferred output: chat tables, CSV or memo?
3. Default window: suggest the last 30 complete UTC days.

Save the answers to memory.

## 10. Demo
- Without the toolkit: show the top Hyperliquid builders by lifetime `builderRewards` (registry addresses), plus this week's Polymarket builders.
- With the toolkit: also run `onchain hl builders --window 7d --top 10`.
- Show the sources and coverage footer.

## If something fails
Say what failed in one line and continue with the skills that are present. "update skills" retries at any time.

Skill version: onchain-getting-started v0.1.2 (Onchain Analyst)
