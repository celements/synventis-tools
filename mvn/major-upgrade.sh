#!/bin/bash
set -euo pipefail

v=${1:?"1. argument invalid: major version number"}
WS="${2:-"$HOME/workspace"}"
[ -d "$WS" ] || { echo "workspace '$WS' not found"; exit 1; }
TREE="$WS/major-$v.tree"
TREE_DONE="$WS/major-$v.done.tree"
LOG="$WS/major-$v.log"

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$SCRIPT_DIR"

if [ ! -r "$TREE" ]; then
  ./build-dependency-tree.py "$WS" > "$TREE"
fi
touch "$TREE_DONE"

while IFS= read -r dir; do
  [ -n "$dir" ] || continue
  grep -Fxq -- "$dir" "$TREE_DONE" && continue
  ./prepare-release.sh --mode=major --version="$v" --branch="major-$v" "$dir" \
    2>&1 | tee -a "$LOG"
  echo "$dir" >> "$TREE_DONE"
done < "$TREE"
