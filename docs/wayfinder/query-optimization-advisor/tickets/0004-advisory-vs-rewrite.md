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

This is the map's central decision. It hangs on two feeders:

- The engine research says how trustworthy a rewrite can be (regex-mangled
  SQL that silently changes results is worse than no advisor).
- The rule catalog says how many rules even have a mechanical fix. Some do
  (insert a `[BROADCAST]` hint, swap `UNION` for `UNION ALL`); some don't
  (only the author knows which columns replace `SELECT *`, or the right
  `dw_process_date` range).

Grill the sponsor through the options:

1. **Flag-only** — findings listed with severity and manual excerpts;
   the user edits the `.sql` file themselves. Least risk, no consent problem.
2. **Flag + suggested rewrite, user confirms** — advisor shows a diff
   (original vs proposed SQL) for the auto-fixable subset; the user accepts
   per-finding or wholesale before launch. Dispatch never silently launches
   SQL that differs from the file on disk.
3. **Silent auto-rewrite** — advisor applies fixes and launches the result.

Also settle: if a rewrite is accepted, does Dispatch write it back to the
user's `.sql` file, launch a modified copy while leaving the file untouched,
or both (user choice)? A Job's SQL comes from a file the user owns in their
launch CWD, so mutating it has consequences outside Dispatch.

The answer locks one option (possibly "2 now, 3 never") and its consent and
file-mutation rules.
