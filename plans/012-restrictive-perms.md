# Plan 012: Create the per-user Job tree with restrictive permissions

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If a STOP condition occurs, report it instead of improvising.
> Update this plan's status in `plans/README.md` when done.
>
> **Drift check (run first)**:
> `git diff --stat 8b4241e..HEAD -- dispatch/config.py dispatch/manifest.py dispatch/__init__.py install.sh tests`
> If these paths changed, compare the live code with this plan before editing.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: Plan 003 (`plans/003-reconcile-stale-and-pending-jobs.md`)
- **Category**: security
- **Planned at**: commit `8b4241e`, 2026-06-27

## Why this matters

`/ads_storage/<user>/.dispatch/jobs/` stores SQL text, recipient emails,
table names, output paths, and process metadata. The installer and runtime
currently create this tree with default permissions. With a typical `022`
umask on a shared Edge Node, other users can read that data.

The private `.dispatch`, `jobs`, and individual Job directories must be
owner-only (`0o700`). Do not restrict `/ads_storage/<user>` or the shared
`/ads_storage/dispatch` deployment tree.

## Current state

- `install.sh:24` runs `mkdir -p "$DISPATCH_HOME/jobs"` without `chmod`.
- `dispatch/manifest.py:190-191` creates a Job directory with
  `job_dir.mkdir(parents=True)`.
- `dispatch/__init__.py:18-19` creates the log parent with
  `mkdir(parents=True, exist_ok=True)`.
- `dispatch/config.py` derives runtime paths but has no creation helper.

`Path.mkdir(parents=True, mode=0o700)` is not sufficient: the requested mode
applies to the leaf, while newly created parents use normal umask-derived
permissions. Calling `mkdir` again also does not tighten an existing path.
The implementation must explicitly create and `chmod` each Dispatch-owned
directory.

## Commands

| Purpose | Command | Expected |
|---|---|---|
| Python syntax | `python -m compileall dispatch` | exit 0 |
| Shell syntax | `sh -n install.sh` | exit 0 |
| Focused tests | `python -m pytest tests/test_install_onboarding.py tests/test_pure_logic.py -q` | all pass |
| Full tests | `python -m pytest tests -q` | all pass |

## Scope

**In scope**:

- `dispatch/config.py`
- `dispatch/manifest.py`
- `dispatch/__init__.py`
- `install.sh`
- `tests/test_install_onboarding.py`
- `tests/test_pure_logic.py`, or one new focused config/manifest test file

**Out of scope**:

- Shared deployment-tree permissions.
- Permissions for the virtualenv or vendored wheels.
- Running a migration across other users' existing runtime directories.
- Changing Job state or cancellation behavior owned by Plan 003.

## Git workflow

- Branch: `advisor/012-restrictive-perms`
- Commit message: `security(config): restrict per-user Dispatch data`
- Do not push unless the operator requests it.

## Steps

### Step 1: Add one private-directory helper

Add this helper to `dispatch/config.py`:

```python
def ensure_private_dir(path: Path) -> Path:
    """Create a per-user Dispatch directory and enforce owner-only access."""
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path
```

The explicit `chmod` tightens existing directories. Let `OSError` propagate
from this helper; callers that intentionally tolerate logging failures already
catch it.

### Step 2: Protect every Job-directory level

In `manifest.create_job`, replace the recursive Job mkdir with:

```python
    home_dir = config.ensure_private_dir(config.dispatch_home(job_user))
    jobs_root = config.ensure_private_dir(home_dir / "jobs")
    job_dir = config.ensure_private_dir(jobs_root / job_id)
```

Do not chmod `config.data_root(job_user)`.

### Step 3: Protect the logging directory

In `dispatch.setup_logging`, construct the log path through the helper:

```python
        log_path = config.ensure_private_dir(config.dispatch_home()) / "dispatch.log"
```

Keep the existing `try/except OSError` behavior so logging setup remains
best-effort.

### Step 4: Tighten installer-created and existing directories

Replace the installer mkdir with:

```sh
mkdir -p "$DISPATCH_HOME/jobs"
chmod 700 "$DISPATCH_HOME" "$DISPATCH_HOME/jobs"
```

The `chmod` must follow `mkdir` so rerunning the idempotent installer also
tightens an older installation.

### Step 5: Add POSIX permission regression tests

On POSIX, the installer test must assert:

```python
assert stat.S_IMODE(dispatch_home.stat().st_mode) == 0o700
assert stat.S_IMODE((dispatch_home / "jobs").stat().st_mode) == 0o700
```

Add a focused test, skipped on Windows, that creates a Job with
`manifest.create_job` and asserts `.dispatch`, `jobs`, and the returned Job
directory are all `0o700`. Before calling `create_job`, set
`DISPATCH_DATA_ROOT` to the test's temporary user root through the existing
`mock_env` fixture.

Run:

```text
python -m pytest tests/test_install_onboarding.py tests/test_pure_logic.py -q
```

Expected: all focused tests pass on POSIX; permission assertions skip on
Windows.

## Done criteria

- [ ] `python -m compileall dispatch` exits 0.
- [ ] `sh -n install.sh` exits 0.
- [ ] `rg -n "ensure_private_dir" dispatch/config.py dispatch/manifest.py dispatch/__init__.py` finds all three integration points.
- [ ] `rg -n "chmod 700" install.sh` finds the installer hardening.
- [ ] Tests prove `0o700` on `.dispatch`, `jobs`, and a Job directory.
- [ ] `python -m pytest tests -q` passes.
- [ ] No files outside the stated scope changed.
- [ ] The Plan 012 row in `plans/README.md` is updated.

## STOP conditions

Stop and report if:

- The target Edge filesystem does not honor POSIX modes.
- The detached runner executes as a different OS user from the TUI.
- Tightening the directory blocks an established shared-support workflow.
- Plan 003 changes Job-directory creation and this plan has not been rebased.

## Maintenance notes

Existing installs become private when their owners rerun `install.sh`; this
plan does not authorize a cross-user migration. Reviewers must confirm the
implementation never chmods `/ads_storage/<user>` or the shared source tree.
