# Query Optimization Advisor rule catalog

Locked with the sponsor on 2026-07-10 (grilling session, ticket
[Rule catalog](../tickets/0001-rule-catalog.md)). Rule ids were renumbered at
assembly; the grilling transcript's working numbers do not carry over.

## Severity semantics

Severity encodes confidence and impact together:

- **error** — high-confidence detection of a pattern the manual forbids
  outright, with severe cluster impact (or that the platform will reject
  anyway).
- **warning** — the pattern is probably a problem, but has legitimate
  exceptions the analyzer cannot see.
- **info** — stylistic or heuristic guidance where the author may well know
  better.

Enforcement (whether any tier blocks a launch) is the
[enforcement policy ticket](../tickets/0005-enforcement-policy.md)'s decision,
not this catalog's.

## Shared definitions

- **Monitored schemas** — a data-file list of schema names, initially `core`,
  `gco`, `mrs`, matched case-insensitively against the schema qualifier.
  Unqualified table references never match (they are usually the user's own
  temp tables).
- **Partition columns** — the data file maps `schema.table` to its partition
  column(s). A monitored-schema table without an entry defaults to
  `dw_process_date`: a missed check is invisible, while a false warning is
  visible and self-correcting (someone adds the entry).
- **Known table / recommendation** — an entry in the embedded join-strategy
  table (manual Guideline #3; file shape is the
  [join-strategy data file ticket](../tickets/0008-join-strategy-data-file.md)).
  "Shuffle-recommended" tables double as the catalog's "known-large" set.
- **Query block** — one SELECT scope in the AST. Predicates "reference" a
  table when they use its alias or columns within that block.
- **Hints** — the engine adapter records bracket-form (`[BROADCAST]`) and
  comment-form (`/* +BROADCAST */`) hints with source spans; a join hint binds
  to the table reference immediately following the `JOIN` keyword.

## Rules

| Id | Rule | Guideline | Severity |
|---|---|---|---|
| R01 | `select-star-unfiltered` | §3, G#10 | error |
| R02 | `missing-partition-filter` | G#1, §8 | warning |
| R03 | `function-on-partition-column` | §8 dates | warning |
| R04 | `date-range-over-13-months` | G#8 | error |
| R05 | `missing-join-hint` | G#3 | info |
| R06 | `wasteful-join-hint` | G#3 | warning |
| R07 | `dangerous-broadcast-hint` | G#3/#4 | error |
| R08 | `large-table-joined-directly` | G#9 | info |
| R09 | `cartesian-product` | §8 joins | error |
| R10 | `cast-in-join-condition` | §4 | info |
| R11 | `leading-wildcard-like` | §8 strings | info |
| R12 | `regexp-predicate` | §8 strings | info |
| R13 | `union-distinct` | §8 | info |
| R14 | `select-distinct` | §8 | info |
| R15 | `count-distinct-on-monitored-table` | §8 aggregates | info |

### R01 `select-star-unfiltered` (error)

Fires when a query block's projection is bare `*` (or `t.*` where `t` is a
monitored-schema table) **and** the block's `WHERE` contains no predicate
referencing that table. `JOIN ... ON` conditions do not count as filters.
`LIMIT` never suppresses the finding (the manual explicitly shows `LIMIT 10`
as bad). `SELECT *` over an already-filtered subquery or CTE does not fire —
that is the manual's own recommended pattern.

If the block has *any* predicate on the table (even non-partition), R01 stays
silent and R02 speaks to the partition-filter gap.

Reporting note: when R01 fires for a table/block, suppress R02 for the same
table/block — both conditions hold by definition and one finding per cause is
enough.

### R02 `missing-partition-filter` (warning)

Fires when a monitored-schema table appears in a query block and **no
recognized partition column of that table** (per the data file, with the
`dw_process_date` default) is referenced anywhere in the block's `WHERE`.
A template predicate like `BETWEEN '{date_inicio}' AND '{date_fim}'` counts
as present — the tokens sit inside string literals. Warning because the
filter may legitimately arrive indirectly (via a view or join the analyzer
cannot see through).

### R03 `function-on-partition-column` (warning)

Fires when a recognized partition column appears **only** wrapped in a
function or `CAST` in the block's `WHERE`. A function on the literal side
(`dw_process_date = some_fn(...)`) is fine; a bare predicate on the same
column elsewhere in the block silences the rule (pruning still works). R02
and R03 are disjoint: no reference at all → R02; wrapped-only → R03; bare
present → neither.

### R04 `date-range-over-13-months` (error)

Fires when a predicate on a recognized partition column has two literal
`YYYY-MM-DD` bounds — `BETWEEN 'a' AND 'b'`, or a `>=`/`<=` pair on the same
column in the same block — and the end date is later than the start date plus
13 calendar months. Non-literal or one-sided bounds produce no finding.
`SqlTemplate` Jobs naturally pass: each monthly expansion spans one month,
which *is* the manual's prescribed "break into sub parts".

### R05 `missing-join-hint` (info)

Fires when a known table is joined with no hint. Impala's optimizer usually
chooses correctly when stats exist; this is advice to follow the manual's
recommended list, not a defect.

### R06 `wasteful-join-hint` (warning)

Fires when a broadcast-recommended table is joined with a `SHUFFLE` hint.
Wasteful (needless network partitioning of a small table) but not dangerous.

### R07 `dangerous-broadcast-hint` (error)

Fires when a shuffle-recommended table (e.g. `core.cut_clear_dtl_enc`) is
joined with a `BROADCAST` hint. Broadcasting a multi-TB table replicates it
to every node — the most cluster-hostile mistake in the catalog. Confidence
is total: the hint is explicit and the table is explicitly listed.

### R08 `large-table-joined-directly` (info)

Fires when a shuffle-recommended table appears as a bare table reference in a
`JOIN` (not wrapped in a subquery/CTE). Worded as a "consider pre-filtering
in a subquery/CTE" nudge (G#9). Info because Impala's predicate pushdown and
runtime filters often make the direct join fine — the manual's own §4
Scenario 1 joins `CORE.auth_dtl_enc` directly.

### R09 `cartesian-product` (error)

Fires on a `CROSS JOIN` node — comma-style, explicit keyword, or `JOIN`
without `ON`/`USING` (the AST normalizes all three) — when the block's
`WHERE` contains no equality predicate linking columns from both sides.
Old-style `FROM a, b WHERE a.id = b.id` stays silent. Deliberate tiny cross
joins will occasionally be flagged; loud-but-ignorable is the right trade in
a flag-only advisor.

### R10 `cast-in-join-condition` (info)

Fires when an explicit `CAST` wraps a column reference inside a
`JOIN ... ON` equality. Worded "can block runtime-filter pushdown; align
source types where possible" — the manual's own auth examples do this when
types genuinely differ, hence info.

### R11 `leading-wildcard-like` (info)

Fires when a `LIKE` pattern literal starts with `%` or `_`. "Forces a full
scan; anchor the pattern or use `IN`."

### R12 `regexp-predicate` (info)

Fires on a `REGEXP`/`RLIKE` operator in any predicate. "`LIKE` may suffice."

### R13 `union-distinct` (info)

Fires on any `UNION` without `ALL`. "Adds deduplication overhead; use
`UNION ALL` if duplicates are acceptable." Whether duplicates matter is the
author's call — which is exactly why this is info.

### R14 `select-distinct` (info)

Fires on a `DISTINCT` projection. "The manual prefers `GROUP BY`."

### R15 `count-distinct-on-monitored-table` (info)

Fires when `COUNT(DISTINCT ...)` appears in a block referencing a
monitored-schema table. "Use two-step aggregation on large tables." Scoped to
monitored schemas to avoid nagging about small temp tables.

## Per-Source applicability

- **`ExistingTable`** — no SELECT exists; the advisor does not run. (Any UI
  treatment is the surface prototype's decision.)
- **`SqlTemplate`** — analyze the template text **once**, pre-render: the
  tokens sit inside string literals, so the AST is identical across monthly
  expansions. R04 auto-passes (one month per expansion). A token outside a
  string literal makes analysis unavailable per the engine research's adapter
  contract.
- **`SqlFile`** — analyze the user's SQL as it sits on disk, **before**
  `table_wrapper` wraps it (the wrapper is generated and satisfied by
  construction). Self-contained DDL files are analyzed as written, per
  statement for multi-statement files.

## Not a rule

| Guideline | Reason |
|---|---|
| G#2 employee-ID `LOCATION`, G#5 table naming, G#6 `DROP TABLE IF EXISTS` | Satisfied by construction — `dispatch/sql.py: table_wrapper` generates all three for every Table destination |
| G#7 quarterly file cleanup; G#11–#15 ports/kernels/processes/environment | Out of scope on the map — not properties of the Job's SQL |
| G#9 as a shape requirement | Softened to R08 (info); its enforceable core is R02 + R06/R07, and a hard subquery-shape rule would contradict §4's runtime-filter guidance |
| GROUP BY cardinality ordering | Needs row counts (metadata) |
| Data-type narrowing (TINYINT/SMALLINT) | Cannot judge intent statically |
| CASE ordering by frequency | Needs data distribution |
| Join order smallest-first | Impala reorders joins unless `STRAIGHT_JOIN` is present |
| NULL-handling patterns | `COALESCE` misuse too niche; `IS NOT NULL` advice too noisy |
| Repeated CASE / same-partition window functions | The manual's own example is common, legitimate SQL |
| Split-path vs CASE restructuring | Architectural advice, not a checkable predicate |

## Parked: needs-metadata (out of v1)

Per the
[metadata availability research](metadata-availability-research.md):
G#4 custom-table size check (`SHOW TABLE STATS`), EXPLAIN-based
partition-pruning verification, and stats freshness. A future metadata effort
behind an explicit Analyze action may revisit them.

## Data file requirements (feeds ticket 0008)

The embedded data file must carry, per entry: `schema.table`, recommended
join strategy (broadcast/shuffle), and partition column(s). Plus the
monitored-schema list. Consumed by R01–R08 and R15.
