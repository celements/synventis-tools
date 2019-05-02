#!/bin/bash
BRANCH=RELEASE

if [ ! -z "$1" ]; then
  cd $1
fi
[ -f ./pom.xml ] || { echo "execute in maven project folder" && exit 1; }
git checkout dev && git pull
[ $? ] || { echo "pull failed" && exit 1; }

echo
echo "Preparing release branch '${BRANCH}' ..."
git branch ${BRANCH}
git checkout ${BRANCH}
[ $? ] || { echo "failed branch preparation ${BRANCH}" && exit 1; }
echo "... done"

echo
echo "Updating pom.xml ..."
mvn versions:use-latest-releases -Dincludes=com.celements:*,ch.programmonline:* -DprocessParent=true -DgenerateBackupPoms=false
echo "... done"

while :
do
  echo
  echo "Executing maven clean install ..."
  mvn validate clean install &>/dev/null && break
  read -p "... failure, please fix project! press enter to retry"
done
echo "... success"

echo
read -p "Please check pom.xml, press enter to commit and push"

echo
echo "Commiting and pushing pom.xml ..."
git add pom.xml
git commit -m "update dependencies" && git push origin $BRANCH
echo "... done"
