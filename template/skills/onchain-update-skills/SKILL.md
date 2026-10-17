---
name: onchain-update-skills
description: Use when the user asks to update, check or repair the Onchain Analyst skills or toolkit, or mentions a newer release; also use when a short starter skill should be upgraded to its full version.
---
# Update Onchain Analyst skills (starter)

- **Check only** (weekly routine "Check for skill updates"): steps 1–3 only. Up to date → stay silent. Otherwise say in one or two sentences what's new (CHANGELOG) and offer the update. Never change skills from a routine.
- **Update:** the user asks in chat or says yes. Steps 4–8 only after a yes in chat.
- Every run: if that routine is missing, create it per onchain-getting-started and tell the user.

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

Skill version: onchain-update-skills v0.1.1-short (Onchain Analyst)
