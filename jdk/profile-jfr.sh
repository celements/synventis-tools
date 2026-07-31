#!/usr/bin/env bash
set -euo pipefail

service="${1:-web}"
cmd=(docker compose exec -T "$service")
profile="profile-$(date +%Y%m%d-%H%M%S)"
tmpfile="/tmp/${profile}.jfr"
recording=false

stop_rec() { [ "$recording" = true ] && "${cmd[@]}" jcmd 1 JFR.stop name="$profile"; }
trap stop_rec EXIT

"${cmd[@]}" jcmd 1 JFR.start name="$profile" settings=profile filename="$tmpfile" maxsize=512m
recording=true

read -r -n 1 -s -p "recording; press any key to stop" && echo

stop_rec
recording=false

"${cmd[@]}" cat "$tmpfile" > "${profile}.jfr"
echo "recording written to ${profile}.jfr"
"${cmd[@]}" rm -f "$tmpfile"
