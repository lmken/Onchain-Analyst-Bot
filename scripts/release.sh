#!/usr/bin/env bash
# Cut a release: checks, annotated tag, GitHub release with CHANGELOG notes and skills/manifest.json attached.
# Usage: scripts/release.sh v0.1.3      (run on a clean, pushed main; requires gh)
# The manifest asset is required: bots download releases/latest/download/manifest.json (see docs/telemetry.md).
set -euo pipefail
TAG="${1:?usage: scripts/release.sh vX.Y.Z}"
REPO="lmken/Onchain-Analyst-Bot"
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
grep -q "^RELEASE = \"$TAG\"" scripts/build_manifest.py || { echo "RELEASE in build_manifest.py is not $TAG"; exit 1; }
grep -q "\"release\": \"$TAG\"" skills/manifest.json || { echo "skills/manifest.json is not $TAG"; exit 1; }
"$PY" scripts/lint_skills.py
"$PY" scripts/build_manifest.py --check
"$PY" -m pytest -q
test -z "$(git status --porcelain)" || { echo "working tree not clean"; exit 1; }
NOTES="$(mktemp)"
awk -v h="## $TAG " 'index($0,h)==1{f=1;next} /^## /{f=0} f' CHANGELOG.md > "$NOTES"
test -s "$NOTES" || { echo "no CHANGELOG entry for $TAG"; exit 1; }
git tag -a "$TAG" -m "$TAG"
git push origin main "$TAG"
gh release create "$TAG" --repo "$REPO" --title "$TAG" --notes-file "$NOTES" --verify-tag "skills/manifest.json#manifest.json"
curl -sfL "https://github.com/$REPO/releases/latest/download/manifest.json" | cmp - skills/manifest.json && echo "asset ok"
