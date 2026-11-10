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

Run [`webapp/up.sh`](webapp/up.sh) from the webapp project root to build the exploded WAR,
start `compose.local.yml`, and watch frontend and backend sources:

```bash
../synventis-tools/webapp/up.sh
../synventis-tools/webapp/up.sh --mvn-startup="-U install" --mvn-watch="prepare-package"
```

Requires Maven, Docker Compose, and watchexec. Frontend watching uses `npm run dev` when a
`package.json` exists.

## Agent Skills

Agent skills live in [`skills/`](skills/). See [`skills/README.md`](skills/README.md) for install
and update workflows.
