#!/usr/bin/env bash
set -euo pipefail

helpstr="Usage: $(basename "$0") ORG BRANCH [GH_PR_CREATE_OPTIONS...]"
org="${1:?$helpstr}"
branch="${2:?$helpstr}"
shift 2

repos=$(gh repo list "$org" --source --no-archived --limit 1000 \
  --json nameWithOwner --jq '.[].nameWithOwner')

for repo in $repos; do
  gh api "repos/$repo/branches/$branch" --silent >/dev/null 2>&1 || continue
  pr=$(gh pr list --repo "$repo" --head "$branch" --state open \
    --json url --jq '.[0].url // empty')
  [ -n "$pr" ] && echo "skip $repo: $pr" && continue
  gh pr create --repo "$repo" --head "$branch" "$@"
done
