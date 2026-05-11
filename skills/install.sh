#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

function install_skills {
  local agent="$1"
  local target="$2"
  mkdir -p "$target"
  for skill_dir in "$script_dir/$agent"/*; do
    [ -d "$skill_dir" ] || continue
    [ -f "$skill_dir/SKILL.md" ] || continue
    skill_name="$(basename "$skill_dir")"
    ln -sfn "$skill_dir" "$target/$skill_name"
    echo "Installed $agent/$skill_name"
  done
}

install_skills "codex" "${CODEX_HOME:-$HOME/.codex}/skills"
