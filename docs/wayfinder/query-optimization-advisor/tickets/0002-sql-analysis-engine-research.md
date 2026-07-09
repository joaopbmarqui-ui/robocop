---
title: "Research: SQL analysis engine options under the air-gapped deploy path"
labels: [wayfinder:research]
status: open
assignee: none
blocked-by: []
---

## Question

What can the advisor use to understand a Job's SQL, given that Dispatch
deploys to an air-gapped Edge Node via vendored wheels (see
`docs/edge-node-first-time-setup.md`, edge-deploy-core bundles) with
Python >= 3.10 and currently a single runtime dependency (`textual`)?

Evaluate at least:

1. **A real SQL parser as a new dependency** — `sqlglot` (has an Impala/Hive
   dialect story?), `sqlparse`, others. For each: pure-Python? wheel
   availability for the edge node? dialect fidelity for Impala specifics the
   manual relies on (`[BROADCAST]`/`[SHUFFLE]` hints, `STRAIGHT_JOIN`,
   backtick identifiers, `{date_inicio}` template tokens present pre-render)?
   licence?
2. **Regex/heuristic analysis in-tree** — the approach `dispatch/sql.py`
   already takes (`detect_source`, `is_self_contained_ddl`). Which rules from
   the catalog survive with acceptable false-positive rates on regex alone?
3. **A hybrid** — lightweight tokenizer in-tree, no new dependency.

Decisive because it caps the whole effort: **reliable auto-rewrite almost
certainly requires a real parser**; if no parser survives the deploy path,
the sponsor's fallback (rating/flagging) becomes the ceiling.

Deliverable: a markdown comparison linked from this ticket, ending in a
recommendation (which engine, and the confidence level it supports:
flag-only vs flag+rewrite).
