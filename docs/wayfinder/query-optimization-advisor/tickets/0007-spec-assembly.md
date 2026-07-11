---
title: "Assemble and lock the Query Optimization Advisor spec"
labels: [wayfinder:task]
status: closed
assignee: cursor-agent
blocked-by:
  [
    0001-rule-catalog,
    0002-sql-analysis-engine-research,
    0003-metadata-availability-research,
    0004-advisory-vs-rewrite,
    0005-enforcement-policy,
    0006-tui-surface-prototype,
    0008-join-strategy-data-file,
    0009-scoring-model,
  ]
---

## Question

Fold every decision on this map into one implementation-ready spec document
(proposed home: `docs/query-optimization-advisor-spec.md`), plus the ADR for
the analysis engine dependency and Impala adapter boundary. This is the map's
destination.

The spec must cover, with nothing left open:

- the rule catalog (ids, detection conditions, severities, and manual
  remediation guidance)
- the analysis engine and any new dependency, with its vendored-wheel story
- flag-only behavior and the invariant that source and launched SQL remain
  unchanged
- launch enforcement policy and override paths
- the TUI surface and interaction flow, referencing the accepted prototype
- scoring/aggregation model (ticket 0009), SqlTemplate/ExistingTable handling
  (locked in the rule catalog), config and suppression (still fog; graduates
  before this ticket unblocks)
- testing expectations: pytest coverage for the analyzer and its syntax
  corpus, plus Edge-Node smoke items reviewers must check manually — no new
  `mocks/scenarios/` entries per the
  [metadata availability research](0003-metadata-availability-research.md)
- new `CONTEXT.md` glossary entries (Advisor, Finding, and whatever else the
  effort coined)

Resolved when the sponsor signs off on the document and it is merged. Any
disagreement discovered during assembly reopens the relevant ticket rather
than being settled ad hoc here.

## Resolution

The spec was assembled at
[docs/query-optimization-advisor-spec.md](../../../query-optimization-advisor-spec.md)
with
[ADR-0006](../../../adr/0006-sqlglot-for-advisor-analysis.md) recording the
analysis-engine choice, audited against every ticket resolution, and
**signed off by the sponsor on 2026-07-11**. The `CONTEXT.md` glossary
gained the **Advisor** and **Finding** entries. Merging the stacked PR
chain (#30 through #40) is the Maintainer's step per `CONTRIBUTING.md`;
implementation starts from the merged spec.
