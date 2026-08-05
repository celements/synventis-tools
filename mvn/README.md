# Maven toolbox scripts

This folder contains helpers for inspecting Maven project dependencies and formatting Java code.

## Prerequisites

- Debian/Linux with `bash`
- `python3` (for `build-dependency-tree.py`)
- `mvn`
- Workspace layout: a directory containing multiple Maven projects with `pom.xml` files

All scripts are intended to be run from this folder (they `cd` to the script directory).

---

## Maven settings

Setup the maven settings files in `~/.m2` with the following commands:

```bash
install -m 600 <workspace>/synventis-tools/mvn/settings.xml ~/.m2/
# will prompt for your tokens (see below)
read -rsp 'forge token: ' token && sed -i "s|{forge-token}|$token|g" ~/.m2/settings.xml
read -rsp 'legacy token: ' token && sed -i "s|{legacy-token}|$token|g" ~/.m2/settings.xml
```

- `forge-token`: create your personal access token with at least `package=Read` permission here:
  https://forge.celhosting.ch/user/settings/applications.
- `legacy-token`: the legacy maven repository password (like before)

---

## `build-dependency-tree`

Scans a workspace for `pom.xml` files, extracts internal project coordinates, and prints a build order (top-down) as a list of project directories.

It only includes projects that inherit from `com.celements:celements-parent`.

### Usage

```bash
<toolbox>/mvn/build-dependency-tree.py [workspace_dir] [--verbose]
```

### Output

- Writes progress info to stderr (e.g. “Scanning…”)
- Writes the resulting ordered directory list to stdout, one path per line (relative to the workspace)

### Example

Create a tree file for a workspace:

```bash
<toolbox>/mvn/build-dependency-tree.py ~/workspace > dependency.tree
```
