#!/usr/bin/env bash
set -euo pipefail

message=$1
shift
base=$(git rev-parse HEAD)
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'

for attempt in 1 2 3; do
  git fetch origin main
  if ! git diff --quiet "$base" origin/main -- "$@"; then
    echo 'Generated files changed upstream; leaving them for the next scheduled run.' >&2
    exit 1
  fi
  git reset --mixed origin/main
  git add -- "$@"
  if git diff --cached --quiet; then exit 0; fi
  git commit -m "$message"
  if git push origin HEAD:main; then exit 0; fi
  git reset --mixed HEAD~1
done
echo 'Could not publish generated files after three attempts.' >&2
exit 1
