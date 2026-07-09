# SQL analysis engine research

Research date: 2026-07-09

## Decision

Use **SQLGlot behind a small in-tree Impala compatibility adapter** for the
advisor's static analysis. Parse with SQLGlot's Hive dialect after replacing
recognized Impala-only tokens with equal-length whitespace in a parse copy.
Keep the original SQL immutable and use the copy only to build the AST. Equal
lengths keep lexical coordinates aligned; they do not make source spans
available on every SQLGlot AST node.

The v1 confidence ceiling is **flag-only**. Do not serialize SQLGlot's AST and
do not launch or write back parser-generated SQL. The parser does not have a
native Impala dialect, fails on syntax used throughout the optimization manual,
and moves a supported comment-form join hint to a different syntactic position
when rendering. Those are disqualifying properties for query rewriting.

This recommendation is compatible with the air-gapped Edge Node: SQLGlot
30.12.0 is a pure-Python, dependency-free `py3-none-any` wheel, supports
Python 3.9+, and is MIT licensed. A platform-targeted Python 3.10 download with
Dispatch's documented `manylinux2014_x86_64` flags succeeded.

## Requirements tested

The comparison prioritizes:

1. Python 3.10 compatibility and an offline-installable Edge Node wheel.
2. Structural access to query blocks, tables, joins, predicates, functions,
   projections, and set operations.
3. Preservation or explicit handling of the manual's Impala syntax:
   `[BROADCAST]`, `[SHUFFLE]`, `STRAIGHT_JOIN`, backtick identifiers, and
   quoted or unquoted `{date_inicio}` / `{date_fim}` tokens.
4. Safe failure. An unsupported query must produce no structural findings
   rather than partial or misleading analysis.
5. Rewrite fidelity. A parser used to rewrite must preserve all syntax and
   semantics after a parse/render round trip.

The probe used current releases and representative SQL copied or reduced from
the manual. It also tested a query combining `DISTINCT`, a comma join, a
`CAST` join predicate, `UNION`, and a leading-wildcard `LIKE`.

## Comparison

| Option | Deployment | Impala fidelity observed | Analysis capability | Rewrite confidence | Result |
|---|---|---|---|---|---|
| SQLGlot 30.12.0, Hive dialect | 708 KB universal wheel; no runtime dependencies; Python >=3.9; MIT | Parses normal joins, backticks, quoted template tokens, and common rule shapes. Misparses unquoted template tokens as named structs. Fails on bracket hints and `STRAIGHT_JOIN`. Parses comment hints but renders them before `JOIN`, not immediately after it. | Semantic AST with query scopes, tables, joins, expressions, and set operations | Unsafe for full-query rendering | **Choose with adapter, flag-only** |
| sqlparse 0.5.5 | 46 KB universal wheel; no runtime dependencies; Python >=3.8; BSD-3-Clause | Tokenizes every probe, including the Impala-only tokens | Non-validating token groups, not a dialect-aware semantic AST; scope and lineage logic would be ours to build | No semantic basis for rewrite | Reject as primary engine |
| SQLFluff 4.2.2, Impala dialect | Pure-Python 1.0 MB universal main wheel, but its transitive closure includes platform-specific compiled wheels; Python >=3.10; MIT | Explicit Impala dialect inherits Hive, but still fails bracket hints and `STRAIGHT_JOIN`; other probes parse | Rich concrete syntax tree and lint framework, but a larger dependency surface and a less stable Python API | Same syntax gaps; formatter is not an advisor rewrite engine | Reject |
| Existing regex heuristics | No dependency | Can search the raw spelling of every construct | Cannot reliably exclude comments/strings or associate predicates and hints with the correct query block/table | Unsafe | Retain only for trivial preflight checks |
| New in-tree tokenizer/parser | No dependency | Could recognize exactly the local syntax corpus | A tokenizer can protect comments, strings, and source spans, but query scopes and expression semantics would recreate a SQL parser | Unsafe until a substantial parser exists | Use only as a narrow adapter |

SQLFluff's main wheel and platform-specific dependencies were available under
the Edge Node download flags, so deployment is not the reason to reject it. It
is rejected because its larger dependency and API surface buy no fidelity on
the syntax that distinguishes this workload.

## Probe results

| Construct | SQLGlot `hive` | SQLGlot after equal-length masking | sqlparse | SQLFluff `impala` |
|---|---|---|---|---|
| Basic Impala-like `SELECT` | Pass | Pass | Tokenized | Pass |
| Backtick identifiers | Pass and preserved | Pass | Tokenized | Pass |
| Quoted template tokens | Pass and preserved | Pass | String tokens | Pass |
| Unquoted template tokens | Silently become `STRUCT(...)` expressions | Same; adapter must reject before parse | Punctuation/name tokens | Parse violation |
| `JOIN [BROADCAST] table` | Parse error | Pass; both tables found | `[BROADCAST]` is a name token | Parse violation |
| `JOIN [SHUFFLE] table` | Parse error | Pass; both tables found | `[SHUFFLE]` is a name token | Parse violation |
| `SELECT STRAIGHT_JOIN ...` | Parse error | Pass; join AST found | Keyword token | Parse violation |
| `JOIN /* +BROADCAST */ table` | Parses, but render moves comment before `JOIN` | Same | Comment token | Pass |
| Combined candidate-rule shapes | Pass; comma join becomes an explicit `CROSS JOIN` in the AST | Pass | Tokenized | Pass |

The equal-length masking experiment replaced only `[BROADCAST]`, `[SHUFFLE]`,
and `STRAIGHT_JOIN` in a copy. SQLGlot then parsed those probe cases and
recovered the expected joined tables. Equal lengths preserve lexical offsets,
but this experiment is evidence for analysis only: the masked SQL must never
be rendered or executed.

Dispatch currently recognizes template tokens by textual presence, so an
unquoted token is accepted as a `SqlTemplate`. SQLGlot does not reject that
form: it silently interprets `{date_inicio}` as `STRUCT(date_inicio)`. The
adapter must classify placeholders before parsing. Tokens inside strings or
comments are safe for static parsing; a token in executable SQL outside a
string or comment makes structural analysis unavailable.

The official Impala documentation confirms that square-bracket hints are
deprecated but still supported for backward compatibility. Dispatch cannot
ignore them because the supplied optimization manual uses that spelling
throughout. The current comment syntax also requires join hints immediately
after `JOIN`, which is why SQLGlot's rendered placement is not equivalent.

## Rule coverage implications

The final rule catalog is not locked yet. Against its current candidates, the
engine boundary is:

### Raw regex ceiling

No candidate catalog rule is reliable enough for warning or error severity
when matched against raw SQL with regex alone. Comments and unrelated string
literals can contain every relevant keyword, and regex cannot associate a
filter, hint, or join condition with the correct table and query block.

After a tokenizer classifies comments, strings, and executable tokens, lexical
checks can safely locate `SELECT DISTINCT`, `COUNT(DISTINCT ...)`, `REGEXP`,
`UNION` without `ALL`, and the spelling of join hints. It can also inspect the
string-literal operand of a `LIKE` token for a leading wildcard. That is the
hybrid option, not regex-only analysis, and these findings still cannot claim
that a semantically different replacement is safe.

### Suitable for SQLGlot AST checks

- `SELECT *` associated with a `core.*` table and the relevant query block.
- Presence of `dw_process_date` predicates and functions applied to that
  column.
- Literal date-range comparison when both bounds are statically known.
- `DISTINCT`, `UNION` versus `UNION ALL`, `COUNT(DISTINCT ...)`, `REGEXP`,
  and leading-wildcard `LIKE`.
- Explicit comma/cross joins and joins without an `ON`/`USING` predicate.
- `CAST` within a join predicate.
- Known-table join strategy after the adapter records each masked hint and
  associates its source span with the following table reference.

### Not reliable from regex alone

- Whether a filter belongs to the same query block as a particular table.
- Whether a large table is filtered before a join through a CTE or subquery.
- Whether a `UNION` can safely become `UNION ALL`, `DISTINCT` can become
  `GROUP BY`, or a `REGEXP` is semantically equivalent to a `LIKE`.
- Whether an absent textual join condition is supplied indirectly by a
  correlated or transformed expression.

The latter semantic claims should either be informational wording ("review
whether...") or excluded by the rule catalog. A parser cannot infer business
intent.

## Required adapter contract

The implementation spec should require an adapter with these properties:

- Scan the original SQL while respecting quoted strings, quoted identifiers,
  and comments.
- Recognize hints only in their documented syntactic positions, and record
  bracket-form and comment-form hints plus `STRAIGHT_JOIN` with their original
  source ranges.
- Reject structural analysis when a template token occurs in executable SQL
  outside a string or comment; never accept SQLGlot's named-struct
  interpretation.
- Replace only those ranges with equal-length whitespace in a parse copy.
- Parse the copy with `read="hive"` and treat any parser error as analysis
  unavailable; do not run AST rules against a partial tree.
- Report a source location only when it comes from an adapter-recorded token
  span or a separately tested token-to-AST mapping. SQLGlot AST nodes do not
  consistently expose source spans.
- Preserve the original SQL as the sole launch and preview input.
- Pin SQLGlot in both `pyproject.toml` and `requirements.txt`, and include its
  universal wheel in the edge-deploy-core offline bundle.
- Maintain a checked-in Impala syntax corpus covering every accepted rule,
  nested queries, CTEs, comments, strings, template tokens, and both hint
  spellings before enabling the advisor.

## Why not rewrite

AST quality is sufficient to locate suspicious structures, not to prove that a
replacement preserves results. Several candidate "fixes" require author
intent, and the parser's round trip is already non-faithful for a join hint.
Source-range edits could eventually support a very small reviewed subset, but
that is a separate capability requiring its own corpus and equivalence checks.
It must not be inferred from choosing SQLGlot for findings.

For the downstream remediation-guidance decision, this research therefore
locks **flag-only for v1** and rules out silent auto-rewrite.

## Sources

- [SQLGlot 30.12.0 on PyPI](https://pypi.org/project/sqlglot/30.12.0/)
- [SQLGlot supported dialects](https://sqlglot.com/sqlglot.html#supported-dialects)
- [SQLGlot issue: Impala is not on the core roadmap](https://github.com/tobymao/sqlglot/issues/4726)
- [Apache Superset's Impala-to-Hive mapping](https://github.com/apache/superset/pull/34662)
- [sqlparse 0.5.5 on PyPI](https://pypi.org/project/sqlparse/0.5.5/)
- [SQLFluff 4.2.2 on PyPI](https://pypi.org/project/sqlfluff/4.2.2/)
- [SQLFluff dialect reference](https://docs.sqlfluff.com/en/stable/reference/dialects.html#apache-impala)
- [Apache Impala optimizer hints](https://impala.apache.org/docs/build/html/topics/impala_hints.html)
- [Dispatch Edge Node bootstrap wheel recipe](../../../edge-node-first-time-setup.md)
- [Dispatch release workflow](../../../release-workflow.md)
