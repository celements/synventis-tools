#!/bin/bash
## Marc Sladek <marc@sadek.me>, June-Nov 2018
## pulls and cleans the branches of the current or given and sub git repositories in parallel

main() {
  mainDir=$1
  if [ -z "$mainDir" ]; then 
    mainDir=$(pwd);
  fi
  if [ ! -d "$mainDir" ]; then
    echo "Invalid directory: '$mainDir'"
    exit 1
  else
    declare -A pids
    runAsync $mainDir
    for subDir in $mainDir/*; do
      runAsync $subDir
    done
    for name in "${!pids[@]}"; do
      wait ${pids[$name]} \
        && echo "done    [$name]" \
        || echo "FAILED  [$name]"
    done
    exit 0
  fi
}

## runs the script async for a given git repository '$1'
runAsync() {
  if [ "$1" ] && [ -d "$1/.git" ]; then
    cleanBranches $1 dev &
    pids[$(basename $1)]=$!
  fi
}

## does the following process for for a git repository '$1':
## 1. checkout branch '$2'
## 2. pull the remote repository
## 3. pruning remote branches from 'origin'
## 4. deleting local branches gone from remote
cleanBranches() {
  [ "$1" ] && [ -d "$1/.git" ] && [ "$2" ] \
    && git -C $1 checkout $2 > /dev/null 2>&1 \
    && git -C $1 pull        > /dev/null 2>&1 \
    && git -C $1 fetch origin --prune \
    && git -C $1 branch -vv | egrep '\[origin/.*: gone\]' \
       | awk '{print $1}' | egrep -v "(^\*|dev*|master*)" \
       | xargs --no-run-if-empty git -C $1 branch --delete --force
  return $?
}

## main call
main $@
