#!/usr/bin/env bash
set -Eeuo pipefail

readonly INSTALL_PREFIX="$HOME/.local"
readonly PASEO_CLI="$INSTALL_PREFIX/bin/paseo"
readonly LOCAL_HOME="${PASEO_HOME:-$HOME/.paseo}"

require_command() {
  local -r command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Error: required command not found: %s\n' "$command_name" >&2
    return 1
  fi
}

require_command npm
require_command node
require_command python3

if npm install --global --prefix "$INSTALL_PREFIX" --allow-scripts="esbuild,node-pty,msgpackr-extract" @getpaseo/cli@latest; then
  :
else
  exit_code=$?
  printf 'Error: Paseo CLI installation failed.\n' >&2
  exit "$exit_code"
fi

if [[ ! -x "$PASEO_CLI" ]]; then
  printf 'Error: installed Paseo CLI is not executable: %s\n' "$PASEO_CLI" >&2
  exit 1
fi

export PATH="$INSTALL_PREFIX/bin:$PATH"

if status_json=$("$PASEO_CLI" daemon status --json --home "$LOCAL_HOME"); then
  :
else
  exit_code=$?
  printf 'Error: unable to determine Paseo daemon status.\n' >&2
  exit "$exit_code"
fi

if status_fields=$(python3 -c '
import json
import sys
try:
    status = json.load(sys.stdin)
except (json.JSONDecodeError, UnicodeDecodeError):
    sys.exit(2)
if (not isinstance(status, dict)
        or not isinstance(status.get("localDaemon"), str)
        or not isinstance(status.get("connectedDaemon"), str)):
    sys.exit(3)
print(status["localDaemon"])
print(status["connectedDaemon"])
' <<<"$status_json"); then
  :
else
  exit_code=$?
  if [[ "$exit_code" -eq 2 ]]; then
    printf 'Error: Paseo daemon status returned malformed JSON.\n' >&2
  else
    printf 'Error: Paseo daemon status is missing required fields.\n' >&2
  fi
  exit "$exit_code"
fi

mapfile -t daemon_status <<<"$status_fields"
readonly local_daemon="${daemon_status[0]}"
readonly connected_daemon="${daemon_status[1]}"

case "$local_daemon:$connected_daemon" in
  stopped:not_probed)
    action=start
    ;;
  running:reachable)
    action=restart
    ;;
  *)
    printf 'Error: refusing lifecycle action for local daemon state %q and connection state %q.\n' "$local_daemon" "$connected_daemon" >&2
    exit 1
    ;;
esac

if "$PASEO_CLI" daemon "$action" --home "$LOCAL_HOME"; then
  :
else
  exit_code=$?
  printf 'Error: Paseo daemon %s failed.\n' "$action" >&2
  exit "$exit_code"
fi
