#!/usr/bin/env bash
set -euo pipefail
umask 077

service="${1:-web}"
cmd=(docker compose exec -T "$service")
profile="profile-$(date +%Y%m%d-%H%M%S)"
tmpfile="/tmp/${profile}.jfr"

cleanup() {
  "${cmd[@]}" jcmd 1 JFR.stop name="$profile" >/dev/null 2>&1 || true
  "${cmd[@]}" rm -f "$tmpfile" || true
}
trap cleanup EXIT

"${cmd[@]}" jcmd 1 JFR.start name="$profile" settings=profile filename="$tmpfile" maxsize=512m

read -r -n 1 -s -p "recording; press any key to stop" && echo

"${cmd[@]}" jcmd 1 JFR.stop name="$profile"

"${cmd[@]}" cat "$tmpfile" > "${profile}.jfr"
echo "recording written to ${profile}.jfr"
