# Plan 014: Bound History manifest refresh work

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report; do not improvise. When done, update the status row for this plan in
> `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat b33c803..HEAD -- dispatch/jobs.py dispatch/screens/history.py tests/test_pure_logic.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: plans/004-bound-manifest-refresh-work.md (must be merged first)
- **Category**: perf
- **Planned at**: commit `b33c803`, 2026-06-29
- **Source**: `codex/implement-plans` branch audit finding #1 (introduced)

## Why this matters

Plan 004 optimized Overview refresh (`active_jobs`) and launch-cap scans
(`launch_slot_jobs` short-circuit), but History still calls
`reconciled_list_manifests()` which reconciles **every** manifest on mount and
on every manual refresh. Operators with hundreds of job directories pay full JSON
parse + PID reconciliation cost each time they open History over SSH, even though
History only needs terminal jobs older than the seven-day supervision window.

## Current state

- `dispatch/jobs.py:47-66` — `_cached_terminal_outside_active_window()` already
  identifies unchanged terminal manifests outside `ACTIVE_WINDOW` using mtime +
  cache; Overview skips reconcile for them.
- `dispatch/jobs.py:258-274` — `active_jobs()` uses that skip helper before
  calling `reconcile_manifest()`.
- `dispatch/jobs.py:277-284` — `history_jobs()` ignores the skip helper and
  always iterates `reconciled_list_manifests(root)`:
  ```python
  def history_jobs(root: Path | None = None) -> list[manifest.JobManifest]:
      now = datetime.now(timezone.utc)
      result = []
      for item in reconciled_list_manifests(root):
          finished = parse_time(item["finished_at"])
          if finished is not None and now - finished > ACTIVE_WINDOW:
              result.append(item)
      return result
  ```
- `dispatch/screens/history.py:83,100` — loads History via
  `jobs.history_jobs()` on mount and `refresh_history()`.
- Product vocabulary: `CONTEXT.md` uses **Job** and terminal states
  (`Succeeded`, `Failed`, `Cancelled`); do not rename them.
- Exemplar to mirror: `active_jobs()` in the same file — same cache, same
  `ACTIVE_WINDOW`, opposite filter predicate.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Focused jobs tests | `source mocks/dev-env.sh && python -m pytest tests/test_pure_logic.py -k "history or active_jobs" -q` | exit 0 |
| Full gate | `source mocks/dev-env.sh && python -m pytest tests -q` | exit 0 |
| Compile | `python -m compileall dispatch scr` | exit 0 |

On Windows without `source`, set `PATH` to include `mocks/bin` and
`DISPATCH_DATA_ROOT` to a writable temp dir the way `tests/conftest.py` does,
then run `py -m pytest`.

## Suggested executor toolkit

Read `.agents/skills/dispatch-textual-tui/SKILL.md` before editing
`dispatch/screens/history.py` if any UI refresh timing changes are needed.

## Scope

**In scope**:
- `dispatch/jobs.py`
- `tests/test_pure_logic.py` (or `tests/test_jobs_reconcile.py` if a better fit)

**Out of scope**:
- `dispatch/screens/dashboard.py` — already optimized.
- `dispatch/screens/history.py` — should not need changes if `history_jobs()`
  becomes cheap; do not add periodic auto-refresh.
- Pagination changes in the History UI.

## Git workflow

- Branch: `advisor/014-bound-history-refresh`
- Commit message style: `perf(jobs): skip reconcile for cached history manifests`
- Do NOT push or open a PR unless the operator asks.

## Steps

### Step 1: Refactor `history_jobs()` to reuse the terminal cache skip

In `dispatch/jobs.py`, rewrite `history_jobs()` to walk `_manifest_paths(root)`
directly (like `active_jobs()`), not `reconciled_list_manifests()`:

1. For each manifest path, if `_cached_terminal_outside_active_window(path, now)`
   is true, take the cached item from `_manifest_cache[path][1]` and append it
   to the result (it is already terminal and outside the active window).
2. Otherwise call `reconcile_manifest(path) or _load_manifest_cached(path)`,
   then include it only when `finished_at` is set and older than
   `ACTIVE_WINDOW`.
3. Call `_prune_manifest_cache(paths)` before returning.

Do **not** call `reconcile_manifest()` for unchanged old terminal manifests —
that is the performance win.

**Verify**: `python -m compileall dispatch` → exit 0.

### Step 2: Add regression tests for bounded History scans

In `tests/test_pure_logic.py` beside the existing `active_jobs` / `can_launch`
tests, add tests that:

1. Seed many terminal manifests outside `ACTIVE_WINDOW` in a temp jobs root.
2. Monkeypatch `reconcile_manifest` to append to a `calls` list.
3. Call `history_jobs(root=jdir)` and assert `reconcile_manifest` was **not**
   called for manifests that `_cached_terminal_outside_active_window` would skip
   (preload cache via one `history_jobs()` call, then reset `calls`, then call
   again with unchanged mtimes).
4. Assert `history_jobs()` still returns only terminal jobs older than seven
   days and excludes `Running` / recent terminal jobs.

Model the monkeypatch pattern after
`test_launch_slot_short_circuit_stops_after_cap` in the same file.

**Verify**:
`source mocks/dev-env.sh && python -m pytest tests/test_pure_logic.py -k history -q`
→ exit 0.

### Step 3: Run the full test suite

**Verify**: `source mocks/dev-env.sh && python -m pytest tests -q` → exit 0.

## Test plan

- New unit tests proving History skips `reconcile_manifest` for cached old
  terminal manifests with unchanged mtime.
- Regression test that a changed mtime still triggers reconcile/load.
- Regression test that `Running` and recent terminal jobs never appear in
  `history_jobs()`.

## Done criteria

- [ ] `history_jobs()` no longer calls `reconciled_list_manifests()`.
- [ ] Tests demonstrate skipped reconcile for unchanged cached history manifests.
- [ ] `source mocks/dev-env.sh && python -m pytest tests -q` exits 0.
- [ ] `python -m compileall dispatch scr` exits 0.
- [ ] `plans/README.md` row for Plan 014 is updated.

## STOP conditions

Stop and report if:

- Plan 004 helpers (`_cached_terminal_outside_active_window`, manifest cache)
  are absent — merge Plan 004 first.
- History must include in-window terminal jobs (product change) — that
  contradicts current `ACTIVE_WINDOW` semantics; do not improvise.
- Any in-scope file changed since `b33c803` and excerpts no longer match.
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- If History gains auto-refresh, keep using `history_jobs()` — do not inline
  filesystem walks in the screen.
- Reviewers should confirm cache coherency: a manifest moved from Running to
  Failed must change mtime and therefore reconcile on the next History load.
