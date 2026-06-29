# Plan 015: Refresh user-story tracker evidence after implement-plans

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report; do not improvise. When done, update the status row for this plan in
> `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat b33c803..HEAD -- docs/dispatch_user_story_tracker.csv`
> If the tracker changed since this plan was written, reconcile line references
> against live code before editing.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (best after Plans 001–013 merge, but docs-only)
- **Category**: docs
- **Planned at**: commit `b33c803`, 2026-06-29
- **Source**: `codex/implement-plans` branch audit finding #2 (introduced)

## Why this matters

`docs/dispatch_user_story_tracker.csv` is the canonical product-truth index for
agents and reviewers. After the `implement-plans` branch, several rows still
describe a “two **Running**” concurrency cap and cite obsolete `jobs.py` line
ranges. Stale evidence causes false regression reports and misdirected harness
work.

## Current state

Rows that need updating (verify live line numbers before editing):

| Row | Problem |
|---|---|
| `JOB-014` | Says “two simultaneous **Running** jobs”; implementation counts **Pending + Running** under `LAUNCH_SLOT_STATES`. Cites `dispatch/jobs.py:13-64`. |
| `NJ-009` | Says “two-running cap”; cites `dispatch/jobs.py:13-64` and old `new_job.py` validation lines. |
| `NJ-012` | Launch path now uses `jobs.create_job_if_slot_available()` and rollback on spawn failure; line refs stale. |
| `DASH-001` | Cites `dispatch/jobs.py:67-74`; active-job logic now lives in `active_jobs()` ~`L258-274`. |

Key implementation anchors (post-`implement-plans`):

- `dispatch/jobs.py:16-17` — `LAUNCH_SLOT_STATES = {"Pending", "Running"}`.
- `dispatch/jobs.py:168-191` — `launch_slot_jobs()` / `can_launch()`.
- `dispatch/jobs.py:229-255` — `create_job_if_slot_available()` with filesystem lock.
- `dispatch/screens/new_job.py` — `_validate()` and `_launch_flow()` re-validate
  Kerberos and call `create_job_if_slot_available()`.
- Tests: `tests/test_pure_logic.py` — `test_can_launch_false_with_two_pending_jobs`,
  `test_create_job_if_slot_available_serializes_one_remaining_slot`.

CSV format: do not add columns; update `expected_behavior`, `code_evidence`, and
`test_evidence` cells only.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tracker tests | `source mocks/dev-env.sh && python -m pytest tests/test_user_story_tracker.py -q` | exit 0 |
| Verify row IDs | `python -m pytest tests/test_user_story_tracker.py -q` | exit 0 |

## Scope

**In scope**:
- `docs/dispatch_user_story_tracker.csv`

**Out of scope**:
- Source code changes.
- `docs/dispatch_user_story_completion_audit.md` unless a row you touch is
  explicitly mirrored there with the same stale text.
- Rewriting historical audit docs under `docs/audits/`.

## Git workflow

- Branch: `advisor/015-tracker-evidence`
- Commit message: `docs(tracker): align launch-cap evidence with implement-plans`
- Do NOT push unless asked.

## Steps

### Step 1: Update JOB-014 expected behavior and evidence

Change the user story / expected behavior to state that the concurrency cap is
**two launch slots** occupied by `Pending` or `Running` Jobs (not Running alone).

Update `code_evidence` to cite:
- `dispatch/jobs.py` — `RUNNING_CAP`, `LAUNCH_SLOT_STATES`, `can_launch`,
  `create_job_if_slot_available`.
- `dispatch/screens/new_job.py` — preflight `can_launch()` checks.

Update `test_evidence` to cite:
- `tests/test_pure_logic.py` — pending-cap and launch-lock tests (use exact test
  function names from the file).

### Step 2: Update NJ-009 and NJ-012

**NJ-009**: Replace “two-running cap” wording with launch-slot cap
(Pending+Running). Refresh `code_evidence` to identifier validation in
`dispatch/sql.py`, live Kerberos re-check in `_launch_flow()`, and
`jobs.create_job_if_slot_available()`. Refresh `test_evidence` line refs.

**NJ-012**: Note atomic slot acquisition + spawn failure marks manifest
`Failed`. Cite `new_job.py` `_launch_flow()` error handling and
`manifest.update(...)` on `OSError` from `process.launch_runner()`.

### Step 3: Update DASH-001

Point `code_evidence` at `dispatch/jobs.py:active_jobs` and
`dispatch/screens/dashboard.py` refresh worker. Mention bounded scan via
`_cached_terminal_outside_active_window` when present.

### Step 4: Verify tracker integrity

**Verify**:
`source mocks/dev-env.sh && python -m pytest tests/test_user_story_tracker.py -q`
→ exit 0.

If the test file asserts specific strings from the CSV, update only what the
test requires; do not weaken tests.

## Test plan

- Rely on `tests/test_user_story_tracker.py` — no new tests unless that file
  asserts updated evidence strings and fails before your CSV edits.

## Done criteria

- [ ] JOB-014, NJ-009, NJ-012, and DASH-001 rows describe Pending+Running cap
  where applicable.
- [ ] All `code_evidence` and `test_evidence` cells cite paths that exist in the
  current tree (spot-check with ripgrep).
- [ ] `python -m pytest tests/test_user_story_tracker.py -q` exits 0.
- [ ] `plans/README.md` row for Plan 015 is updated.

## STOP conditions

Stop and report if:

- Plans 001–013 are not merged and cited symbols (`create_job_if_slot_available`,
  `active_jobs`) do not exist on your branch — merge or rebase first.
- `tests/test_user_story_tracker.py` encodes obsolete text as required behavior
  and updating the CSV would be incorrect — report the contradiction.
- You need to change product behavior to make the tracker truthful.

## Maintenance notes

- Re-run this plan after any future change to launch-slot semantics or dashboard
  refresh architecture.
- Reviewers should treat the tracker as authoritative only when evidence columns
  match `git grep` spot checks.
