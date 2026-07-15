# Secure Usage Telemetry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship PR #38's offline usage telemetry as a standalone, non-blocking, symlink-safe replacement PR with complete instrumentation.

**Architecture:** Keep event construction synchronous and bounded, then enqueue validated records to one daemon writer thread. The writer owns all filesystem work, opens shared files without following symlinks, verifies file ownership and type, applies analyst-readable permissions, and skips contended locks. Event-specific public functions replace arbitrary event/property dictionaries.

**Tech Stack:** Python 3.10+, standard-library `queue`, `threading`, `os`, `fcntl`, Textual, pytest.

---

### Task 1: Import the telemetry feature baseline

**Files:**
- Add: `dispatch/telemetry.py`
- Add: `tests/test_telemetry.py`
- Add: `docs/superpowers/specs/2026-07-11-usage-telemetry-design.md`
- Modify: `README.md`
- Modify: `dispatch/__main__.py`
- Modify: `dispatch/app.py`
- Modify: `dispatch/screens/job_detail.py`
- Modify: `dispatch/screens/new_job.py`
- Modify: `update.sh`

- [ ] Cherry-pick PR #38's three commits in order.
- [ ] Run `ruff format dispatch/screens/new_job.py` to remove the baseline CI formatting failure.
- [ ] Run `/workspace/.venv/bin/python -m pytest tests/test_telemetry.py -q`.
- [ ] Commit only if formatting changes the imported baseline.

### Task 2: Specify and test secure shared appends

**Files:**
- Modify: `tests/test_telemetry.py`
- Modify: `dispatch/telemetry.py`

- [ ] Add a test that creates `users/<name>.jsonl` as a symlink, emits an event, flushes the writer, and asserts the target is unchanged.
- [ ] Add a test that emits under `umask(0o077)` and asserts the shared JSONL mode is `0o644`.
- [ ] Add a test that pre-creates another-UID or non-regular shared target through a patched ownership check and asserts it is skipped.
- [ ] Run the three tests and verify they fail against PR #38.
- [ ] Open shared files with `O_APPEND | O_CREAT | O_WRONLY | O_CLOEXEC | O_NOFOLLOW`, verify `fstat()` reports a regular file owned by the effective user, and apply `fchmod(0o644)`.
- [ ] Move `fcntl` to module scope and use `LOCK_EX | LOCK_NB`; skip the shared or private append on contention.
- [ ] Re-run the three tests and verify they pass.

### Task 3: Make TUI emission non-blocking and typed

**Files:**
- Modify: `tests/test_telemetry.py`
- Modify: `dispatch/telemetry.py`
- Modify: `dispatch/app.py`
- Modify: `dispatch/screens/new_job.py`
- Modify: `dispatch/screens/job_detail.py`

- [ ] Add a test that holds a JSONL lock, calls a public event function, and asserts the call returns before a short deadline.
- [ ] Add tests that invalid screen/refusal values and unknown properties cannot enter a record.
- [ ] Run the tests and verify they fail against PR #38.
- [ ] Add a bounded `queue.Queue`, one lazily started daemon writer, and a test-visible `flush(timeout)` helper; queue saturation drops events with debug logging.
- [ ] Replace `emit(event, props)` with event-specific functions: `note_session_start`, `note_session_end`, `note_screen_view`, `note_job_launched`, `note_launch_refused`, and `note_job_cancelled`.
- [ ] Update TUI call sites to use the event-specific functions.
- [ ] Re-run the focused tests and verify they pass.

### Task 4: Correct launch and navigation instrumentation

**Files:**
- Modify: `tests/test_telemetry.py`
- Modify: `tests/test_ui_ux_audit_implementation.py`
- Modify: `dispatch/screens/new_job.py`
- Modify: `dispatch/screens/history.py`

- [ ] Add a launch-flow test where `process.launch_runner` raises after Job creation and assert `job_launched` was recorded.
- [ ] Add a History navigation test that opens Job Detail and asserts the app-level telemetry helper is used.
- [ ] Run both tests and verify they fail against PR #38.
- [ ] Record `job_launched` immediately after successful Job creation and before awaiting runner startup.
- [ ] Route both History Job Detail entry points through `DispatchApp.open_job_detail`.
- [ ] Re-run both tests and verify they pass.

### Task 5: Align documentation and CLI

**Files:**
- Modify: `docs/superpowers/specs/2026-07-11-usage-telemetry-design.md`
- Modify: `README.md`
- Modify: `dispatch/__main__.py`
- Modify: `tests/test_telemetry.py`

- [ ] Update the design from synchronous direct writes to the bounded writer queue and document best-effort drop behavior.
- [ ] Document symlink, ownership, mode, and nonblocking-lock protections.
- [ ] Keep `--user` only on `telemetry summary`, matching the documented CLI.
- [ ] Add CLI parser coverage for accepted and rejected argument shapes.
- [ ] Run `/workspace/.venv/bin/python -m pytest tests/test_telemetry.py -q`.

### Task 6: Verify and ship

**Files:**
- Verify all changed product, test, and documentation files.

- [ ] Run `/workspace/.venv/bin/python -m compileall dispatch scr`.
- [ ] Run `/workspace/.venv/bin/ruff check dispatch tests`.
- [ ] Run `/workspace/.venv/bin/ruff format --check dispatch tests`.
- [ ] Run `/workspace/.venv/bin/mypy dispatch/sql.py dispatch/jobs.py dispatch/manifest.py`.
- [ ] Run `/workspace/.venv/bin/python -m pytest -n 4 --dist loadfile`.
- [ ] Source `mocks/dev-env.sh`, launch Dispatch from a directory containing SQL, and exercise startup, History → Job Detail, and quit while confirming telemetry CLI output.
- [ ] Review the final diff against the telemetry design and verify no temporary diagnostics remain.
- [ ] Commit focused changes, push `cursor/secure-usage-telemetry-86ac`, and open a draft PR against `main` with validation and release-risk notes.
