#!/usr/bin/env bash
set -euo pipefail

service="${1:-web}"
cmd=(docker compose exec -T "$service")
dump="heap-$(date +%Y%m%d-%H%M%S).hprof"
tmpfile="/tmp/$dump"

cleanup() {
  "${cmd[@]}" rm -f "$tmpfile"
}
trap cleanup EXIT

echo "heap dump may pause the JVM and require up to the heap size in free disk space"
"${cmd[@]}" jcmd 1 VM.flags
"${cmd[@]}" jcmd 1 GC.heap_info
"${cmd[@]}" jcmd 1 GC.heap_dump "$tmpfile"
"${cmd[@]}" cat "$tmpfile" > "$dump"
echo "heap dump written to $dump"
