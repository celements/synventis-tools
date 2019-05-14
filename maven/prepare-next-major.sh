#!/bin/bash
die() { echo >&2 "failed - $@"; exit 1; }

echo $1 | grep -E -q '^[0-9]+$' \
            || die "1. argument invalid: major version number" 
VERSION=$1
[ ! -z $2 ] || die "2. argument invalid: branch name" 
BRANCH=$2
[ ! -z $3 ] || die "3. argument invalid: commit message"
MESSAGE=$3

if [ ! -z "$4" ]; then
  cd $4
fi
[ -f ./pom.xml ] || die "execute in maven project folder"

git checkout dev && \
git pull
[ $? ] || die "unable to pull from git repository, check connection"

echo
BRANCHLAST="dev-$(($VERSION-1)).x"
echo "Creating last release branch '${BRANCHLAST}' ..."
git branch ${BRANCHLAST} && \
git push origin ${BRANCHLAST} && \
echo "... done"

echo
echo "Preparing new branch '${BRANCH}' ..."
git branch ${BRANCH}
git checkout ${BRANCH} && \
echo "... done" || die "unable to prepare branch ${BRANCH}"

echo
echo "Updating pom.xml ..."
mvn versions:set -DnewVersion=${VERSION}.0-SNAPSHOT -DgenerateBackupPoms=false && \
mvn versions:use-latest-versions -Dincludes=com.celements:*,ch.programmonline:*,ch.newjobplacement:* \
    -DallowSnapshots=true -DprocessParent=true -DgenerateBackupPoms=false && \
echo "... done" || die "maven versions command failed"

echo
read -p "List other dependency update? [y/N] " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  mvn versions:display-dependency-updates -DprocessDependencyManagement=false
fi

echo
read -p "Update external dependencies (except xwiki)? [y/N] " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  mvn versions:use-latest-versions -Dexcludes=org.xwiki.platform:* -DgenerateBackupPoms=false && \
  echo "... done" || echo "... FAILED"
fi

while :
do
  echo
  echo "Executing maven clean install ..."
  MVNOUT=$(mvn validate clean install 2>&1)
  [ $? ] && break
  echo $MVNOUT | grep '^\[ERROR\]'
  read -p "... failure, please fix project! press enter to retry"
done
echo "... success"

echo
read -p "Please check pom.xml, press enter to commit and push"

echo
echo "Commiting and pushing pom.xml ..."
git add pom.xml && \
git commit -m "${MESSAGE}" && \
git push origin $BRANCH && \
echo "... done" || echo "... FAILED"
