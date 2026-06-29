# Plan 020: Tighten the mypy gate incrementally

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report; do not improvise. When done, update the status row for this plan in
> `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat b33c803..HEAD -- pyproject.toml dispatch`

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED
- **Depends on**: plans/007-lint-typecheck-gates.md, plans/008-ci.md
- **Category**: dx
- **Planned at**: commit `b33c803`, 2026-06-29
- **Source**: `codex/implement-plans` branch audit finding #7 (pre-existing config)

## Why this matters

Plan 007 landed mypy in CI with deliberate relaxations so the gate could merge
without a large annotation rewrite. Several `disable_error_code` entries and
`check_untyped_defs = false` mean real regressions in `dispatch/` can pass CI.
This plan tightens the gate in **one incremental slice** — pure logic modules
first — without a repo-wide strict-mode flag day.

## Current state

`pyproject.toml:51-63`:

```toml
[tool.mypy]
python_version = "3.10"
platform = "linux"
packages = ["dispatch"]
exclude = ["scr/", "tools/prod_tui/", "mocks/"]
ignore_missing_imports = true
check_untyped_defs = false
warn_unused_ignores = false
warn_redundant_casts = true
disable_error_code = ["arg-type", "assignment", "attr-defined", "list-item", "typeddict-item"]
```

CI (`.github/workflows/ci.yml:33-34`) runs `mypy dispatch`.

High-value, low-Textual-noise modules to tighten first:

- `dispatch/sql.py` — validators and path helpers; mostly stdlib types.
- `dispatch/jobs.py` — manifest supervision; TypedDict manifests but contained API.
- `dispatch/manifest.py` — job creation and argv building.

**Out of scope for this plan**: `dispatch/screens/*` Textual widgets (defer to a
follow-up plan).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Typecheck | `python -m pip install -e ".[dev]" && mypy dispatch` | exit 0 |
| Tests | `source mocks/dev-env.sh && python -m pytest tests -q` | exit 0 |

## Scope

**In scope**:
- `pyproject.toml` — `[tool.mypy.overrides]` for the three modules above
- `dispatch/sql.py`, `dispatch/jobs.py`, `dispatch/manifest.py` — type fixes only
- Any test files that need trivial annotation/import fixes caused by typing changes

**Out of scope**:
- `scr/`, `mocks/`, `tools/prod_tui/`
- Enabling strict mode globally
- Rewriting Textual screens for full `attr-defined` coverage
- Changing runtime behavior

## Git workflow

- Branch: `advisor/020-tighten-mypy-gate`
- Commit message: `chore(dx): tighten mypy overrides for dispatch core modules`
- Do NOT push unless asked.

## Steps

### Step 1: Add per-module mypy overrides

In `pyproject.toml`, add:

```toml
[[tool.mypy.overrides]]
module = [
    "dispatch.sql",
    "dispatch.jobs",
    "dispatch.manifest",
]
check_untyped_defs = true
warn_unused_ignores = true
disable_error_code = []  # no suppressed codes in this slice
```

Leave the global `[tool.mypy]` section unchanged for other packages.

**Verify**: `mypy dispatch` → expect errors only in the three modules (if any).

### Step 2: Fix reported errors in the three modules

Address mypy findings with minimal annotations:

- Prefer precise types (`Path`, `str | None`, `TypedDict` references) over `Any`.
- Use `typing.cast` only when necessary and document why in a one-line comment if
  non-obvious.
- Do **not** change function behavior to satisfy the checker.

Common patterns in this repo:

- `manifest.JobManifest` / `Destination` TypedDicts — use them instead of `dict`.
- Validators returning `str | None` for error messages.

**Verify**: `mypy dispatch` → exit 0.

### Step 3: Confirm CI parity

Ensure `pip install -e ".[dev]"` includes mypy (already in dev extras from Plan 007).

**Verify**: `mypy dispatch/sql.py dispatch/jobs.py dispatch/manifest.py` → exit 0.

### Step 4: Regression tests

**Verify**: `source mocks/dev-env.sh && python -m pytest tests -q` → exit 0.

## Test plan

- No new behavioral tests required.
- Typing-only changes must not alter test outcomes.

## Done criteria

- [ ] `mypy dispatch` exits 0 with overrides enabled for sql/jobs/manifest.
- [ ] Global relaxed settings remain for other `dispatch` subpackages.
- [ ] `source mocks/dev-env.sh && python -m pytest tests -q` exits 0.
- [ ] `AGENTS.md` lint section notes per-module mypy tightening (one sentence).
- [ ] `plans/README.md` row for Plan 020 is updated.

## STOP conditions

Stop and report if:

- Fixing the three modules requires touching `dispatch/screens/*` beyond imports —
  split work; do not expand scope silently.
- More than ~30 errors appear — stop and report count; propose a smaller module
  slice (e.g. `dispatch/sql.py` only).
- TypedDict changes would alter runtime JSON serialization — do not change manifest
  on-disk shape.

## Maintenance notes

- Follow-up plan should tighten `dispatch/runner.py`, `dispatch/process.py`, then
  screens incrementally.
- When removing a global `disable_error_code`, delete the override duplication for
  modules already strict.
