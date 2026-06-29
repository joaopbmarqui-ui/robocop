# Plan 016: Harden explicit CSV paths in manifests

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report; do not improvise. When done, update the status row for this plan in
> `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat b33c803..HEAD -- dispatch/manifest.py dispatch/sql.py tests`
> Compare excerpts if in-scope files changed.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: plans/001-harden-launch-identifiers-and-csv-paths.md
- **Category**: security
- **Planned at**: commit `b33c803`, 2026-06-29
- **Source**: `codex/implement-plans` branch audit finding #3 (introduced)

## Why this matters

Plan 001 added `sql.safe_csv_path()` for TUI-built CSV destinations, and
`manifest._csv_path_for_destination()` re-checks containment for hand-edited
manifests. Containment alone still allows odd filename stems (spaces,
metacharacters) when `destination["csv_path"]` is set explicitly. The detached
runner builds `impala-shell -o` from that path; tighten the manifest boundary to
match the TUI rules.

## Current state

- `dispatch/sql.py:30-42` — `safe_csv_path(launch_cwd, table)` validates a
  plain identifier stem and confines output under `launch_cwd`.
- `dispatch/manifest.py:251-268` — explicit path branch only checks
  `is_relative_to(resolved_cwd)`:
  ```python
  explicit_csv_path = destination.get("csv_path")
  if not explicit_csv_path:
      return str(sql.safe_csv_path(launch_cwd, table or "dispatch_export"))
  resolved_cwd = launch_cwd.resolve()
  raw_path = Path(explicit_csv_path)
  output_path = (raw_path if raw_path.is_absolute() else resolved_cwd / raw_path).resolve()
  if not output_path.is_relative_to(resolved_cwd):
      raise ValueError("CSV output path must stay within the launch directory")
  return str(output_path)
  ```
- `dispatch/screens/new_job.py` — TUI path uses `safe_csv_path()` for normal
  launches.
- Product invariant (`AGENTS.md`): CSV outputs are written uncompressed to the
  launch-time working directory.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Manifest tests | `source mocks/dev-env.sh && python -m pytest tests/test_pure_logic.py -k "csv or orchestrator" -q` | exit 0 |
| Full gate | `source mocks/dev-env.sh && python -m pytest tests -q` | exit 0 |
| Compile | `python -m compileall dispatch scr` | exit 0 |

## Scope

**In scope**:
- `dispatch/sql.py`
- `dispatch/manifest.py`
- `tests/test_pure_logic.py` (manifest / CSV path tests)

**Out of scope**:
- `scr/download_to_csv.py` — already validates `--table-name`; `--output-file`
  comes from Dispatch manifest argv built here.
- Changing the on-disk manifest JSON schema.
- Allowing CSV paths outside `launch_cwd`.

## Git workflow

- Branch: `advisor/016-explicit-csv-paths`
- Commit message: `fix(manifest): validate explicit csv_path filename stems`
- Do NOT push unless asked.

## Steps

### Step 1: Add `resolve_csv_output_path()` in `dispatch/sql.py`

Add a function used by both the TUI and manifest layers:

```python
def resolve_csv_output_path(launch_cwd: Path, raw_path: str | Path) -> Path:
    """Resolve a CSV output path under launch_cwd with safe filename rules."""
```

Requirements:

1. Resolve `launch_cwd` and combine relative/absolute `raw_path` the same way
   `_csv_path_for_destination` does today.
2. Reject paths that escape `launch_cwd` after `.resolve()`.
3. Require suffix `.csv` (case-insensitive).
4. Validate `output_path.stem` with the same rules as `safe_csv_path()`:
   no `/`, `\`, `..`, empty stem; `validate_identifier(stem, "CSV filename")`
   must pass.
5. Return the resolved `Path`.

Refactor `safe_csv_path()` to call `resolve_csv_output_path(launch_cwd,
f"{table}.csv")` so there is one validation implementation.

**Verify**: `python -m compileall dispatch` → exit 0.

### Step 2: Use `resolve_csv_output_path()` in manifest

In `dispatch/manifest.py`, replace the explicit-path branch of
`_csv_path_for_destination()` with:

```python
return str(sql.resolve_csv_output_path(launch_cwd, explicit_csv_path))
```

Keep the `safe_csv_path` fallback when `csv_path` is absent.

**Verify**: `python -m compileall dispatch` → exit 0.

### Step 3: Add regression tests

In `tests/test_pure_logic.py` (beside existing manifest / CSV tests), add cases:

| Input | Expected |
|---|---|
| `launch_cwd / "valid.csv"` | accepted |
| `launch_cwd / "bad name.csv"` | `ValueError` |
| `launch_cwd / "../escape.csv"` | `ValueError` (escapes cwd) |
| `launch_cwd / "ok.txt"` | `ValueError` (not `.csv`) |
| `build_orchestrator_calls()` with manifest carrying unsafe explicit `csv_path` | raises before argv built |

**Verify**:
`source mocks/dev-env.sh && python -m pytest tests/test_pure_logic.py -k csv -q`
→ exit 0.

### Step 4: Full test suite

**Verify**: `source mocks/dev-env.sh && python -m pytest tests -q` → exit 0.

## Test plan

- Unit tests for `resolve_csv_output_path()` happy path and rejections.
- Manifest integration test proving unsafe explicit paths fail at
  `build_orchestrator_calls()` time.

## Done criteria

- [ ] Single CSV path validator in `dispatch/sql.py` backs both TUI and manifest.
- [ ] Unsafe explicit `destination["csv_path"]` values raise `ValueError`.
- [ ] `source mocks/dev-env.sh && python -m pytest tests -q` exits 0.
- [ ] `plans/README.md` row for Plan 016 is updated.

## STOP conditions

Stop and report if:

- Production requires CSV filenames outside `[A-Za-z_][A-Za-z0-9_]*.csv` —
  record the requirement; do not silently loosen TUI rules.
- Plan 001 symbols are missing on your branch.
- Fixing tests requires changing `scr/` export behavior beyond argv paths.

## Maintenance notes

- Any future “rerun to CSV” or Browser export shortcut must call
  `resolve_csv_output_path()` or `safe_csv_path()`, not raw `Path` joins.
- Reviewers should confirm hand-edited manifest fixtures in tests use realistic
  explicit paths.
