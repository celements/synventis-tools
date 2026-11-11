# synventis-tools

Shared Synventis developer tooling for Git, Maven, Eclipse, and agent skills.

## Eclipse Config

Shared Eclipse formatter, cleanup, and import-order settings live in [`eclipse/`](eclipse/).

## Git Tools

Git helper scripts live in [`git/`](git/), including PR creation, subtree initialization, SSH URL
conversion, and local cleanup helpers.

## Maven Tools

Maven helper scripts live in [`mvn/`](mvn/). See [`mvn/README.md`](mvn/README.md) for dependency
inspection and formatting workflows.

## Local Webapp

Run these commands from the webapp project root.

### webapp-up

Builds the exploded WAR, starts containers and watches sources:

```bash
../synventis-tools/webapp/up.sh
../synventis-tools/webapp/up.sh --mvn-startup="-U install" --mvn-watch="prepare-package"
```

### webapp-mysql

Opens a root DB session using the container password; `upgrade` runs `mariadb-upgrade`:

```bash
../synventis-tools/webapp/mysql.sh
../synventis-tools/webapp/mysql.sh -e "SHOW DATABASES"
../synventis-tools/webapp/mysql.sh upgrade
```

## Agent Skills

Agent skills live in [`skills/`](skills/). See [`skills/README.md`](skills/README.md) for install
and update workflows.
