#!/usr/bin/env bash

set -Eeuo pipefail

mvn_startup=(prepare-package)
mvn_watch=(prepare-package)
for arg in "$@"; do
  case "$arg" in
    --mvn-startup=*) read -r -a mvn_startup <<< "${arg#*=}" ;;
    --mvn-watch=*) read -r -a mvn_watch <<< "${arg#*=}" ;;
    *) echo "Usage: $0 [--mvn-startup=\"goals/options\"] [--mvn-watch=\"goals/options\"]" >&2; exit 1 ;;
  esac
done

prefix_output() {
  sed -u "s/^/[$1] /"
}

pids=()
cleanup() {
  trap - EXIT INT TERM
  if ((${#pids[@]})); then
    kill -- "${pids[@]/#/-}" 2>/dev/null || true
    wait "${pids[@]}" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo
echo "==> Preparing backend sources for startup ..."
mvncmd=(mvn -ntp -Dstyle.color=always)
"${mvncmd[@]}" clean "${mvn_startup[@]}" war:exploded
echo "... done"

set -m # Give each background job its own process group, including its children.

echo
echo "==> Starting the local Docker services ..."
docker compose -f compose.local.yml up --menu=false </dev/null &
pids+=("$!")

if [[ -f package.json ]]; then
  echo
  echo "==> Watching frontend sources ..."
  FORCE_COLOR=1 npm run dev > >(prefix_output vite) 2>&1 &
  pids+=("$!")
fi

echo
echo "==> Watching backend sources ..."
FORCE_COLOR=1 watchexec \
  --color always \
  --postpone \
  --watch pom.xml \
  --watch src/main/webapp \
  --ignore 'src/main/webapp/resources/dist/**' \
  --debounce 2s \
  --on-busy-update queue \
  -- "${mvncmd[@]}" "${mvn_watch[@]}" war:exploded \
  > >(prefix_output maven) 2>&1 &
pids+=("$!")

set +m
wait -n "${pids[@]}"
