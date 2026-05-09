# `scr/` modification policy

The orchestrator scripts in `scr/` (`Query_Impala_Parametrized.py`,
`download_to_csv.py`, `monthly_query_processor.py`) are production-tested by
usage rather than by an automated test suite. They have known internal
duplications and one hardcoded path that future authors will be tempted to
clean up. This ADR defines what is and isn't allowed.

## What is allowed

- **Obvious bug fixes** (typos in error strings, off-by-one in retry counts,
  unambiguous logic errors).
- **Factorisation of duplicated code** into a shared module (proposed name:
  `scr/_common.py`), specifically:
  - `classificar_erro_impala` — currently exists in two divergent versions
    in `Query_Impala_Parametrized.py` and `download_to_csv.py`. Reconciled
    behaviour must be a strict superset of both.
  - `send_email` — duplicated; consolidate.
  - The retry loop pattern — three implementations with subtle drift in
    `Query_Impala_Parametrized.retry_loop`,
    `download_to_csv.retry_loop`, and
    `monthly_query_processor.execute_step_with_retry`. A single
    `cycle_through_pools` helper.
- **Configuration externalised via env vars** with the current hardcoded
  value as the default — most importantly,
  `'/ads_storage/hadoop_query_launcher/scr/download_to_csv.py'` hardcoded in
  `Query_Impala_Parametrized.export_table_to_csv`, which becomes
  `os.environ.get('DISPATCH_SCR_DIR', '/ads_storage/dispatch/scr')`.
  `MAILHOST` similarly externalises `mailhost.mclocal.int`. This is what
  makes the mock layer (ADR-0004) viable.
- **Removal of dead code** (e.g. the `--download` path of
  `Query_Impala_Parametrized.py` once the legacy GUI is hard-deleted at
  v1.0; see ADR-0003).

## What is not allowed

- Restructuring the public CLI surface (argv shape, flag names, exit codes).
- Changing the email format or subjects.
- Touching the queue list `["adhoc_fast", "acs_small", "adhoc_small",
  "acs_large", "adhoc"]` or the retry timing constants.
- Anything not traceable to a specific, narrow improvement.

## Required process for any `scr/` change

1. PR description carries an explicit `[scr/]` tag and a paragraph stating:
   what changed, why it's safe, what the regression risk is.
2. The change must run green against every scenario in `mocks/scenarios/`
   (see ADR-0004). New scenarios are added if the change exposes
   uncovered behaviour.
3. Two reviewers, at least one of whom has personally run the previous
   version of the script in production.
4. Behavioural-equivalence proof in the PR: side-by-side log captures from a
   pre-change and post-change run on the same mock scenarios.

## Considered alternatives

- **Strict no-touch forever.** Rejected because the duplications grow into
  real bugs over time (the two `classificar_erro_impala` variants already
  classify a few errors differently), and because the hardcoded path makes
  the mock layer impossible without an out-of-tree wrapper.
- **Wholesale rewrite of `scr/`.** Rejected: the risk profile is wrong.
  Surgical, mock-validated changes accumulate the cleanup with bounded
  blast radius.

## Consequences

- ADR-0004 (mock layer) is a hard prerequisite for any change under this
  policy. No `scr/` changes merge before the mock layer lands.
- The `_common.py` module's public API becomes a frozen contract once it
  exists, with the same care as `scr/`'s scripts themselves.
