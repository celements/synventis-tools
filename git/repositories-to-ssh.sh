#!/bin/bash
## Marc Sladek <marc@sadek.me>, June 2018
## sets the ssh url for all repositories

mainDir=$1
if [ -z "$mainDir" ]; then 
  mainDir=$(pwd);
fi
for dir in $mainDir/*; do
  if [ -d "$dir/.git" ]; then
    cd $dir
    repo=`git config --get remote.origin.url | awk -F/ '{ print $4"/"$5}'`
    if [ "$repo" = "/" ]; then 
      echo "skipping '$dir'"
    else
      url=git@github.com:$repo
      echo $url
      git remote set-url origin $url
    fi
  fi
done
exit 0
