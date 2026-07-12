# SQLGlot behind an Impala adapter for advisor analysis

The Query Optimization Advisor
([spec](../query-optimization-advisor-spec.md)) needs to understand a Job's
SQL statically, on an air-gapped Edge Node, well enough to run the locked
rule catalog. This ADR records the analysis-engine choice and its
boundaries. Full evaluation:
[SQL analysis engine research](../wayfinder/query-optimization-advisor/assets/sql-analysis-engine-research.md).

## Decision

Add **SQLGlot** (pinned, pure-Python universal wheel, MIT, zero transitive
dependencies) as Dispatch's second runtime dependency, and parse with its
Hive dialect behind a small in-tree **Impala adapter**:

- The adapter scans the original SQL (respecting strings, quoted
  identifiers, and comments), records Impala-only constructs — bracket-form
  and comment-form join hints, `STRAIGHT_JOIN` — with their source spans,
  and replaces only those ranges with equal-length whitespace in a **parse
  copy**. Equal lengths keep lexical coordinates aligned.
- Any parse error means **analysis unavailable**: no findings from a
  partial tree, and never any effect on launching.
- The AST is used for analysis only. **Never serialize it**: SQLGlot has no
  native Impala dialect, rejects the manual's hint syntax unmasked,
  misparses unquoted template tokens as named structs, and relocates
  comment-form hints when rendering. The original SQL on disk remains the
  sole launch and preview input.

## Considered alternatives

- **sqlparse** — non-validating token groups, not a dialect-aware AST;
  every scope/lineage judgment the catalog needs would be built by hand.
- **SQLFluff (Impala dialect)** — advertises Impala but fails the same hint
  syntax; much larger dependency and less stable Python API for no fidelity
  gain.
- **Regex/heuristics in-tree** — cannot exclude comments/strings or
  associate predicates with query blocks at acceptable false-positive
  rates for warning/error severities.
- **New in-tree parser** — recreates a SQL parser to reach the same AST
  quality; the adapter keeps in-tree code to a narrow, testable seam.

## Consequences

- `requirements.txt` gains a second pinned package; the edge-deploy-core
  offline bundle path covers it with no extra packaging work
  (verified: platform-targeted `manylinux2014_x86_64` / cp310 download
  succeeds).
- A checked-in Impala syntax corpus must cover every catalog rule and both
  hint spellings before the advisor is enabled (spec, Testing
  expectations).
- Query rewriting stays out of scope regardless of parser quality; any
  future source-editing capability is a fresh effort with its own
  equivalence proofs.
