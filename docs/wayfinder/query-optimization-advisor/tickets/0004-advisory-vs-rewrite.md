---
title: "Decide: remediation guidance for flag-only findings"
labels: [wayfinder:grilling]
status: open
assignee: none
blocked-by: [0001-rule-catalog, 0002-sql-analysis-engine-research]
---

## Question

The
[engine research](../assets/sql-analysis-engine-research.md) makes v1
flag-only: Dispatch never mutates the user's `.sql` file, never launches SQL
that differs from it, and never renders parser-generated SQL. Query rewriting
and auto-fix mechanics have moved out of this map.

How much remediation guidance should each Finding provide while the user edits
the file themselves?

Grill the sponsor through:

1. **Finding + manual excerpt** — identify the rule, severity, evidence, and
   relevant guideline, but leave the correction entirely to the author.
2. **Finding + textual remediation steps** — add deterministic prose such as
   "filter this query block on `dw_process_date`" or "review the join strategy
   for `core.product_hierarchy`". This is guidance, not generated SQL or a
   diff.
3. **Rule-specific mix** — include steps only when the rule catalog can state
   them without guessing business intent; explanation-only for `SELECT *`,
   date bounds, `UNION` semantics, and similar author decisions.

Also settle whether the UI should use imperative wording ("Add...") or
diagnostic wording ("No ... was found"), given that static analysis can be
wrong.

The answer is a rule-level remediation-content policy and a wording standard.
The file-ownership rule is already locked: v1 is read-only with respect to Job
SQL.
