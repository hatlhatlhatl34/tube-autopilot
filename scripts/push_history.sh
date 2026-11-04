#!/usr/bin/env bash
# Commit updated topic-history files back to the repo (called by daily workflow).
# [skip ci] in the message prevents re-triggering Actions in a loop.
set -u
CH="${1:-unknown}"

git config user.name  "autopilot[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

git add data/history 2>/dev/null || true
if git diff --cached --quiet; then
  echo "no history changes for ${CH}"
  exit 0
fi
git commit -m "history: ${CH} daily update [skip ci]" >/dev/null

BRANCH="${GITHUB_REF_NAME:-main}"
for i in 1 2 3; do
  if git pull --rebase origin "$BRANCH" && git push; then
    echo "history pushed (${CH})"
    exit 0
  fi
  sleep $((i * 7))
done
echo "WARN: could not push history (non-fatal)"
exit 0
