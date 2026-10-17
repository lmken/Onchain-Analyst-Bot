---
name: onchain-update-skills
description: Use when the user asks to update, check or repair the Onchain Analyst skills or toolkit, or mentions a newer release; also use when a short starter skill should be upgraded to its full version.
---
# Update Onchain Analyst skills (starter)

Run only when the user asks.

1. **Read** the memory `onchain-skills-manifest` (`repo`, `tag`, `REPO_RAW`, skill ids and versions). If it's missing, use the values in onchain-getting-started.
2. **Find the newest tag:** `curl -s https://api.github.com/repos/{REPO}/releases/latest`. If there's no release, use `/tags`.
3. **Fetch** `{REPO_RAW}/<tag>/skills/manifest.json` and `CHANGELOG.md`.
4. **Classify** each skill:
   - **upgrade-short:** the version line ends `-short`
   - **changed:** newer version
   - **new**
   - **removed**
   - **unchanged**
5. **Diff** changed skills against the old tag with `diff -u` and summarise them with the CHANGELOG lines.
   - Check each new file's sha256 against the manifest. Skip mismatches.
   - If the user edited a skill, offer: overwrite / keep mine / save mine as a copy.
6. **Ask once:** all / pick / none. Remind the user that skills are shared by all their bots.
7. **Apply:**
   - upgrade or changed → UpdateSkill `write` with the existing id and the same name
   - new → `write` without an id
   - removed → ask separately before `delete`, because deletion is global
8. **Record:** update the memory record (tag, versions, ids, sha256, date).

Skill version: onchain-update-skills v0.1.0-short (Onchain Analyst)
