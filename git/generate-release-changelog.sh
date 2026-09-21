#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Generate a Markdown commit inventory from a release to current origin/dev.

Options:
  -r, --release VERSION  Release number, for example 7.2
  -w, --workspace DIR    Directory containing the Git repositories
  -o, --output FILE      Write Markdown to FILE instead of standard output
      --stdout           Write Markdown to standard output
  -h, --help             Show this help
EOF
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

github_repo() {
  local remote=${1%.git}
  case "$remote" in
    git@github.com:*) printf '%s\n' "${remote#git@github.com:}" ;;
    https://github.com/*) printf '%s\n' "${remote#https://github.com/}" ;;
    ssh://git@github.com/*) printf '%s\n' "${remote#ssh://git@github.com/}" ;;
    *) return 1 ;;
  esac
}

inspect_repo() {
  local dir=$1 slug remote_tags tag_sha tag_commit baseline commits count full_sha short_sha date subject title pr
  local -a tag_shas bases tag_bases unique_bases
  slug=$(github_repo "$(git -C "$dir" remote get-url origin)") || return 0
  [ -z "${seen[$slug]+x}" ] || return 0
  seen[$slug]=1
  remote_tags=$(git -C "$dir" ls-remote --tags --refs origin "*-$release")
  [ -n "$remote_tags" ] || return 0
  [ "$(gh repo view "$slug" --json isArchived --jq '.isArchived')" = false ] || return 0
  printf 'Inspecting %s\n' "$slug" >&2
  git -C "$dir" fetch --quiet origin '+refs/heads/dev:refs/remotes/origin/dev' || return 0
  mapfile -t tag_shas < <(printf '%s\n' "$remote_tags" | cut -f1 | sort -u)
  git -C "$dir" fetch --quiet --no-tags origin "${tag_shas[@]}"
  bases=()
  for tag_sha in "${tag_shas[@]}"; do
    tag_commit=$(git -C "$dir" rev-parse "$tag_sha^{commit}")
    mapfile -t tag_bases < <(git -C "$dir" merge-base --all "$tag_commit" origin/dev)
    [ "${#tag_bases[@]}" -eq 1 ] || die "$slug has multiple merge bases for a $release tag"
    bases+=("${tag_bases[0]}")
  done
  mapfile -t unique_bases < <(printf '%s\n' "${bases[@]}" | sort -u)
  [ "${#unique_bases[@]}" -eq 1 ] || die "$slug has different baselines for its $release tags"
  baseline=${unique_bases[0]}
  commits=$(git -C "$dir" rev-list "$baseline..origin/dev")
  [ -n "$commits" ] || return 0
  count=$(printf '%s\n' "$commits" | wc -l)
  printf '### %s\n' "${slug##*/}"
  printf -- '- **Branch:** `origin/dev` | **Release:** `%s` | **Baseline:** [`%s`](https://github.com/%s/commit/%s) | **Total Commits:** %s\n\n' \
    "$release" "${baseline:0:8}" "$slug" "$baseline" "$count"
  while read -r full_sha; do
    short_sha=${full_sha:0:8}
    IFS=$'\t' read -r date subject < <(git -C "$dir" show -s --format='%cs%x09%s' "$full_sha")
    if [[ $subject =~ ^(.*)[[:space:]]\(\#([0-9]+)\)$ ]]; then
      title=${BASH_REMATCH[1]}
      pr=${BASH_REMATCH[2]}
      printf -- '- [`%s`](https://github.com/%s/commit/%s) (%s) %s ([#%s](https://github.com/%s/pull/%s))\n' \
        "$short_sha" "$slug" "$full_sha" "$date" "$title" "$pr" "$slug" "$pr"
    else
      printf -- '- [`%s`](https://github.com/%s/commit/%s) (%s) %s\n' \
        "$short_sha" "$slug" "$full_sha" "$date" "$subject"
    fi
  done <<< "$commits"
  printf '\n'
  ((repo_count += 1))
}

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
workspace=$(cd -- "$script_dir/../.." && pwd)
release=
output=
output_set=false

while (($#)); do
  case "$1" in
    -r|--release) [ "$#" -ge 2 ] || die "$1 requires a value"; release=$2; shift 2 ;;
    -w|--workspace) [ "$#" -ge 2 ] || die "$1 requires a value"; workspace=$2; shift 2 ;;
    -o|--output) [ "$#" -ge 2 ] || die "$1 requires a value"; output=$2; output_set=true; shift 2 ;;
    --stdout) output=; output_set=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

if [ -z "$release" ]; then
  [ -t 0 ] || die 'release is required; use --release VERSION'
  read -r -p 'Release number: ' release
fi
[[ $release =~ ^[[:alnum:]][[:alnum:]._-]*$ ]] || die "invalid release: $release"
[ -d "$workspace" ] || die "workspace does not exist: $workspace"
workspace=$(cd -- "$workspace" && pwd)

if [ "$output_set" = false ] && [ -t 0 ] && [ -t 1 ]; then
  read -r -p 'Output [file/stdout] (file): ' output_mode
  case "${output_mode:-file}" in
    file)
      default_output="$workspace/AI-Output/changelogs/changelog-$release-to-dev.md"
      read -r -p "Output file [$default_output]: " output
      output=${output:-$default_output}
      ;;
    stdout) output= ;;
    *) die "invalid output choice: $output_mode" ;;
  esac
fi

command -v git >/dev/null || die 'git is required'
command -v gh >/dev/null || die 'gh is required'
gh auth status >/dev/null 2>&1 || die 'gh is not authenticated'

declare -A seen=()
repo_count=0
report=$(mktemp)
trap 'rm -f "$report"' EXIT
{
  printf '# Changelog since release %s\n\n' "$release"
  printf 'Compared with current `origin/dev`.\n\n'
  for dir in "$workspace"/*; do
    [ -d "$dir" ] || continue
    git -C "$dir" rev-parse --git-dir >/dev/null 2>&1 || continue
    inspect_repo "$dir"
  done
} > "$report"

[ "$repo_count" -gt 0 ] || die "no changes found after release $release in $workspace"
if [ -n "$output" ]; then
  mkdir -p -- "$(dirname -- "$output")"
  cp -- "$report" "$output"
  printf 'Wrote %s repositories to %s\n' "$repo_count" "$output" >&2
else
  cat "$report"
fi
