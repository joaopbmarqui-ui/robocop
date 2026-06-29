# Plan 017: Add CI coverage for offline install guard

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report; do not improvise. When done, update the status row for this plan in
> `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat b33c803..HEAD -- .github/workflows/ci.yml install.sh tests/test_install_onboarding.py`

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: plans/008-ci.md, plans/006-offline-install-guard.md
- **Category**: tests
- **Planned at**: commit `b33c803`, 2026-06-29
- **Source**: `codex/implement-plans` branch audit finding #4 (introduced)

## Why this matters

Plan 006 made `install.sh` fail fast when `vendor/` has no wheels and
`DISPATCH_ALLOW_ONLINE_PIP` is unset — the edge-node offline install path.
Plan 008 added GitHub Actions CI, but CI only runs `pip install -e ".[dev]"` from
PyPI. The offline guard is covered by local tests
(`tests/test_install_onboarding.py`) yet never runs in CI, so regressions can
ship green.

## Current state

- `install.sh:41-52` — empty `vendor/` exits 1 unless
  `DISPATCH_ALLOW_ONLINE_PIP=1`.
- `tests/test_install_onboarding.py:48+` —
  `test_install_fails_when_vendor_empty_and_no_online_opt_in` exercises that
  branch with a fake environment.
- `.github/workflows/ci.yml:21-38` — installs dev deps from PyPI; runs pytest
  but does not isolate or highlight install-script tests.
- `AGENTS.md` documents CI running on push/PR to `main`.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Install tests locally | `python -m pytest tests/test_install_onboarding.py -q` | exit 0 |
| CI workflow syntax | valid YAML; GitHub Actions will validate on push | — |

## Scope

**In scope**:
- `.github/workflows/ci.yml`
- Optionally `tests/test_install_onboarding.py` only if a test rename/split is
  needed for a stable CI filter

**Out of scope**:
- Changing `install.sh` behavior.
- Building a real Linux wheelhouse in CI.
- Running full edge-node `install.sh` end-to-end (too heavy for default CI).

## Git workflow

- Branch: `advisor/017-ci-install-guard`
- Commit message: `ci: run offline install guard tests`
- Do NOT push unless asked.

## Steps

### Step 1: Add a dedicated CI step for install onboarding tests

In `.github/workflows/ci.yml`, after the dev dependency install and before or
after the main test step, add:

```yaml
      - name: Offline install guard tests
        run: python -m pytest tests/test_install_onboarding.py -q
```

Rationale: keep install tests visible and fast; they do not require
`mocks/dev-env.sh` because they subprocess `install.sh` with crafted env vars.

If the full suite already runs `tests/` and you prefer a separate job instead,
add a second job `install-guard` that checks out the repo, sets up Python 3.12
only, and runs the command above. Choose one approach — do not duplicate the
entire matrix twice without reason.

**Verify**: `python -m pytest tests/test_install_onboarding.py -q` → exit 0
locally.

### Step 2: Document CI coverage in AGENTS.md (one paragraph)

Under the CI bullet added by Plan 008, note that CI explicitly runs
`tests/test_install_onboarding.py` for the empty-`vendor/` guard.

**Verify**: `rg "test_install_onboarding" AGENTS.md` → one match.

### Step 3: Confirm main test step still passes

**Verify**: `python -m pytest tests tools/prod_tui/tests -q` → exit 0 locally.

## Test plan

- No new tests required if `test_install_fails_when_vendor_empty_and_no_online_opt_in`
  already passes.
- Optional: add `test_install_succeeds_with_vendor_wheels` only if CI needs a
  positive counterpart — skip unless the executor finds zero positive coverage.

## Done criteria

- [ ] CI workflow runs `tests/test_install_onboarding.py` on every PR/push.
- [ ] `python -m pytest tests/test_install_onboarding.py -q` exits 0 locally.
- [ ] `AGENTS.md` mentions install-guard CI coverage.
- [ ] `plans/README.md` row for Plan 017 is updated.

## STOP conditions

Stop and report if:

- Plan 006 install guard is absent on your branch.
- Install tests require bash paths unavailable on `ubuntu-latest` — propose a
  `shell: bash` fix, do not skip silently.
- Tests need network access the guard is meant to avoid.

## Maintenance notes

- If `install.sh` gains new offline requirements (wheel platform tags, etc.),
  extend `test_install_onboarding.py` first, then keep the dedicated CI step.
- A future job that builds `vendor/` in CI belongs in a separate plan; do not
  conflate it here.
