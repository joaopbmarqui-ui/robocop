"""Catalog rules R01–R18 evaluated against the adapted SQLGlot AST."""

from __future__ import annotations

import re
from datetime import date, datetime

from sqlglot import exp

from dispatch import advisor_data

from .adapter import AdapterResult, HintRecord
from .models import Finding

_DATE_LITERAL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MAX_MONTHS = 13

RULE_META: dict[str, tuple[str, str, str]] = {
    # rule_id: (rule_name, guideline, severity)
    "R01": ("select-star-unfiltered", "§3, G#10", "error"),
    "R02": ("missing-partition-filter", "G#1, §8", "warning"),
    "R03": ("function-on-partition-column", "§8 dates", "warning"),
    "R04": ("date-range-over-13-months", "G#8", "error"),
    "R05": ("missing-join-hint", "G#3", "info"),
    "R06": ("wasteful-join-hint", "G#3", "warning"),
    "R07": ("dangerous-broadcast-hint", "G#3/#4", "error"),
    "R08": ("large-table-joined-directly", "G#9", "info"),
    "R09": ("cartesian-product", "§8 joins", "error"),
    "R10": ("cast-in-join-condition", "§4", "info"),
    "R11": ("leading-wildcard-like", "§8 strings", "info"),
    "R12": ("regexp-predicate", "§8 strings", "info"),
    "R13": ("union-distinct", "§8", "info"),
    "R14": ("select-distinct", "§8", "info"),
    "R15": ("count-distinct-on-monitored-table", "§8 aggregates", "info"),
    "R16": ("destination-table-naming", "G#5", "warning"),
    "R17": ("ddl-missing-drop", "G#6", "warning"),
    "R18": ("ddl-location-outside-user-dir", "G#2", "warning"),
}


def run_sql_rules(adapted: AdapterResult) -> list[Finding]:
    """Evaluate AST rules R01–R15 against a successful adapter result."""
    assert adapted.available
    findings: list[Finding] = []
    for expression in adapted.expressions:
        findings.extend(_rules_for_expression(expression, adapted.hints))
    return _dedupe(findings)


def run_form_rules(
    *,
    source_type: str,
    destination_type: str,
    destination_table: str,
    user_id: str,
) -> list[Finding]:
    """R16 — destination table naming (form field, not SQL text)."""
    if source_type == "ExistingTable":
        return []
    if destination_type not in ("Table", "Table+Csv"):
        return []
    if not destination_table or not user_id:
        return []
    prefix = f"{user_id}_"
    if destination_table.startswith(prefix):
        return []
    return [
        _finding(
            "R16",
            f"Destination table name {destination_table!r} does not start with {prefix!r}",
            f"Rename the destination table to start with {prefix}.",
        )
    ]


def run_ddl_rules(
    adapted: AdapterResult,
    *,
    user_id: str,
    self_contained_ddl: bool,
) -> list[Finding]:
    """R17/R18 — self-contained DDL SqlFile Jobs only."""
    if not self_contained_ddl or not adapted.available:
        return []
    findings: list[Finding] = []
    dropped: set[str] = set()
    for expression in adapted.expressions:
        if isinstance(expression, exp.Drop) and expression.args.get("kind") == "TABLE":
            key = _table_key_from_node(expression.this)
            if key:
                dropped.add(key)
            continue
        if not isinstance(expression, exp.Create):
            continue
        if expression.args.get("kind") != "TABLE":
            continue
        key = _table_key_from_node(expression.this)
        table_label = key or _node_sql(expression.this) or "table"
        if key and key not in dropped:
            findings.append(
                _finding(
                    "R17",
                    f"CREATE TABLE for {table_label} has no preceding DROP TABLE IF EXISTS",
                    f"Add DROP TABLE IF EXISTS {table_label} before the CREATE.",
                )
            )
        location = _create_location(expression)
        if location is None:
            findings.append(
                _finding(
                    "R18",
                    f"CREATE TABLE for {table_label} has no LOCATION clause",
                    f"Add a LOCATION under the launching user's directory (segment {user_id!r}).",
                )
            )
        elif user_id and f"/{user_id}/" not in f"/{location.strip('/')}/":
            findings.append(
                _finding(
                    "R18",
                    f"LOCATION {location!r} for {table_label} does not contain user id {user_id!r} as a path segment",
                    f"Point LOCATION at a path under the launching user's directory (segment {user_id!r}).",
                )
            )
        if key:
            # A later CREATE for the same name still needs its own preceding DROP;
            # do not treat this CREATE as satisfying DROP for subsequent twins.
            pass
    return findings


def _rules_for_expression(
    expression: exp.Expression, hints: tuple[HintRecord, ...]
) -> list[Finding]:
    findings: list[Finding] = []
    # Walk every SELECT query block (including CTEs and subqueries).
    for select in _select_blocks(expression):
        findings.extend(_rules_for_select(select, hints))
    # UNION DISTINCT can sit above SELECT nodes.
    for union in expression.find_all(exp.Union):
        if union.args.get("distinct") is True:
            findings.append(
                _finding(
                    "R13",
                    "UNION without ALL found",
                    "UNION ALL avoids the deduplication overhead if duplicates are acceptable.",
                )
            )
    return findings


def _rules_for_select(select: exp.Select, hints: tuple[HintRecord, ...]) -> list[Finding]:
    findings: list[Finding] = []
    tables = _direct_tables(select)
    where = select.args.get("where")
    where_sql_cols = _columns_in(where) if where else set()

    r01_keys: set[str] = set()
    # R01 / R02 / R03 / R04 / R15 per monitored table in this block.
    for table in tables:
        schema = (table.db or "").lower()
        name = table.name.lower()
        if not schema or not advisor_data.is_monitored_schema(schema):
            continue
        key = advisor_data.table_key(schema, name)
        refs_table = _where_references_table(where, table, where_sql_cols)

        # R01: bare * (or t.*) with no WHERE predicate on the monitored table.
        if _projects_star_for(select, table) and not refs_table:
            findings.append(
                _finding(
                    "R01",
                    f"SELECT * over monitored table {key} with no WHERE predicate on that table",
                    "Project needed columns, or filter the monitored table "
                    "(for example via a filtered subquery/CTE) before selecting *.",
                )
            )
            r01_keys.add(key)

        part_cols = {c.lower() for c in advisor_data.partition_columns_for(schema, name)}
        part_refs = _partition_refs_in_where(where, table, part_cols)

        # R02: no recognized partition column referenced in WHERE.
        # Suppressed when R01 already fired for this table/block.
        if key not in r01_keys and part_cols and not part_refs["any"]:
            findings.append(
                _finding(
                    "R02",
                    f"No {next(iter(part_cols))} predicate found for {key} in this query block",
                    f"Add a {next(iter(part_cols))} filter to this query block.",
                )
            )
        # R03: partition column appears only wrapped in a function/CAST.
        elif key not in r01_keys and part_refs["wrapped_only"]:
            col = next(iter(part_refs["wrapped_only"]))
            findings.append(
                _finding(
                    "R03",
                    f"Partition column {col} for {key} appears only inside a function or CAST in WHERE",
                    f"Compare {col} directly (put functions on the literal side) so "
                    "partition pruning can apply.",
                )
            )

        # R04: literal date range on a partition column exceeding 13 months.
        for detection in _wide_date_ranges(where, table, part_cols, key):
            findings.append(detection)

        # R15: COUNT(DISTINCT ...) in a block referencing a monitored table.
        if _has_count_distinct(select):
            findings.append(
                _finding(
                    "R15",
                    f"COUNT(DISTINCT ...) found in a query block referencing monitored table {key}",
                    "Use two-step aggregation on large tables.",
                )
            )

    # R05–R08 join-strategy rules.
    findings.extend(_join_strategy_findings(select, hints))

    # R09 cartesian product.
    findings.extend(_cartesian_findings(select))

    # R10 CAST in join ON equality.
    for join in select.args.get("joins") or []:
        on = join.args.get("on")
        if on is None:
            continue
        for eq in on.find_all(exp.EQ):
            if _cast_wraps_column(eq.this) or _cast_wraps_column(eq.expression):
                findings.append(
                    _finding(
                        "R10",
                        "CAST wraps a column reference inside a JOIN ... ON equality",
                        "CAST can block runtime-filter pushdown; align source types where possible.",
                    )
                )
                break

    # R11 leading-wildcard LIKE.
    for like in select.find_all(exp.Like):
        # Only predicates owned by this select (not nested subqueries).
        if not _owned_by_select(like, select):
            continue
        pattern = like.expression
        if isinstance(pattern, exp.Literal) and pattern.is_string:
            text = pattern.this
            if text.startswith("%") or text.startswith("_"):
                findings.append(
                    _finding(
                        "R11",
                        f"LIKE pattern {text!r} starts with a leading wildcard",
                        "Forces a full scan; anchor the pattern or use IN.",
                    )
                )

    # R12 REGEXP / RLIKE (Hive dialect lowers both to RegexpLike).
    for regexp in select.find_all(exp.RegexpLike):
        if _owned_by_select(regexp, select):
            findings.append(
                _finding(
                    "R12",
                    "REGEXP/RLIKE operator found in a predicate",
                    "LIKE may suffice and avoids the regex engine.",
                )
            )

    # R14 SELECT DISTINCT.
    if select.args.get("distinct"):
        findings.append(
            _finding(
                "R14",
                "DISTINCT projection found",
                "The manual prefers GROUP BY.",
            )
        )

    return findings


def _join_strategy_findings(select: exp.Select, hints: tuple[HintRecord, ...]) -> list[Finding]:
    findings: list[Finding] = []
    joins = list(select.args.get("joins") or [])
    if not joins:
        return findings

    from_tables = [t for t in [_from_table(select)] if t is not None]
    joined_tables = [t for t in (_join_table(j) for j in joins) if t is not None]

    def hint_for(table: exp.Table) -> HintRecord | None:
        schema = (table.db or "").lower()
        name = table.name.lower()
        key = advisor_data.table_key(schema, name) if schema else name
        for hint in hints:
            if hint.kind not in ("BROADCAST", "SHUFFLE") or not hint.table_sql:
                continue
            hint_key = hint.table_sql.lower()
            if hint_key == key or hint_key == name:
                return hint
            if "." not in hint_key and hint_key == name:
                return hint
        return None

    # R05–R07: hints bind to the table immediately after JOIN, so only join sides.
    for table in joined_tables:
        schema = (table.db or "").lower()
        name = table.name.lower()
        if not schema:
            continue
        strategy = advisor_data.join_strategy_for(schema, name)
        if strategy is None:
            continue
        key = advisor_data.table_key(schema, name)
        hint = hint_for(table)
        if hint is None:
            findings.append(
                _finding(
                    "R05",
                    f"Known table {key} is joined with no join hint",
                    f"Consider [{strategy.upper()}] per the recommended join-strategy list "
                    f"({advisor_data.DATA_VERSION}).",
                )
            )
        elif strategy == "broadcast" and hint.kind == "SHUFFLE":
            findings.append(
                _finding(
                    "R06",
                    f"[SHUFFLE] hint found on broadcast-recommended {key}",
                    f"Use [BROADCAST] per the recommended join-strategy list "
                    f"({advisor_data.DATA_VERSION}).",
                )
            )
        elif strategy == "shuffle" and hint.kind == "BROADCAST":
            findings.append(
                _finding(
                    "R07",
                    f"[BROADCAST] hint found on shuffle-recommended {key}",
                    f"Use [SHUFFLE] per the recommended join-strategy list "
                    f"({advisor_data.DATA_VERSION}).",
                )
            )

    # R08: shuffle-recommended table as bare ref on either side of a join.
    for table in from_tables + joined_tables:
        schema = (table.db or "").lower()
        name = table.name.lower()
        if not schema:
            continue
        if advisor_data.join_strategy_for(schema, name) != "shuffle":
            continue
        key = advisor_data.table_key(schema, name)
        findings.append(
            _finding(
                "R08",
                f"Shuffle-recommended table {key} is joined directly (not via subquery/CTE)",
                "Consider pre-filtering in a subquery/CTE before the join.",
            )
        )

    return findings


def _from_table(select: exp.Select) -> exp.Table | None:
    from_ = select.args.get("from_")
    if from_ is not None and isinstance(from_.this, exp.Table):
        return from_.this
    return None


def _cartesian_findings(select: exp.Select) -> list[Finding]:
    findings: list[Finding] = []
    where = select.args.get("where")
    from_table = None
    from_ = select.args.get("from_")
    if from_ is not None:
        from_table = from_.this if isinstance(from_.this, exp.Table) else None

    for join in select.args.get("joins") or []:
        kind = (join.args.get("kind") or "").upper()
        on = join.args.get("on")
        is_cross = kind == "CROSS"
        is_true_on = on is None or (isinstance(on, exp.Boolean) and on.this is True)
        if not (is_cross or is_true_on):
            continue
        right = _join_table(join)
        if from_table is None or right is None:
            # Still flag structural cartesian when we can't name sides.
            if not _where_links_any(where):
                findings.append(
                    _finding(
                        "R09",
                        "Cartesian join shape found with no equality predicate linking both sides in WHERE",
                        "Add an explicit join condition, or keep a deliberate cross join only for tiny inputs.",
                    )
                )
            continue
        left_aliases = {_table_aliases(from_table)}
        # Include earlier join tables as left side for multi-way.
        for prior in select.args.get("joins") or []:
            if prior is join:
                break
            pt = _join_table(prior)
            if pt is not None:
                left_aliases.add(_table_aliases(pt))
        right_alias = _table_aliases(right)
        if _where_links_sides(where, left_aliases, {right_alias}):
            continue
        findings.append(
            _finding(
                "R09",
                "Cartesian join shape found with no equality predicate linking both sides in WHERE",
                "Add an explicit join condition, or keep a deliberate cross join only for tiny inputs.",
            )
        )
    return findings


# ── helpers ──────────────────────────────────────────────────────────────


def _finding(rule_id: str, detection: str, remediation: str) -> Finding:
    name, guideline, severity = RULE_META[rule_id]
    return Finding(
        rule_id=rule_id,
        rule_name=name,
        guideline=guideline,
        severity=severity,  # type: ignore[arg-type]
        detection=detection,
        remediation=remediation,
    )


def _dedupe(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, str, str]] = set()
    out: list[Finding] = []
    for finding in findings:
        key = (finding.rule_id, finding.detection, finding.remediation)
        if key in seen:
            continue
        seen.add(key)
        out.append(finding)
    return out


def _select_blocks(expression: exp.Expression) -> list[exp.Select]:
    return [node for node in expression.find_all(exp.Select)]


def _direct_tables(select: exp.Select) -> list[exp.Table]:
    """Tables in this select's FROM/JOIN list, not nested subquery interiors."""
    tables: list[exp.Table] = []
    from_ = select.args.get("from_")
    if from_ is not None and isinstance(from_.this, exp.Table):
        tables.append(from_.this)
    for join in select.args.get("joins") or []:
        table = _join_table(join)
        if table is not None:
            tables.append(table)
    return tables


def _join_table(join: exp.Join) -> exp.Table | None:
    this = join.this
    if isinstance(this, exp.Table):
        return this
    return None


def _projects_star_for(select: exp.Select, table: exp.Table) -> bool:
    alias = table.alias_or_name
    for projected in select.expressions:
        if isinstance(projected, exp.Star):
            return True
        if isinstance(projected, exp.Column) and isinstance(projected.this, exp.Star):
            table_qual = projected.table
            if not table_qual or table_qual.lower() == alias.lower():
                return True
        # SQLGlot may represent t.* as Column with Star
        if isinstance(projected, exp.Star) and projected.table:
            if projected.table.lower() == alias.lower():
                return True
    return False


def _columns_in(node: exp.Expression | None) -> set[str]:
    if node is None:
        return set()
    cols: set[str] = set()
    for col in node.find_all(exp.Column):
        cols.add(col.name.lower())
        if col.table:
            cols.add(f"{col.table.lower()}.{col.name.lower()}")
    return cols


def _where_references_table(
    where: exp.Expression | None,
    table: exp.Table,
    cols: set[str],
) -> bool:
    if where is None:
        return False
    alias = table.alias_or_name.lower()
    # Any column qualified with this alias, or unqualified column when this is
    # the sole table (conservative: require alias match or bare column name use).
    for col in where.find_all(exp.Column):
        if col.table and col.table.lower() == alias:
            return True
        if not col.table:
            # Unqualified — count as referencing the table if it's in this block.
            return True
    return False


def _partition_refs_in_where(
    where: exp.Expression | None,
    table: exp.Table,
    part_cols: set[str],
) -> dict[str, set[str] | bool]:
    """Classify partition-column references in WHERE.

    Returns keys: any (bool), wrapped_only (set of col names).
    """
    result: dict[str, set[str] | bool] = {"any": False, "wrapped_only": set()}
    if where is None or not part_cols:
        return result
    alias = table.alias_or_name.lower()
    bare_cols: set[str] = set()
    wrapped_cols: set[str] = set()
    for col in where.find_all(exp.Column):
        name = col.name.lower()
        if name not in part_cols:
            continue
        if col.table and col.table.lower() != alias:
            continue
        result["any"] = True
        if _column_is_wrapped(col):
            wrapped_cols.add(name)
        else:
            bare_cols.add(name)
    result["wrapped_only"] = wrapped_cols - bare_cols
    return result


def _column_is_wrapped(col: exp.Column) -> bool:
    """True when the column is the argument of a function or CAST (not bare)."""
    parent = col.parent
    while isinstance(parent, exp.Paren):
        parent = parent.parent
    if parent is None:
        return False
    # Bare predicate operand: comparison / BETWEEN / IN / LIKE side.
    if isinstance(
        parent,
        (
            exp.EQ,
            exp.NEQ,
            exp.GT,
            exp.GTE,
            exp.LT,
            exp.LTE,
            exp.Between,
            exp.In,
            exp.Like,
            exp.Where,
            exp.And,
            exp.Or,
            exp.Not,
        ),
    ):
        return False
    if isinstance(parent, (exp.Cast, exp.TryCast, exp.Anonymous, exp.Func)):
        return True
    # Arithmetic or other expression wrappers also block pruning.
    return isinstance(parent, exp.Expression)


def _wide_date_ranges(
    where: exp.Expression | None,
    table: exp.Table,
    part_cols: set[str],
    table_key: str,
) -> list[Finding]:
    if where is None or not part_cols:
        return []
    findings: list[Finding] = []
    alias = table.alias_or_name.lower()

    for between in where.find_all(exp.Between):
        col = between.this
        if not isinstance(col, exp.Column):
            continue
        if col.name.lower() not in part_cols:
            continue
        if col.table and col.table.lower() != alias:
            continue
        low = _date_literal(between.args.get("low"))
        high = _date_literal(between.args.get("high"))
        if low and high and _months_between(low, high) > _MAX_MONTHS:
            findings.append(
                _finding(
                    "R04",
                    f"Partition filter on {col.name.lower()} for {table_key} spans more than 13 calendar months "
                    f"({low.isoformat()} .. {high.isoformat()})",
                    "Narrow the date range to at most 13 calendar months, or split into sub-queries.",
                )
            )

    # Paired >=/> and <=/< bounds on the same column.
    lowers: dict[str, date] = {}
    uppers: dict[str, date] = {}
    for pred in where.find_all((exp.GTE, exp.GT, exp.LTE, exp.LT)):
        col, lit, is_lower = _bound_predicate(pred)
        if col is None or lit is None:
            continue
        if col.name.lower() not in part_cols:
            continue
        if col.table and col.table.lower() != alias:
            continue
        key = col.name.lower()
        if is_lower:
            lowers[key] = lit
        else:
            uppers[key] = lit
    for col_name, low in lowers.items():
        high = uppers.get(col_name)
        if high and _months_between(low, high) > _MAX_MONTHS:
            findings.append(
                _finding(
                    "R04",
                    f"Partition filter on {col_name} for {table_key} spans more than 13 calendar months "
                    f"({low.isoformat()} .. {high.isoformat()})",
                    "Narrow the date range to at most 13 calendar months, or split into sub-queries.",
                )
            )
    return findings


def _bound_predicate(
    pred: exp.Expression,
) -> tuple[exp.Column | None, date | None, bool]:
    """Return (column, literal_date, is_lower_bound) for inequality predicates."""
    left, right = pred.this, pred.expression
    if isinstance(left, exp.Column) and isinstance(right, exp.Literal):
        lit = _date_literal(right)
        is_lower = isinstance(pred, (exp.GTE, exp.GT))
        return left, lit, is_lower
    if isinstance(right, exp.Column) and isinstance(left, exp.Literal):
        lit = _date_literal(left)
        # Flipped: '2024-01-01' <= col  → lower bound on col
        is_lower = isinstance(pred, (exp.LTE, exp.LT))
        return right, lit, is_lower
    return None, None, False


def _date_literal(node: exp.Expression | None) -> date | None:
    if not isinstance(node, exp.Literal) or not node.is_string:
        return None
    text = node.this
    if not _DATE_LITERAL_RE.match(text):
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _months_between(start: date, end: date) -> int:
    if end < start:
        start, end = end, start
    return (end.year - start.year) * 12 + (end.month - start.month)


def _has_count_distinct(select: exp.Select) -> bool:
    for count in select.find_all(exp.Count):
        if not _owned_by_select(count, select):
            continue
        if isinstance(count.this, exp.Distinct):
            return True
    return False


def _owned_by_select(node: exp.Expression, select: exp.Select) -> bool:
    """True when node's nearest Select ancestor is ``select``."""
    parent = node.parent
    while parent is not None:
        if isinstance(parent, exp.Select):
            return parent is select
        parent = parent.parent
    return False


def _cast_wraps_column(node: exp.Expression | None) -> bool:
    if node is None:
        return False
    if isinstance(node, (exp.Cast, exp.TryCast)):
        return node.find(exp.Column) is not None
    return False


def _where_links_sides(
    where: exp.Expression | None,
    left_aliases: set[str],
    right_aliases: set[str],
) -> bool:
    if where is None:
        return False
    left_aliases = {a.lower() for a in left_aliases if a}
    right_aliases = {a.lower() for a in right_aliases if a}
    for eq in where.find_all(exp.EQ):
        lcols = [c for c in eq.this.find_all(exp.Column)] if eq.this else []
        rcols = [c for c in eq.expression.find_all(exp.Column)] if eq.expression else []
        if not lcols or not rcols:
            continue
        l_tables = {c.table.lower() for c in lcols if c.table}
        r_tables = {c.table.lower() for c in rcols if c.table}
        if (l_tables & left_aliases and r_tables & right_aliases) or (
            l_tables & right_aliases and r_tables & left_aliases
        ):
            return True
    return False


def _where_links_any(where: exp.Expression | None) -> bool:
    if where is None:
        return False
    for eq in where.find_all(exp.EQ):
        lcols = list(eq.this.find_all(exp.Column)) if eq.this else []
        rcols = list(eq.expression.find_all(exp.Column)) if eq.expression else []
        if lcols and rcols:
            return True
    return False


def _table_aliases(table: exp.Table) -> str:
    return table.alias_or_name.lower()


def _table_key_from_node(node: exp.Expression | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, exp.Schema):
        node = node.this
    if isinstance(node, exp.Table):
        schema = (node.db or "").lower()
        name = node.name.lower()
        if schema:
            return f"{schema}.{name}"
        return name
    if isinstance(node, exp.Identifier):
        return node.name.lower()
    return None


def _node_sql(node: exp.Expression | None) -> str:
    if node is None:
        return ""
    try:
        return node.sql(dialect="hive")
    except Exception:  # noqa: BLE001
        return ""


def _create_location(create: exp.Create) -> str | None:
    props = create.args.get("properties")
    if props is None:
        return None
    for prop in props.find_all(exp.LocationProperty):
        this = prop.this
        if isinstance(this, exp.Literal) and this.is_string:
            return this.this
        if this is not None:
            return this.sql(dialect="hive").strip("'\"")
    # Fallback: scan property list SQL
    text = props.sql(dialect="hive")
    match = re.search(r"LOCATION\s+'([^']+)'", text, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r'LOCATION\s+"([^"]+)"', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None
