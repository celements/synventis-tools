#!/usr/bin/env bash

set -Eeuo pipefail

cmd_db=mariadb
if [[ ${1:-} == upgrade ]]; then
  cmd_db=mariadb-upgrade
  shift
fi

cmd_docker=(docker compose exec)
if [[ ! -t 0 ]]; then
  cmd_docker+=(-T)
fi

# shellcheck disable=SC2016
exec "${cmd_docker[@]}" db sh -c \
  'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec "$@"' sh \
  "$cmd_db" --no-defaults --protocol=socket --user=root "$@"
