#!/bin/bash
set -euo pipefail # strict mode

die() { echo >&2 "failed - $@"; exit 1; }

MODE="release" # release | major
DIR=""
for arg in "$@"; do
  case "$arg" in
    --mode=*) MODE="${arg#*=}" ;;
    --version=*) VERSION="${arg#*=}" ;;
    --branch=*) BRANCH="${arg#*=}" ;;
    *) [ -z "$DIR" ] || die "only one path argument allowed"; DIR="$arg" ;;
  esac
done

if [ "${MODE}" = "major" ]; then
  echo "${VERSION-}" | grep -E -q '^[0-9]+$' || die "--version invalid: major version number" 
  VERSION="${VERSION}.0-SNAPSHOT"
elif [ "${MODE}" != "release" ]; then
  die "--mode invalid: release | major"
fi
[ -n "${BRANCH-}" ] || die "--branch invalid: branch name"
[ -n "${DIR-}" ] && cd -- "$DIR"
DIR="${DIR:-$(basename "$(pwd)")}"

echo "------------------------------------------------------------------------"
echo " prepare-${MODE} ${DIR} ${VERSION-}"
echo "------------------------------------------------------------------------"

[ -f ./pom.xml ] || die "execute in maven project folder"
git diff --quiet ./pom.xml || die "uncommitted changes in pom.xml, please commit or stash first"

BASE="dev"
INCLUDES="com.celements:*,com.synventis:*,ch.programmonline:*,ch.newjobplacement:*,prog.online:*,online.prog:*"

git switch -q "${BASE}"
git pull -q origin "${BASE}"

echo "Preparing branch '${BRANCH}' ..."
if ! git switch -c "${BRANCH}" "${BASE}" 2>/dev/null; then
  git switch -q "${BRANCH}"
  git pull -q origin "${BRANCH}" 2>/dev/null || true
  git merge -q "${BASE}"
fi

echo "Updating pom.xml ..."
MVN="mvn -q -Dmaven.transfer.listener=warn"
if [ "${MODE}" = "release" ]; then
  # doesn't work for milestones with naming schema 'x.y-M1'
  $MVN versions:use-releases -U -Dincludes="${INCLUDES}" \
      -DprocessParent=true -DfailIfNotReplaced=true -DgenerateBackupPoms=false
  $MVN versions:use-latest-releases -U -Dincludes="${INCLUDES}" \
      -DprocessParent=true -DgenerateBackupPoms=false
  COMMIT_MSG="[prepare-release] update dependencies to latest releases"
elif [ "${MODE}" = "major" ]; then
  $MVN versions:set -DnewVersion="${VERSION}" -DgenerateBackupPoms=false
  $MVN versions:use-latest-versions -U -Dincludes="${INCLUDES}" \
      -DallowSnapshots=true -DprocessParent=true -DgenerateBackupPoms=false
  COMMIT_MSG="[prepare-major] update to major version ${VERSION}"
fi

echo "Executing maven clean install ..."
$MVN validate clean install -Dmaven.test.skip=true

echo "Pushing branch..."
git add pom.xml
if ! git diff --cached --quiet; then
  git commit -m "${COMMIT_MSG}"
fi
git push -q --set-upstream origin "${BRANCH}"

echo "------------------------------------------------------------------------"
echo " prepare-${MODE} ${DIR} DONE"
echo "------------------------------------------------------------------------"
echo
