---
title: "Decide: auto-rewrite the query, or rate/flag only"
labels: [wayfinder:grilling]
status: open
assignee: none
blocked-by: [0001-rule-catalog, 0002-sql-analysis-engine-research]
---

## Question

The sponsor's ideal is that the advisor **automatically updates the query**;
the acceptable fallback is a **rating or flagging system**. Which does v1
ship — and if rewrite, under what consent model?

The engine research now caps v1 at flag-only: no evaluated parser faithfully
round-trips the Impala syntax in the manual, and parser-generated SQL must
never become the launch input. This ticket asks the sponsor to confirm that
boundary and decide whether narrow, source-range suggested edits remain a
future goal or leave this map entirely.

This is the map's central decision. It hangs on two feeders:

- The engine research supports AST-backed findings but rules out full-query
  serialization and silent rewrite.
- The rule catalog says whether any finding has a semantics-independent,
  source-range edit. Replacing `UNION` with `UNION ALL`, choosing columns for
  `SELECT *`, and choosing a `dw_process_date` range all require author intent.

Grill the sponsor through the options:

1. **Flag-only v1** — findings listed with severity and manual excerpts;
   the user edits the `.sql` file themselves. Least risk, no consent problem.
2. **Flag-only v1, preserve a future suggested-edit path** — a later effort
   may evaluate narrow source-range edits for rules the catalog proves
   semantics-independent. Each edit requires a visible diff and explicit user
   confirmation.
3. **Parser-generated or silent auto-rewrite** — ruled out by the engine
   research; retain only as a recorded non-option.

For v1, Dispatch never mutates the user's `.sql` file and never launches SQL
that differs from it. If the sponsor preserves option 2 as a future goal,
settle whether an accepted edit would write back to that file or create a
separate copy; do not leave the ownership rule implicit.

The answer locks option 1 or 2, permanently rejects option 3, and records the
corresponding future-scope and file-ownership rules.
