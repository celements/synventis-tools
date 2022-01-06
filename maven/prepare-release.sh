#!/bin/bash
die() { echo >&2 "failed - $@"; exit 1; }

[ -n "$1" ] || die "1. argument invalid: branch name" 
BRANCH=$1

if [ -n "$2" ]; then
  cd $2
fi
[ -f ./pom.xml ] || die "execute in maven project folder"

git checkout dev && git pull
[ $? ] || die "unable to pull from git repository, check connection"

echo
echo "Preparing release branch '${BRANCH}' ..."
git branch ${BRANCH}
git checkout ${BRANCH} && \
(! git branch --remotes | egrep --quiet "(^|\s)origin/${BRANCH}(\s|$)" || \
   git pull origin ${BRANCH}) && \
git merge dev && \
echo "... done" || die "unable to prepare branch ${BRANCH}"

echo
echo "Updating pom.xml change SNAPSHOT to releases, if available ..."
# doesn't work for milestones with naming schema 'x.y-M1'
mvn versions:use-releases -U \
    -Dincludes=com.celements:*,com.synventis:*,ch.programmonline:*,ch.newjobplacement:*,prog.online:* \
    -DprocessParent=true -DfailIfNotReplaced=true -DgenerateBackupPoms=false && \
echo "... done" || die "maven versions command failed"

echo
echo "Updating pom.xml using latest releases ..."
mvn versions:use-latest-releases -U \
    -Dincludes=com.celements:*,com.synventis:*,ch.programmonline:*,ch.newjobplacement:*,prog.online:* \
    -DprocessParent=true -DgenerateBackupPoms=false && \
echo "... done" || die "maven versions command failed"

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
git diff pom.xml
echo
read -p "Please check pom.xml, press enter to commit and push"

echo
echo "Commiting and pushing pom.xml ..."
git add pom.xml && \
git commit -m "[prepare-release] update dependencies to latest releases" && \
git push --set-upstream origin ${BRANCH} && \
echo "... done" || echo "... FAILED"
