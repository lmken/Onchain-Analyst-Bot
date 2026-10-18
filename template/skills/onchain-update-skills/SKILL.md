---
name: onchain-update-skills
description: Use when the user asks to update, check or repair the Onchain Analyst skills or toolkit, turn automatic updates on or off, or mentions a newer release; also use when a short starter skill should be upgraded to its full version.
---
# Update Onchain Analyst skills (starter)

- **Update mode:** `update_mode` in the memory `onchain-skills-manifest` (missing = `ask`). `ask`: notify and offer. `auto`: install verified updates, then send a short note. The user can switch anytime ("update automatically" / "ask before updating"); save it and confirm.
- **Routine** ("Check for skill updates"): steps 1–3. Up to date → stay silent. `ask` → say in one or two sentences what's new (CHANGELOG), offer the update, change nothing. `auto` → continue in auto mode. Routines change skills only in `auto` mode.
- **Chat:** the user asks or says yes; steps 4–8.
- Every run: make sure that routine exists with the prompt in onchain-getting-started (create it or update its prompt) and tell the user.

1. **Read** `onchain-skills-manifest` (`repo`, `tag`, `REPO_RAW`, `update_mode`, skill ids, versions, sha256). If it's missing, use the values in onchain-getting-started.
2. **Newest release:** `curl -sfL https://github.com/{REPO}/releases/latest/download/manifest.json` (its `release` is the tag). If that fails: `https://api.github.com/repos/{REPO}/releases/latest` and `{REPO_RAW}/<tag>/skills/manifest.json`.
3. **Fetch** `{REPO_RAW}/<tag>/CHANGELOG.md`.
4. **Classify:** upgrade-short (`-short`), changed (newer version), new, removed, unchanged.
5. **Verify:** check each new file's sha256 and bytes against the manifest; skip mismatches. Diff changed skills against the old tag with `diff -u`. If the user edited a skill (sha256 ≠ `installed_sha256`), offer: overwrite / keep mine / save mine as a copy. `auto` never overwrites an edited skill without asking.
6. **Ask once** (chat or `ask`): all / pick / none. Skills are shared by all their bots. `auto` skips this for verified, unedited skills.
7. **Apply:**
   - upgrade or changed → UpdateSkill `write` with the existing id and the same name
   - new → `write` without an id
   - removed → always ask separately before `delete` (deletion is global), even in `auto`
8. **Record** the memory (tag, versions, ids, sha256, `update_mode`, date). `auto`: note what was updated and that "ask before updating" switches modes.

Skill version: onchain-update-skills v0.1.2-short (Onchain Analyst)
