#!/bin/bash
printf "%-30s %s\n" "DIRECTORY" "BRANCH"
printf "%-30s %s\n" "---------" "------"
for d in */ ; do
    [ -d "$d/.git" ] && printf "%-30s %s\n" "$d" "$(git -C "$d" branch --show-current)"
done

