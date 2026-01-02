# Maven toolbox scripts

This folder contains a small set of scripts to automate dependency updates across multiple Maven projects in a workspace.

## Prerequisites

- Debian/Linux with `bash`
- `python3` (for `build-dependency-tree.py`)
- `git`
- `mvn` (and the Maven Versions Plugin available, since `versions:*` goals are used)
- Workspace layout: a directory containing multiple Maven projects with `pom.xml` files

All scripts are intended to be run from this folder (they `cd` to the script directory).

---

## `build-dependency-tree`

Scans a workspace for `pom.xml` files, extracts internal project coordinates, and prints a build order (top-down) as a list of project directories.

It only includes projects that inherit from `com.celements:base-pom` (directly or transitively).

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

---

## `prepare-release`

Prepares and pushes a git branch for a maven project directory for either:

- `--mode=release`: update dependencies to latest releases (default mode)
- `--mode=major`: bump the project version to `X.0-SNAPSHOT` and update dependencies to latest snapshots

It expects a clean `pom.xml`.

### Usage

```bash
<toolbox>/mvn/prepare-release.sh [--mode=release] --branch=<branch-name> [project-dir]
<toolbox>/mvn/prepare-release.sh --mode=major --version=<major> --branch=<branch-name> [project-dir]
```

### Examples

Update the current directory project to the latest releases:

```bash
<toolbox>/mvn/prepare-release.sh --branch=RELEASE
```

Prepare major version 7.0-SNAPSHOT for a single project:

```bash
<toolbox>/mvn/prepare-release.sh --mode=major --version=7 --branch=major-7 ~/workspace/some-project
```

---

## `major-upgrade`

Runs a major upgrade across *multiple* Maven projects in a workspace, in dependency order.

It uses `build-dependency-tree` to generate an ordered list of project directories, then runs `prepare-release --mode=major` for each directory. Progress is checkpointed so the run can be resumed.

### Usage

```bash
<toolbox>/mvn/major-upgrade.sh <major> [workspace_dir]
```

- `<major>`: required major version number (e.g. `7`)
- `workspace_dir`: optional, defaults to `$HOME/workspace`

### Files created

For major version `$v` in workspace `$WS`:

- `$WS/major-$v.tree` — dependency-ordered list of projects (generated once, reused on reruns)
- `$WS/major-$v.done.tree` — checkpoint file of already-processed directories
- `$WS/major-$v.log` — combined stdout/stderr log of all `prepare-release` runs

### Example flow

1. Go to your workspace directory and make sure all repos are cloned. Ensure all repos are
on a clean git state (on `dev` branch).
    ```bash
    cd $WS
    <toolbox>/git/pull-and-clean.sh
    ```
2. Generate a dependency `major-$v.tree` and vet it manually. Entries can be removed if needed.
    ```bash
    <toolbox>/mvn/build-dependency-tree.py > major-$v.tree
    edit major-$v.tree
    ```
3. Run the routine to process all pom's in order. If one fails, fix the repo and rerun the same command to resume. Already completed directories are skipped based on `major-$v.done.tree`.
    ```bash
    <toolbox>/mvn/major-upgrade.sh $v
    ```
