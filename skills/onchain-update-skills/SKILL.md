---
name: onchain-update-skills
description: Use when the user asks to update, check or repair the Onchain Analyst skills or toolkit, or mentions a newer release; also use when a short starter skill should be upgraded to its full version.
---
# Update Onchain Analyst skills

Two modes:
- **Check only** (from the weekly routine "Check for skill updates"): do steps 1–3 only. If up to date, stay silent. Otherwise tell the user in one or two sentences what's new (from that tag's CHANGELOG) and offer to run this skill. Never install, overwrite or delete anything from a routine.
- **Update** (the user asks in chat, or says yes to the offer): do every step. Steps 4–8 change skills only after the user says yes in chat.

Every run, first make sure the routine "Check for skill updates" exists. If it's missing, create it as described in onchain-getting-started ("Keep the weekly update check") and tell the user.

## 1. Read the install record
- Read the memory `onchain-skills-manifest` for `repo`, `tag`, `template_mode`, and per skill `{slug, id, version, installed_sha256}`.
- If the record is missing, rebuild it: find library skills whose last line starts `Skill version: <slug> v` and ends `(Onchain Analyst)`.

## 2. Find the newest release
```bash
curl -s https://api.github.com/repos/{REPO}/releases/latest | python3 -c "import sys,json;print(json.load(sys.stdin).get('tag_name'))"
```
If there's no release, use `https://api.github.com/repos/{REPO}/tags`. Unauthenticated GitHub API calls are limited to 60/hour; raw file downloads are not.

## 3. Compare
- **Up to date:** the tag isn't newer **and** no skill is `-short` or missing. Say so and stop (check-only mode: stay silent).
- **Check-only mode, not up to date:** fetch `{REPO_RAW}/<new_tag>/CHANGELOG.md`, notify the user, offer the update and stop here.
- **Otherwise:** fetch `{REPO_RAW}/<new_tag>/skills/manifest.json` and `{REPO_RAW}/<new_tag>/CHANGELOG.md`.

## 4. Classify each skill
- **upgrade-short:** the installed version ends `-short`.
- **changed:** the manifest `version` is newer than the installed one.
- **new:** in the manifest, not installed.
- **removed:** installed, not in the manifest.
- **unchanged:** none of the above.

## 5. Summarise the diff
For each changed skill:
1. Fetch the old body (`{REPO_RAW}/<old_tag>/skills/<slug>/SKILL.md`) and the new one with `curl -sf`.
2. Check the new file's sha256 and byte count against the manifest. On a mismatch, skip it and report it.
3. Run `diff -u old new`. Report the sections touched and lines added/removed, plus that tag's CHANGELOG lines.

**Local edits:** if you can read the library copy and its sha256 ≠ `installed_sha256`, the user edited it. Offer: overwrite / keep mine / save mine as a copy. If you can't read it, warn before overwriting.

## 6. Ask once
Show a table (skill, change, size, summary) and ask: update all / pick / none. Remind the user that skills are shared by all of their bots.

## 7. Apply only what was approved
- **upgrade-short and changed:** UpdateSkill `write` with the **recorded id**, the same `name`, the manifest `description` and the file body (everything after the frontmatter).
- **new:** UpdateSkill `write` without an id. Record the id it returns.
- **removed:** ask **separately** before UpdateSkill `delete`. Deleting removes the skill for every bot.

## 8. Record
- Update the memory `onchain-skills-manifest` (tag, versions, ids, sha256, source: repo, date).
- If the memory says `toolkit: installed`, offer `~/.onchain/venv/bin/pip install --upgrade "git+https://github.com/{REPO}@<new_tag>"`.

Skill version: onchain-update-skills v0.1.1 (Onchain Analyst)
