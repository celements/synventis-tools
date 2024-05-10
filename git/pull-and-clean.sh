#!/bin/bash
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
## 2. pull the remote repository
## 3. pruning remote branches from 'origin'
## 4. deleting local branches gone from remote
cleanBranches() {
  IFS='|'
  for b in $baseBranches; do
    [ "$1" ] && [ -d "$1/.git" ] && [ "$b" ] \
      && git -C "$1" switch "$b" > /dev/null 2>&1 \
      && git -C "$1" pull        > /dev/null 2>&1 \
      && git -C "$1" fetch origin --prune \
      && git -C "$1" branch -vv | grep -E '\[origin/.*: gone\]' \
        | awk '{print $1}' | grep -Ev "(^\*|${baseBranches})" \
        | xargs --no-run-if-empty git -C "$1" branch --delete --force \
      && return 0
  done
  return $?
}

## main call
main "$@"
