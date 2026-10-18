---
name: onchain-update-skills
description: Use when the user asks to update, check or repair the Onchain Analyst skills or toolkit, turn automatic updates on or off, or mentions a newer release; also use when a short starter skill should be upgraded to its full version.
---
# Update Onchain Analyst skills

Update mode (`update_mode` in the memory `onchain-skills-manifest`; missing means `ask`):
- **ask:** notify and offer; skills change only after a yes in chat.
- **auto:** verified changed, new and `-short` upgrades install without asking, then a short note says what changed.
- The user can switch anytime ("update automatically" / "ask before updating"). Save the new value and confirm in one line.

Run types:
- **Routine** ("Check for skill updates"): steps 1–3. Up to date → stay silent. `ask` → tell the user in one or two sentences what's new (that tag's CHANGELOG), offer this skill, change nothing. `auto` → continue with steps 4–8 in auto mode. Routines change skills only in `auto` mode.
- **Chat** (the user asks, or says yes to the offer): every step; steps 4–8 change skills only after the user says yes.

Every run, first make sure the routine "Check for skill updates" exists with the prompt in onchain-getting-started ("Keep the weekly update check"). Create it if missing, or update its prompt if it differs, and tell the user.

## 1. Read the install record
- Read `onchain-skills-manifest` for `repo`, `tag`, `template_mode`, `update_mode`, and per skill `{slug, id, version, installed_sha256}`.
- If the record is missing, rebuild it: find library skills whose last line starts `Skill version: <slug> v` and ends `(Onchain Analyst)`.

## 2. Find the newest release
Get the latest manifest from the release asset (each download is counted anonymously; nothing identifies you):
```bash
curl -sfL https://github.com/{REPO}/releases/latest/download/manifest.json -o new_manifest.json \
  && python3 -c "import json;print(json.load(open('new_manifest.json'))['release'])"
```
If that fails, get the tag from `curl -s https://api.github.com/repos/{REPO}/releases/latest` (`tag_name`; no release → `https://api.github.com/repos/{REPO}/tags`) and the manifest from `{REPO_RAW}/<new_tag>/skills/manifest.json`. Unauthenticated GitHub API calls are limited to 60/hour; downloads are not.

## 3. Compare
- **Up to date:** the tag isn't newer **and** no skill is `-short` or missing. Say so and stop (routine: stay silent).
- **Routine in `ask` mode, not up to date:** fetch `{REPO_RAW}/<new_tag>/CHANGELOG.md`, notify, offer the update and stop.
- **Otherwise:** fetch `{REPO_RAW}/<new_tag>/CHANGELOG.md` and continue.

## 4. Classify each skill
- **upgrade-short:** the installed version ends `-short`.
- **changed:** the manifest `version` is newer than the installed one.
- **new:** in the manifest, not installed.
- **removed:** installed, not in the manifest.
- **unchanged:** none of the above.

## 5. Verify and diff
For each upgrade-short, changed and new skill:
1. Fetch the new file with `curl -sf {REPO_RAW}/<new_tag>/skills/<slug>/SKILL.md` (getting-started: `template/getting-started/SKILL.md`).
2. Check its sha256 and byte count against the manifest. On a mismatch, skip it and report it.
3. For changed skills, `diff -u` against `{REPO_RAW}/<old_tag>/...`; report sections touched, lines added/removed and that tag's CHANGELOG lines.

**Local edits:** if the library copy's sha256 ≠ `installed_sha256`, the user edited it. Offer: overwrite / keep mine / save mine as a copy. If you can't read it, warn before overwriting. In `auto` mode, skip edited or unreadable skills and ask about them in the note; never overwrite them silently.

## 6. Ask once (chat and `ask` mode)
Show a table (skill, change, size, summary) and ask: update all / pick / none. Remind the user that skills are shared by all of their bots. In `auto` mode skip this step for verified upgrade-short, changed and new skills that the user hasn't edited.

## 7. Apply
- **upgrade-short and changed:** UpdateSkill `write` with the **recorded id**, the same `name`, the manifest `description` and the file body (everything after the frontmatter).
- **new:** UpdateSkill `write` without an id. Record the id it returns.
- **removed:** always ask **separately** before UpdateSkill `delete`, even in `auto` mode. Deleting removes the skill for every bot.

## 8. Record and report
- Update `onchain-skills-manifest` (tag, versions, ids, sha256, source: repo, `update_mode`, date).
- `auto` mode: send a short note: "Updated Onchain Analyst to <tag>: <skills, one line each from the CHANGELOG>. Say 'ask before updating' to approve updates yourself." Add any skipped, edited or removed skills that need an answer.
- If the memory says `toolkit: installed`, offer `~/.onchain/venv/bin/pip install --upgrade "git+https://github.com/{REPO}@<new_tag>"`.

Skill version: onchain-update-skills v0.1.2 (Onchain Analyst)
