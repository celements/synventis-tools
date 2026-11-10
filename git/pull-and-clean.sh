#!/usr/bin/env bash
## Marc Sladek <marc@sadek.me>, June-Nov 2018
## pulls and cleans the branches of the current or given and sub git repositories in parallel

baseBranches='dev|develop|master|main'

main() {
  mainDir=$1
  if [ -z "$mainDir" ]; then 
    mainDir=$(pwd);
  fi
  if [ ! -d "$mainDir" ]; then
    echo "Invalid directory: '$mainDir'"
    exit 1
  else
    githubKeyfile="$(ssh -G github | grep '^identityfile' | head -1 | awk '{print $2}')"
    githubKeyfile=${githubKeyfile/#\~/$HOME}
    [ -f "$githubKeyfile" ] \
      && ! ssh-add -l | grep -q "$(ssh-keygen -lf "$githubKeyfile" | awk '{print $2}')" \
      && ssh-add "$githubKeyfile"
    declare -A pids
    directories=("$mainDir" "$mainDir"/*)
    for dir in "${directories[@]}"; do
      runAsync "$dir"
    done
    for dir in "${directories[@]}"; do
      joinAsync "$dir"
    done
    exit 0
  fi
}

## runs the script async for a given git repository '$1'
runAsync() {
  if [ "$1" ] && [ -d "$1/.git" ]; then
    cleanBranches "$1" &
    pids[$(basename "$1")]=$!
  fi
}

## joins the async process for a given git repository '$1'
joinAsync() {
  name=$(basename "$1")
  pid=${pids[$name]}
  [ -z "$pid" ] && return
  wait "$pid" \
    && echo "done    [$name]" \
    || echo "FAILED  [$name]"
}

## does the following process for for a git repository '$1':
## 1. tries switching to any base branch
## 2. pulls the current base branch
## 3. prunes remote branches from 'origin'
## 4. deletes local branches whose upstream is gone
cleanBranches() {
  [ "$1" ] && [ -d "$1/.git" ] || return 1
  local -a git=(git -C "$1")
  local IFS='|'
  local branch
  for branch in $baseBranches
      do "${git[@]}" switch "$branch" > /dev/null 2>&1 \
      && "${git[@]}" pull > /dev/null 2>&1 \
      && "${git[@]}" fetch origin --prune \
      && "${git[@]}" for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads \
        | awk '$2 == "[gone]" { print $1 }' \
        | xargs --no-run-if-empty "${git[@]}" branch --delete --force \
      && return 0
  done
  return $?
}

## main call
main "$@"
