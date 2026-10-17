# Security

- **No secrets in this repo.** Nothing here needs an API key. Every MVP source is keyless and public.
- **Keys, later.** Optional paid or free-key sources are read only from environment variables (for example `ONCHAIN_<PROVIDER>_KEY`). A bot must ask for a key with its platform's masked secret request. It must never ask anyone to paste a key into chat, and never write a key to a file.
- **Read-only by design.** No skill or command trades, signs, approves, posts or sends anything.
- **Integrity.** Skills are installed from a pinned release tag. Each skill file is checked against the sha256 in `skills/manifest.json` before it is saved.
- **Reporting.** Open a GitHub issue for non-sensitive problems. For anything sensitive, contact the maintainer through the profile linked on the repository, and don't include exploit details in public issues.
