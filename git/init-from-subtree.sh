#!/bin/bash
## init a new repository from a sub directory
# $1 = sub directory
# $2 = github org
# $3 = github repository
# $4 = branch name (default master)

set -euo pipefail

SUBDIR=$1
ORG=$2
REPO=$3
BRANCH=${4:-master}
TMP_BRANCH="${REPO}-${BRANCH}"

echo "creating subtree from ${SUBDIR} ..."
git gc
git subtree split -P $SUBDIR -b $TMP_BRANCH

echo
echo "building new repository ${REPO} ..."
echo $REPO >> .gitignore
mkdir $REPO
cd $REPO
git init -b $BRANCH
git pull .. $TMP_BRANCH

echo
echo "setting remote and push ..."
git remote add origin git@github.com:${ORG}/${REPO}.git
git push -u origin $BRANCH
