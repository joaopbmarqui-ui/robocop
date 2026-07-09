---
title: "Decide: can findings block a launch, or only inform"
labels: [wayfinder:grilling]
status: open
assignee: none
blocked-by: [0001-rule-catalog]
---

## Question

Dispatch already **hard-refuses** launches for illegal Source/Destination
combinations, missing Kerberos tickets, and a third simultaneous Running Job
(product invariant in `.agents/skills/dispatch-textual-tui/SKILL.md`). Do any
advisor findings join that list, or is the advisor purely informative?

Grill through the severity tiers the rule catalog produces:

- Are there guidelines so unconditionally bad (e.g. unfiltered `SELECT *`
  from `core.cut_clear_dtl_enc`, a >13-month date range that Impala will
  reject anyway) that launch should be refused or require an explicit
  override keystroke?
- False-positive tolerance: a static analyzer will sometimes be wrong.
  Blocking on a wrong finding strands a legitimate Job on a production edge
  node — what override path exists (per-launch "launch anyway", per-rule
  suppression comment in the SQL, config opt-out)?
- Does the answer differ by Source? `SqlTemplate` and `ExistingTable` Jobs
  have different exposure (an `ExistingTable -> Csv` Job has no SELECT to
  analyze at all).

The answer is a policy table: severity tier -> launch behavior (block /
confirm / warn / info) plus the override mechanism.
