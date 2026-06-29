# Dispatch Improvement Plans

This is the consolidated implementation backlog from PRs #23 and #24, vetted
against local `main` at commit `8b4241e`. PR #23 provides the five core plans.
Unique findings from PR #24 were either added as Plans 006-012, folded into an
existing core plan, or explicitly rejected/deferred below.

Execute plans in dependency order. Each executor must read its assigned plan
fully, honor its STOP conditions, run every verification command, and update
the status row when done.

## Execution order and status

| Plan | Title | Priority | Effort | Depends on | Status |
|---|---|---|---|---|---|
| 001 | Harden launch identifiers and CSV output paths | P1 | M | - | DONE |
| 002 | Make launch preflight live and enforce the Job cap at creation | P1 | M | 001 | DONE |
| 003 | Reconcile stale Running and orphan Pending Jobs | P1 | M | 002 | DONE |
| 004 | Bound manifest refresh work for SSH-scale supervision | P2 | M | 002, 003 | DONE |
| 005 | Expand runner and `scr/` contract coverage before deeper orchestrator work | P2 | M | - | DONE |
| 006 | Guard offline installation when `vendor/` is empty | P2 | M | - | DONE |
| 007 | Add conservative lint and typecheck gates | P2 | M | - | TODO |
| 008 | Add GitHub Actions CI | P2 | M | 007 | TODO |
| 009 | Cap Job Detail log-tail reads per refresh tick | P2 | S | - | DONE |
| 010 | Align the `config.json` email schema | P2 | M | - | DONE |
| 011 | Unify the product version source | P3 | S | - | DONE |
| 012 | Apply restrictive permissions to per-user Job data | P3 | S | 003 | DONE |

Status values: TODO | IN PROGRESS | DONE | BLOCKED (with one-line reason) |
REJECTED (with one-line rationale).

## Recommended execution waves

1. **Launch correctness and security:** 001, 002, 003.
2. **Supervision performance and coverage:** 004, 005, 009.
3. **Installation and developer gates:** 006, 007, then 008.
4. **Configuration and low-risk hygiene:** 010, 011, 012.

Plans without dependencies may run independently, but changes to the same file
must still be serialized. In particular:

- 001 and 002 both edit `dispatch/screens/new_job.py`; run 001 first.
- 003 follows 002 because launch-slot semantics define which manifests consume
  capacity.
- 004 follows 002 and 003 so refresh optimization preserves launch-cap and
  stale-Job reconciliation behavior.
- 008 follows 007 because CI invokes the lint and typecheck gates.
- 012 follows 003 because both plans touch Job-directory lifecycle behavior.
- 005 may run independently, but coordinate its `tests/test_pure_logic.py`
  changes with Plan 001.

## Consolidation decisions

### Folded into core plans

- PR #24 stale-Running reconciliation and Pending cancellation are covered by
  Plan 003.
- PR #24 synchronous New Job scans, manifest-cache concurrency, bounded
  dashboard scans, and hidden-screen refresh work belong in Plan 004. Executors
  must choose one coherent refresh design rather than landing four interacting
  micro-fixes independently.
- PR #24 identifier validation is covered more completely by Plan 001, including
  CSV path containment and production-orchestrator entry validation.
- PR #24 validation deduplication and runner/classifier tests are covered by
  Plans 002 and 005.

### Rejected

- **Change Impala `SHOW TABLES LIKE` from `*` to `%`:** incorrect. Impala uses
  Unix-style `*` wildcards for SHOW patterns; `%` is not the equivalent here.
- **Change production-harness SSH from `StrictHostKeyChecking=no` to
  `accept-new`:** the current choice is documented in the Edge operating model.
  Changing operator SSH policy is not a source-only cleanup.
- **Immediately consolidate `scr/` retry loops:** production-sensitive and lower
  confidence. Land Plan 005 characterization coverage before proposing this
  behavior-preserving refactor.
- **Treat UPDATE/DELETE/REPLACE/CALL as self-contained DDL:** the current helper
  is deliberately scoped to DDL leaders. Expanding statement classes requires a
  product requirement and safety review, not an opportunistic fix.

### Deferred or tracked as direction

- Resume partial `Table+Csv` Jobs and add per-step manifest progress after the
  launch/reconciliation plans establish the state contract.
- Add one-keystroke rerun and Browser-to-CSV shortcuts as post-v1 product work.
- Investigate the SqlTemplate `_fulljoin` naming contract only if users report
  ambiguity or downstream integration failures.
- Revisit monthly-query architecture only with production evidence. Commit
  `8b4241e` already pins dependent monthly statements to one Impala session.

## Source PR disposition

- PR #23 is fully represented by Plans 001-005.
- PR #24 contributes Plans 006-012 and the decisions above; its duplicate,
  invalid, unrelated, and policy-sensitive recommendations are intentionally
  not copied as standalone plans.
- Neither PR should be merged after this consolidation commit lands on `main`.
