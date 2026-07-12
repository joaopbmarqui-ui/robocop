# Query Optimization Advisor — implementation spec

Status: **signed off by the sponsor 2026-07-11**; merge of the PR chain
rests with a Maintainer. Assembled from the decisions of the
[Query Optimization Advisor map](wayfinder/query-optimization-advisor/map.md);
every section links the ticket that locked it. Disagreements found during
implementation reopen the relevant ticket, not this document.

## What ships

A pre-launch **Advisor** in the Dispatch TUI that statically checks a Job's
SQL against the
[Impala optimization manual](wayfinder/query-optimization-advisor/assets/impala-optimization-manual.md)
(v2.0) and reports **Findings**. The advisor is **flag-only**: it never
mutates the user's `.sql` file, never launches SQL that differs from it, and
never renders parser-generated SQL
([engine research](wayfinder/query-optimization-advisor/tickets/0002-sql-analysis-engine-research.md)).
It is **static-only**: no `EXPLAIN`, `SHOW TABLE STATS`, or any Impala call
during composition
([metadata research](wayfinder/query-optimization-advisor/tickets/0003-metadata-availability-research.md)).
All advisor code lives in `dispatch/`; `scr/` is untouched (ADR-0005).

## Analysis engine

Locked by the
[engine research](wayfinder/query-optimization-advisor/assets/sql-analysis-engine-research.md):

- New runtime dependency: **SQLGlot 30.12.0** as the initial pin — the
  researched, deploy-verified release whose join-shape behavior the
  catalog's R09 detection is specified against — in `pyproject.toml` and
  `requirements.txt`. The edge-deploy-core offline bundle picks it up from
  `requirements.txt`; no other packaging work. Pin bumps re-run the syntax
  corpus.
- Parse with `read="hive"` behind an in-tree **Impala adapter** in a new
  `dispatch/advisor/` package (the data file stays at
  `dispatch/advisor_data.py` per its ticket) implementing the research's
  contract:
  scan the original SQL respecting strings/identifiers/comments; record
  bracket-form and comment-form join hints plus `STRAIGHT_JOIN` with source
  spans; replace only those ranges with equal-length whitespace in a parse
  copy; treat any parse error as **analysis unavailable** (no partial
  findings); reject structural analysis when a template token appears in
  executable SQL outside a string or comment.
- The original SQL remains the sole launch and preview input. Findings
  report locations only from adapter-recorded token spans or a tested
  token-to-AST mapping.

## Rule catalog

The whole catalog — severity semantics, shared definitions, eighteen rules
(R01–R18: 4 error / 6 warning / 8 info) with exact detection conditions,
per-Source applicability, not-a-rule and parked tables — is locked in
[the rule catalog](wayfinder/query-optimization-advisor/assets/rule-catalog.md)
and is normative as written. Summary for orientation only:

| Tier | Rules |
|---|---|
| error | R01 `select-star-unfiltered`, R04 `date-range-over-13-months`, R07 `dangerous-broadcast-hint`, R09 `cartesian-product` |
| warning | R02 `missing-partition-filter`, R03 `function-on-partition-column`, R06 `wasteful-join-hint`, R16 `destination-table-naming`, R17 `ddl-missing-drop`, R18 `ddl-location-outside-user-dir` |
| info | R05, R08, R10–R15 |

Per-Source
([catalog](wayfinder/query-optimization-advisor/assets/rule-catalog.md)):
`SqlFile` is analyzed as it sits on disk, pre-`table_wrapper`; `SqlTemplate`
is analyzed once on the template text; `ExistingTable` is not analyzed.

## Findings

Locked by the
[remediation guidance ticket](wayfinder/query-optimization-advisor/tickets/0004-advisory-vs-rewrite.md):
every Finding is a diagnostic detection line (factual, named to
table/block/span), a typed remediation line (imperative only for R02–R04,
R06–R07, R16–R18; alternative-naming otherwise), and its rule id +
guideline reference. Manual excerpts stay out of finding text.

Aggregation
([scoring ticket](wayfinder/query-optimization-advisor/tickets/0009-scoring-model.md)):
a **worst-severity badge** (`error`/`warning`/`info`/`clean`), pure display,
optionally accompanied by severity counts.

## Data file

Locked by the
[data file ticket](wayfinder/query-optimization-advisor/tickets/0008-join-strategy-data-file.md):
`dispatch/advisor_data.py`, plain Python literals — `MONITORED_SCHEMAS`
(`core`, `gco`, `mrs`), `DEFAULT_PARTITION_COLUMN = "dw_process_date"`,
`DATA_VERSION` (date string) plus the manual version transcribed from
(v2.0), and
per-table records keyed by exact lowercase `schema.table` (expanded verbatim
from Guideline #3; slash variants and multi-database rows become separate
entries) carrying `join_strategy` and optional `partition_columns`.
Revisions are ordinary reviewed PRs.

## TUI surface and interaction flow

Locked by the approved
[surface prototype](wayfinder/query-optimization-advisor/tickets/0006-tui-surface-prototype.md)
(assets linked from the ticket):

1. **New Job validation summary** — the badge with severity counts beside
   "Ready to launch", updating live as the form changes.
2. **Preview SQL screen** — a findings panel below the highlighted SQL,
   findings in the two-part shape, badge repeated in the action bar.
3. **Launch gate** — a modal listing only error findings with explicit
   proceed/cancel, stating the SQL launches exactly as written.

Analysis runs inline on form changes — static analysis of these files is
fast enough to need no worker or spinner. Severity is conveyed label-first,
never color alone; layouts hold at 80x24. The dedicated Analyze screen is
future-proofing for the deferred metadata effort, not v1.

## Enforcement

Locked by the
[enforcement policy ticket](wayfinder/query-optimization-advisor/tickets/0005-enforcement-policy.md):
**confirm is the ceiling.** Errors pause on the launch-gate modal; warnings
and info never gate; analysis-unavailable never gates. The per-launch
confirm is the only override; suppression comments and config opt-outs are
out of scope.

## Testing expectations

- **Pytest** (pure logic, no UI): an **Impala syntax corpus** of checked-in
  SQL fixtures covering every catalog rule firing and not firing — R01–R15
  plus DDL entries for R17/R18 (R16 is a form-field check needing no SQL
  corpus) — nested queries, CTEs, comments, strings, template tokens, both
  hint spellings, and analysis-unavailable inputs (bracket hints in
  unrecognized positions left unmasked, template tokens outside strings,
  unparseable SQL). Adapter tests assert masking is length-preserving and
  never leaks into launch/preview text.
- **Textual pilot tests**: badge in the New Job action bar per finding set;
  findings panel rendering in Preview; launch gate appearing only for
  errors, proceeding on confirm, cancelling on escape; no gating when
  analysis is unavailable.
- **Mocks**: no new `mocks/scenarios/` entries and no `impala-shell` mock
  routing — analysis is static
  ([metadata research](wayfinder/query-optimization-advisor/tickets/0003-metadata-availability-research.md)).
- **Edge-Node smoke items** (manual, reviewer checklist): advisor renders
  over SSH at 80x24; a Job with error findings launches after confirm; a
  clean Job launches without added friction; `NO_COLOR` output remains
  readable (labels carry severity).

## Glossary additions (`CONTEXT.md`)

Added to `CONTEXT.md` when this spec locks:

- **Advisor**: The pre-launch static analysis feature that checks a Job's
  SQL against the Impala optimization manual and reports **Findings**.
  Flag-only: it never modifies or gates what SQL is launched beyond the
  error-confirm modal. _Avoid_: linter, optimizer, rewriter.
- **Finding**: One Advisor detection — a rule id, guideline reference,
  severity (`error` / `warning` / `info`), diagnostic detection line, and
  typed remediation line. _Avoid_: violation, issue, error (reserved for
  the severity tier).

## Out of scope (fresh efforts if ever)

Query rewriting and auto-fix mechanics; live metadata checks (EXPLAIN,
SHOW TABLE STATS) behind an Analyze action; per-rule suppression and config
opt-outs; post-run PROFILE feedback; orchestrator-side or cluster-side
enforcement. See the map's Out of scope section for the reasoning links.
