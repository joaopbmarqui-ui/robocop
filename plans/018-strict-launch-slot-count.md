# Plan 018: Make the launch-slot cap strict under corruption

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report; do not improvise. When done, update the status row for this plan in
> `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat b33c803..HEAD -- dispatch/jobs.py tests/test_pure_logic.py`

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: MED
- **Depends on**: plans/002-make-launch-preflight-atomic-and-live.md, plans/003-reconcile-stale-and-pending-jobs.md
- **Category**: bug
- **Planned at**: commit `b33c803`, 2026-06-29
- **Source**: `codex/implement-plans` branch audit finding #5 (introduced)

## Why this matters

`launch_slot_jobs()` stops scanning after it collects `RUNNING_CAP` (2)
Pending/Running manifests. `can_launch()` and `create_job_if_slot_available()`
use that truncated list. If a third slot-consuming manifest exists (manual JSON
edit, partial failure, or restored backup), `len(launch_slot_jobs())` stays 2,
`can_launch()` returns true, and a fourth Job can launch. The product invariant
is two simultaneous launch slots — counting must be exact for enforcement.

## Current state

- `dispatch/jobs.py:168-191` — `launch_slot_jobs()` breaks early:
  ```python
  if item["state"] in LAUNCH_SLOT_STATES:
      loaded.append(item)
      if len(loaded) >= RUNNING_CAP:
          break
  ```
- `dispatch/jobs.py:190-191` — `can_launch()` →
  `len(launch_slot_jobs(root)) < RUNNING_CAP`.
- `dispatch/jobs.py:242-247` — `create_job_if_slot_available()` calls
  `can_launch()` under filesystem lock.
- `tests/test_pure_logic.py:765+` — `test_launch_slot_short_circuit_stops_after_cap`
  asserts the **performance** short-circuit, not strict counting.
- Product invariant (`AGENTS.md`): refuse more than two simultaneously Running
  jobs; Plans 002–003 extended this to Pending+Running launch slots.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Jobs unit tests | `source mocks/dev-env.sh && python -m pytest tests/test_pure_logic.py -k "launch_slot or can_launch" -q` | exit 0 |
| Reconcile tests | `source mocks/dev-env.sh && python -m pytest tests/test_jobs_reconcile.py -q` | exit 0 |
| Full gate | `source mocks/dev-env.sh && python -m pytest tests -q` | exit 0 |

## Scope

**In scope**:
- `dispatch/jobs.py`
- `tests/test_pure_logic.py`

**Out of scope**:
- Changing `RUNNING_CAP` value.
- UI wording in `new_job.py` (unless error message must mention corruption).
- Reconciling how a third Running manifest could appear — only enforce the cap
  correctly when it does.

## Git workflow

- Branch: `advisor/018-strict-launch-slot-count`
- Commit message: `fix(jobs): count all launch slots for cap enforcement`
- Do NOT push unless asked.

## Steps

### Step 1: Split counting from short-circuit listing

In `dispatch/jobs.py`:

1. Add `count_launch_slot_jobs(root: Path | None = None) -> int` that walks
   **all** `_manifest_paths(root)`, reconciles/loads each manifest, and counts
   items in `LAUNCH_SLOT_STATES` without early break.
2. Change `can_launch()` to use `count_launch_slot_jobs(root) < RUNNING_CAP`.
3. Change `create_job_if_slot_available()` to use `count_launch_slot_jobs` inside
   the lock (not `can_launch()` if that would double-scan — acceptable for
   correctness; optimize only if tests prove safe).
4. Keep `launch_slot_jobs()` as a **listing** helper for UI if needed, or rename
   its docstring to clarify it returns at most `RUNNING_CAP` items for display.
   Dashboard/New Job must not use the truncated list for enforcement.

**Verify**: `python -m compileall dispatch` → exit 0.

### Step 2: Add strict-count regression test

In `tests/test_pure_logic.py`, add `test_can_launch_false_when_three_slot_jobs_exist`:

1. Seed **three** manifests with state `Running` or mix of `Pending`/`Running`.
2. Assert `count_launch_slot_jobs(root=jdir) == 3`.
3. Assert `can_launch(root=jdir) is False`.
4. Assert `create_job_if_slot_available(...)` raises `LaunchSlotUnavailable`.

Keep `test_launch_slot_short_circuit_stops_after_cap` — it should still pass for
the **listing** helper if retained.

**Verify**:
`source mocks/dev-env.sh && python -m pytest tests/test_pure_logic.py -k launch_slot -q`
→ exit 0.

### Step 3: Full test suite

**Verify**: `source mocks/dev-env.sh && python -m pytest tests -q` → exit 0.

## Test plan

- Strict count with 3 slot-consuming manifests → `can_launch` false.
- Normal cases: 0, 1, 2 slots → behavior unchanged from existing tests.
- Launch lock serialization test still passes.

## Done criteria

- [ ] Cap enforcement uses a full count, not a truncated scan.
- [ ] New test fails on `b33c803` behavior and passes after the fix.
- [ ] `source mocks/dev-env.sh && python -m pytest tests -q` exits 0.
- [ ] `plans/README.md` row for Plan 018 is updated.

## STOP conditions

Stop and report if:

- Product owners want best-effort cap only — that reverses Plan 002; stop.
- `launch_slot_jobs()` is unused and can be deleted instead of kept — report the
  simplification; do not delete without updating all callers.
- Full counting causes unacceptable SSH latency — propose caching, do not revert
  strictness without operator approval.

## Maintenance notes

- Plan 014/004 performance work must not reintroduce truncated counting for
  `can_launch()`.
- Reviewers should verify `count_launch_slot_jobs` and `launch_slot_jobs` are not
  confused in new call sites.
