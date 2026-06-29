# Plan 019: Reconcile orphan Pending jobs after runner startup failure

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report; do not improvise. When done, update the status row for this plan in
> `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat b33c803..HEAD -- dispatch/jobs.py dispatch/runner.py dispatch/process.py dispatch/screens/new_job.py tests`

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: plans/003-reconcile-stale-and-pending-jobs.md
- **Category**: bug
- **Planned at**: commit `b33c803`, 2026-06-29
- **Source**: `codex/implement-plans` branch audit finding #6 (pre-existing, mitigated partially)

## Why this matters

Plan 003 reconciles dead **Running** PIDs and lets users cancel **Pending** jobs
without a PID manually. A gap remains: if the detached runner exits before it
updates the manifest to `Running` (import error, immediate crash, missing
`dispatch` module), the manifest stays `Pending` with `pid: null` indefinitely
and consumes a launch slot until the user opens Job Detail and cancels. Automatic
reconciliation should recover these orphan Pending jobs after a conservative
age threshold.

## Current state

- `dispatch/process.py:29-42` — `launch_runner()` spawns
  `nohup setsid python -m dispatch.runner --job-dir ...` and returns the wrapper
  PID; it does **not** write the manifest.
- `dispatch/runner.py:103-117` — runner sets `Running` + `pid` only after
  opening `run.log`; failures before that leave `Pending`.
- `dispatch/jobs.py:119-148` — `reconcile_manifest()` only acts on
  `state == "Running"` with dead PID.
- `dispatch/screens/job_detail.py:468-479` — manual Pending cancel without PID.
- `dispatch/screens/new_job.py` — marks `Failed` only when `launch_runner()`
  raises `OSError`, not when the runner process dies later before updating state.
- Plan 003 explicitly deferred automatic Pending age policy; this plan adds it.

Constants to introduce: `PENDING_ORPHAN_GRACE = timedelta(minutes=5)` (adjust only
if tests prove too aggressive).

Manifest timestamps: use `created_at` from manifest JSON (written at job
creation in `manifest.create_job()`).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Reconcile tests | `source mocks/dev-env.sh && python -m pytest tests/test_jobs_reconcile.py -q` | exit 0 |
| Launch flow tests | `source mocks/dev-env.sh && python -m pytest tests/test_phase1_safety.py tests/test_new_features.py -q` | exit 0 |
| Full gate | `source mocks/dev-env.sh && python -m pytest tests -q` | exit 0 |

## Suggested executor toolkit

Read `.agents/skills/dispatch-textual-tui/SKILL.md` before changing cancel or
notification strings.

## Scope

**In scope**:
- `dispatch/jobs.py`
- `tests/test_jobs_reconcile.py`

**Out of scope**:
- Rewriting `launch_runner()` to synchronously wait for runner readiness — too
  fragile over SSH.
- Changing `RUNNING_CAP` or launch-lock design.
- Auto-failing Pending jobs that are merely slow to start within the grace window.

## Git workflow

- Branch: `advisor/019-reconcile-orphan-pending`
- Commit message: `fix(jobs): fail orphan Pending jobs after startup grace`
- Do NOT push unless asked.

## Steps

### Step 1: Extend `reconcile_manifest()` for aged Pending without PID

In `dispatch/jobs.py`, after the Running/dead-PID branch:

1. If `state == "Pending"` and `pid is None`:
2. Parse `created_at`; if missing, do not reconcile (conservative).
3. If `now - created_at > PENDING_ORPHAN_GRACE`, call `manifest.update()` to
   set `state="Failed"`, `exit_code=-1`, `finished_at=now`, and append a line to
   `run.log` if present:
   `[dispatch] Pending job exceeded startup grace; manifest marked Failed`
4. Invalidate manifest cache entry for that path (same as stale Running path).

Do **not** reconcile fresh Pending jobs — runners need time to flip to Running.

**Verify**: `python -m compileall dispatch` → exit 0.

### Step 2: Ensure cap and overview paths invoke reconcile

Confirm `launch_slot_jobs`, `count_launch_slot_jobs` (Plan 018), and
`active_jobs` already call `reconcile_manifest()` per path — orphan Pending
should disappear from slot counts after grace without new call sites. If Plan 018
is not merged, ensure `can_launch()` path still reconciles.

**Verify**: read call graph; add one comment in `reconcile_manifest()` docstring
noting Pending orphan policy.

### Step 3: Add tests

In `tests/test_jobs_reconcile.py`:

1. `test_orphan_pending_without_pid_reconciles_after_grace` — create Pending job
   with `created_at` older than grace (monkeypatch `jobs.PENDING_ORPHAN_GRACE` or
   manifest timestamp); assert reconcile → `Failed`.
2. `test_fresh_pending_without_pid_stays_pending` — `created_at` recent; assert
   state unchanged.
3. `test_orphan_pending_frees_launch_slot` — two fresh Pending + one orphan;
   after reconcile, `can_launch()` true (coordinate with Plan 018 helpers).

Use `freezegun` only if already a dependency; otherwise monkeypatch
`datetime.now` or pass explicit timestamps into manifest fixtures.

**Verify**:
`source mocks/dev-env.sh && python -m pytest tests/test_jobs_reconcile.py -q`
→ exit 0.

### Step 4: Full test suite

**Verify**: `source mocks/dev-env.sh && python -m pytest tests -q` → exit 0.

## Test plan

- Aged Pending without PID → Failed with log note.
- Fresh Pending → untouched.
- Launch slot freed after orphan reconciliation.

## Done criteria

- [ ] `reconcile_manifest()` fails orphan Pending jobs after grace period.
- [ ] Tests cover grace pass and grace fail cases.
- [ ] `source mocks/dev-env.sh && python -m pytest tests -q` exits 0.
- [ ] `plans/README.md` row for Plan 019 is updated.

## STOP conditions

Stop and report if:

- Manifests lack `created_at` in production fixtures — propose backfill or alternate
  signal (`run.log` empty + mtime); do not guess.
- Five-minute grace is demonstrably shorter than real runner startup on edge nodes
  — report measured startup time.
- Product requires Pending to block forever until manual cancel — contradicts this
  plan; stop.

## Maintenance notes

- If runner later writes an early “starting” heartbeat, narrow the orphan rule to
  avoid racing legitimate slow starts.
- Update Plan 015 / JOB-014 tracker row if expected behavior mentions manual-only
  Pending recovery.
