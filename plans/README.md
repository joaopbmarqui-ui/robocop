# Dispatch Improvement Plans

Plans **001–013** were implemented on branch `codex/implement-plans` (HEAD
`b33c803` at audit time). Plans **014–020** are follow-up work from the
`codex/implement-plans` vs `main` branch audit (2026-06-29).

Execute in dependency order. Each executor must read its assigned plan fully,
honor STOP conditions, run every verification command, and update the status row
when done.

## Execution order and status

| Plan | Title | Priority | Effort | Depends on | Status |
|---|---|---|---|---|---|
| 001 | Harden launch identifiers and CSV output paths | P1 | M | - | DONE on `codex/implement-plans` |
| 002 | Make launch preflight live and enforce the Job cap at creation | P1 | M | 001 | DONE on `codex/implement-plans` |
| 003 | Reconcile stale Running and orphan Pending Jobs | P1 | M | 002 | DONE on `codex/implement-plans` |
| 004 | Bound manifest refresh work for SSH-scale supervision | P2 | M | 002, 003 | DONE on `codex/implement-plans` |
| 005 | Expand runner and `scr/` contract coverage | P2 | M | - | DONE on `codex/implement-plans` |
| 006 | Guard offline installation when `vendor/` is empty | P2 | M | - | DONE on `codex/implement-plans` |
| 007 | Add conservative lint and typecheck gates | P2 | M | - | DONE on `codex/implement-plans` |
| 008 | Add GitHub Actions CI | P2 | M | 007 | DONE on `codex/implement-plans` |
| 009 | Cap Job Detail log-tail reads per refresh tick | P2 | S | - | DONE on `codex/implement-plans` |
| 010 | Align the `config.json` email schema | P2 | M | - | DONE on `codex/implement-plans` |
| 011 | Unify the product version source | P3 | S | - | DONE on `codex/implement-plans` |
| 012 | Apply restrictive permissions to per-user Job data | P3 | S | 003 | DONE on `codex/implement-plans` |
| 013 | Harden production `scr/` orchestrators | P1 | M | 005, 007 | DONE on `codex/implement-plans` |
| 014 | Bound History manifest refresh work | P2 | M | 004 | DONE |
| 015 | Refresh user-story tracker evidence | P2 | S | - | DONE |
| 016 | Harden explicit CSV paths in manifests | P2 | S | 001 | DONE |
| 017 | Add CI coverage for offline install guard | P2 | S | 006, 008 | DONE (already covered; docs synced) |
| 018 | Make the launch-slot cap strict under corruption | P2 | S | 002, 003 | DONE |
| 019 | Reconcile orphan Pending jobs after runner startup failure | P2 | M | 003 | DONE (mtime grace policy) |
| 020 | Tighten the mypy gate incrementally | P3 | M | 007, 008 | DONE |

Status values: TODO | IN PROGRESS | DONE | BLOCKED (with one-line reason) |
REJECTED (with one-line rationale).

## Recommended execution waves

### Wave A — merge `codex/implement-plans`

Land Plans 001–013 via merge/rebase of `codex/implement-plans` onto `main`.
Run full `pytest` and edge harness smoke before deploy.

### Wave B — docs and quick hardening (post-merge)

1. **015** — tracker evidence (docs only; no code conflict).
2. **016** — explicit CSV path validation (`dispatch/sql.py`, `dispatch/manifest.py`).
3. **017** — CI install-guard step (`.github/workflows/ci.yml`).

### Wave C — supervision correctness

4. **018** — strict launch-slot counting (`dispatch/jobs.py`).
5. **019** — orphan Pending reconciliation (`dispatch/jobs.py`; coordinate with 018).
6. **014** — History refresh bounds (`dispatch/jobs.py`; builds on 004 cache helpers).

### Wave D — typing hygiene

7. **020** — incremental mypy tightening (`pyproject.toml`, core `dispatch/` modules).

## Dependency graph (014–020)

```text
004 ──► 014
001 ──► 016
006 ──► 017 ◄── 008
002 ──► 018 ◄── 003
003 ──► 019 (run after 018 if both touch jobs.py)
007 ──► 020 ◄── 008
015 (independent)
```

Serialize edits to `dispatch/jobs.py`: **018 → 019 → 014**.

## Branch audit source (2026-06-29)

| Plan | Audit finding |
|---|---|
| 014 | History uses full `reconciled_list_manifests()` scan (introduced) |
| 015 | User-story tracker stale vs Pending+Running cap (introduced) |
| 016 | Explicit manifest `csv_path` containment-only (introduced) |
| 017 | CI skips offline `install.sh` guard tests (introduced) |
| 018 | `can_launch()` undercounts when >2 slot jobs exist (introduced) |
| 019 | Stuck Pending without pid after runner crash (pre-existing) |
| 020 | Permissive mypy baseline (pre-existing config) |

## Consolidation decisions (001–013)

Unchanged from the original consolidation — see plan files 001–012 and
`plans/013-scr-hardening-design.md`. Rejected items (Impala `%` wildcard, SSH
`StrictHostKeyChecking` policy change, opportunistic `scr/` retry consolidation)
remain rejected.

## Findings considered and rejected

- **Monthly coordinator pin regression** — intentional fix on `main` (`59b1b02`);
  branch adds tests and `render_monthly_sql()`, not a defect.
- **`cycle_through_pools` retry-count semantics** — intentional Plan 013 behavior;
  covered by `tests/test_scr_common.py`.
- **Merge without edge harness** — not a code plan; operators must still run
  `tools/prod_tui` smoke before production deploy.
