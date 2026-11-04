#!/usr/bin/env bash
set -euo pipefail

if (( $# != 1 )); then
  echo "Usage: $(basename "$0") <name>" >&2
  exit 2
fi

cd "$HOME/.codex"

auth_file="auth.$1.json"
if [[ ! -f "$auth_file" ]]; then
  echo "Error: auth json not found: $auth_file" >&2
  exit 1
fi

ln -sfnT -- "$auth_file" auth.json
echo "installed $auth_file"

command -v codex >/dev/null 2>&1 \
 && echo "restarting codex app-server..." \
 && codex app-server daemon restart

command -v paseo >/dev/null 2>&1 \
 && echo "restarting paseo daemon..." \
 && paseo daemon restart

echo "...done"
