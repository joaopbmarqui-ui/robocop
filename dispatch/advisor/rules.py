"""Catalog rules R01–R18 evaluated against the adapted SQLGlot AST."""

from __future__ import annotations

import calendar
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
    for statement_number, expression in enumerate(adapted.expressions, start=1):
        findings.extend(
            _rules_for_expression(expression, adapted.hints, statement_number=statement_number)
        )
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
            # Only DROP TABLE IF EXISTS satisfies G#6: a plain DROP fails the
            # Job when the table does not exist yet.
            if expression.args.get("exists"):
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
        _report_location(findings, expression, table_label, user_id)
    return findings


def _report_location(
    findings: list[Finding],
    expression: exp.Create,
    table_label: str,
    user_id: str,
) -> None:
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


def _rules_for_expression(
    expression: exp.Expression,
    hints: tuple[HintRecord, ...],
    *,
    statement_number: int,
) -> list[Finding]:
    findings: list[Finding] = []
    # Walk every SELECT query block (including CTEs and subqueries).
    for block_number, select in enumerate(_select_blocks(expression), start=1):
        location = f"statement {statement_number}, query block {block_number}"
        findings.extend(_rules_for_select(select, hints, location=location))
    # UNION DISTINCT can sit above SELECT nodes.
    for union_number, union in enumerate(expression.find_all(exp.Union), start=1):
        if union.args.get("distinct") is True:
            findings.append(
                _finding(
                    "R13",
                    "UNION without ALL found",
                    "UNION ALL avoids the deduplication overhead if duplicates are acceptable.",
                    location=f"statement {statement_number}, UNION {union_number}",
                )
            )
    return findings


def _rules_for_select(
    select: exp.Select,
    hints: tuple[HintRecord, ...],
    *,
    location: str,
) -> list[Finding]:
    findings: list[Finding] = []
    tables = _direct_tables(select)
    where = select.args.get("where")

    r01_keys: set[str] = set()
    monitored_keys: list[str] = []
    # R01 / R02 / R03 / R04 per monitored table in this block.
    for table in tables:
        schema = (table.db or "").lower()
        name = table.name.lower()
        if not schema or not advisor_data.is_monitored_schema(schema):
            continue
        key = advisor_data.table_key(schema, name)
        monitored_keys.append(key)
        refs_table = _where_references_table(where, table, select)

        # R01: bare * (or t.*) with no WHERE predicate on the monitored table.
        if _projects_star_for(select, table) and not refs_table:
            findings.append(
                _finding(
                    "R01",
                    f"SELECT * over monitored table {key} with no WHERE predicate on that table",
                    "Explicit columns reduce scan and serialization work; a filtered "
                    "subquery/CTE preserves a star projection while constraining input.",
                    location=location,
                )
            )
            r01_keys.add(key)

        part_cols = {c.lower() for c in advisor_data.partition_columns_for(schema, name)}
        part_refs = _partition_refs_in_where(where, table, part_cols, select)

        # R02: no recognized partition column referenced in WHERE.
        # Suppressed when R01 already fired for this table/block.
        if key not in r01_keys and part_cols and not part_refs["any"]:
            findings.append(
                _finding(
                    "R02",
                    f"No {next(iter(part_cols))} predicate found for {key} in this query block",
                    f"Add a {next(iter(part_cols))} filter to this query block.",
                    location=location,
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
                    location=location,
                )
            )

        # R04: literal date range on a partition column exceeding 13 months.
        for detection in _wide_date_ranges(
            where,
            table,
            part_cols,
            key,
            select,
            location=location,
        ):
            findings.append(detection)

    # R15: one finding per block that references any monitored table.
    if monitored_keys and _has_count_distinct(select):
        findings.append(
            _finding(
                "R15",
                "COUNT(DISTINCT ...) found in a query block referencing monitored "
                f"table(s) {', '.join(sorted(set(monitored_keys)))}",
                "Use two-step aggregation on large tables.",
                location=location,
            )
        )

    # R05–R08 join-strategy rules.
    findings.extend(_join_strategy_findings(select, hints, location=location))

    # R09 cartesian product.
    findings.extend(_cartesian_findings(select, location=location))

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
                        location=location,
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
                        location=location,
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
                    location=location,
                )
            )

    # R14 SELECT DISTINCT.
    if select.args.get("distinct"):
        findings.append(
            _finding(
                "R14",
                "DISTINCT projection found",
                "The manual prefers GROUP BY.",
                location=location,
            )
        )

    return findings


def _join_strategy_findings(
    select: exp.Select,
    hints: tuple[HintRecord, ...],
    *,
    location: str,
) -> list[Finding]:
    findings: list[Finding] = []
    joins = list(select.args.get("joins") or [])
    if not joins:
        return findings

    from_tables = [t for t in [_from_table(select)] if t is not None]
    joined_tables = [t for t in (_join_table(j) for j in joins) if t is not None]

    def hint_for(table: exp.Table) -> HintRecord | None:
        table_span = _table_span(table)
        if table_span is None:
            return None
        for hint in hints:
            hint_span = (hint.table_start, hint.table_end)
            if hint.kind in ("BROADCAST", "SHUFFLE") and hint_span == table_span:
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
                    f"[{strategy.upper()}] is the catalog-recommended strategy for {key} "
                    f"({advisor_data.DATA_VERSION}).",
                    location=location,
                )
            )
        elif strategy == "broadcast" and hint.kind == "SHUFFLE":
            findings.append(
                _finding(
                    "R06",
                    f"[SHUFFLE] hint found on broadcast-recommended {key}",
                    f"Use [BROADCAST] per the recommended join-strategy list "
                    f"({advisor_data.DATA_VERSION}).",
                    location=location,
                )
            )
        elif strategy == "shuffle" and hint.kind == "BROADCAST":
            findings.append(
                _finding(
                    "R07",
                    f"[BROADCAST] hint found on shuffle-recommended {key}",
                    f"Use [SHUFFLE] per the recommended join-strategy list "
                    f"({advisor_data.DATA_VERSION}).",
                    location=location,
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
                "A pre-filtered subquery/CTE can reduce the large table before the join.",
                location=location,
            )
        )

    return findings


def _from_table(select: exp.Select) -> exp.Table | None:
    from_ = select.args.get("from_")
    if from_ is not None and isinstance(from_.this, exp.Table):
        return from_.this
    return None


def _cartesian_findings(select: exp.Select, *, location: str) -> list[Finding]:
    findings: list[Finding] = []
    where = select.args.get("where")
    from_ = select.args.get("from_")
    from_relation = from_.this if from_ is not None else None

    for join in select.args.get("joins") or []:
        kind = (join.args.get("kind") or "").upper()
        on = join.args.get("on")
        using = join.args.get("using")
        is_cross = kind == "CROSS"
        is_true_on = (on is None and not using) or (isinstance(on, exp.Boolean) and on.this is True)
        if not (is_cross or is_true_on):
            continue
        left_aliases = {_relation_alias(from_relation)}
        # Include earlier join tables as left side for multi-way.
        for prior in select.args.get("joins") or []:
            if prior is join:
                break
            left_aliases.add(_relation_alias(prior.this))
        right_alias = _relation_alias(join.this)
        if right_alias and _where_links_sides(
            where,
            left_aliases,
            {right_alias},
            select,
        ):
            continue
        findings.append(
            _finding(
                "R09",
                "Cartesian join shape found with no equality predicate linking both sides in WHERE",
                "An explicit join condition links both sides; a deliberate cross join "
                "is appropriate only for tiny inputs.",
                location=location,
            )
        )
    return findings


# ── helpers ──────────────────────────────────────────────────────────────


def _finding(
    rule_id: str,
    detection: str,
    remediation: str,
    *,
    location: str = "",
) -> Finding:
    name, guideline, severity = RULE_META[rule_id]
    return Finding(
        rule_id=rule_id,
        rule_name=name,
        guideline=guideline,
        severity=severity,  # type: ignore[arg-type]
        detection=detection,
        remediation=remediation,
        location=location,
    )


def _dedupe(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, str, str, str]] = set()
    out: list[Finding] = []
    for finding in findings:
        key = (finding.rule_id, finding.detection, finding.remediation, finding.location)
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


def _table_span(table: exp.Table) -> tuple[int | None, int | None] | None:
    """Return the original source span for a parsed table reference."""
    starts: list[int] = []
    ends: list[int] = []
    for part_name in ("catalog", "db", "this"):
        part = table.args.get(part_name)
        if not isinstance(part, exp.Expression):
            continue
        start = part.meta.get("start")
        end = part.meta.get("end")
        if isinstance(start, int) and isinstance(end, int):
            starts.append(start)
            ends.append(end + 1)
    if not starts:
        return None
    return min(starts), max(ends)


def _relation_alias(relation: exp.Expression | None) -> str:
    if relation is None:
        return ""
    alias = relation.alias_or_name
    return alias.lower() if alias else ""


def _projects_star_for(select: exp.Select, table: exp.Table) -> bool:
    alias = table.alias_or_name
    for projected in select.expressions:
        if isinstance(projected, exp.Star):
            return True
        if isinstance(projected, exp.Column) and isinstance(projected.this, exp.Star):
            table_qual = projected.table
            if not table_qual or table_qual.lower() == alias.lower():
                return True
    return False


def _where_references_table(
    where: exp.Expression | None,
    table: exp.Table,
    select: exp.Select,
) -> bool:
    if where is None:
        return False
    alias = table.alias_or_name.lower()
    # Any column qualified with this alias, or unqualified column when this is
    # the sole table (conservative: require alias match or bare column name use).
    for col in where.find_all(exp.Column):
        if not _owned_by_select(col, select):
            continue
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
    select: exp.Select,
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
        if not _owned_by_select(col, select):
            continue
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
    """True when the column is inside a function or CAST wrapper.

    Predicate operands and arithmetic expressions are outside R03's catalog
    condition, so only explicit function and CAST ancestry counts.
    """
    parent = col.parent
    while parent is not None and not isinstance(parent, exp.Select):
        if isinstance(parent, (exp.Predicate, exp.Connector)):
            return False
        if isinstance(parent, (exp.Cast, exp.TryCast, exp.Anonymous, exp.Func)):
            return True
        parent = parent.parent
    return False


def _wide_date_ranges(
    where: exp.Expression | None,
    table: exp.Table,
    part_cols: set[str],
    table_key: str,
    select: exp.Select,
    *,
    location: str,
) -> list[Finding]:
    if where is None or not part_cols:
        return []
    findings: list[Finding] = []
    alias = table.alias_or_name.lower()

    for between in where.find_all(exp.Between):
        if not _owned_by_select(between, select):
            continue
        col = between.this
        if not isinstance(col, exp.Column):
            continue
        if col.name.lower() not in part_cols:
            continue
        if col.table and col.table.lower() != alias:
            continue
        low = _date_literal(between.args.get("low"))
        high = _date_literal(between.args.get("high"))
        if low and high and _exceeds_month_limit(low, high, _MAX_MONTHS):
            findings.append(
                _finding(
                    "R04",
                    f"Partition filter on {col.name.lower()} for {table_key} spans more than 13 calendar months "
                    f"({low.isoformat()} .. {high.isoformat()})",
                    "Narrow the date range to at most 13 calendar months, or split into sub-queries.",
                    location=location,
                )
            )

    # Paired >=/> and <=/< bounds on the same column.
    lowers: dict[str, date] = {}
    uppers: dict[str, date] = {}
    pred: exp.Expression
    for pred in where.find_all(exp.GTE, exp.GT, exp.LTE, exp.LT):
        if not _owned_by_select(pred, select):
            continue
        col, lit, is_lower = _bound_predicate(pred)
        if col is None or lit is None:
            continue
        if col.name.lower() not in part_cols:
            continue
        if col.table and col.table.lower() != alias:
            continue
        key = col.name.lower()
        if is_lower:
            lowers[key] = max(lit, lowers.get(key, lit))
        else:
            uppers[key] = min(lit, uppers.get(key, lit))
    for col_name, low in lowers.items():
        high = uppers.get(col_name)
        if high and _exceeds_month_limit(low, high, _MAX_MONTHS):
            findings.append(
                _finding(
                    "R04",
                    f"Partition filter on {col_name} for {table_key} spans more than 13 calendar months "
                    f"({low.isoformat()} .. {high.isoformat()})",
                    "Narrow the date range to at most 13 calendar months, or split into sub-queries.",
                    location=location,
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


def _exceeds_month_limit(start: date, end: date, months: int) -> bool:
    """True when ``end`` is later than ``start`` plus ``months`` calendar months.

    Day-precise per the catalog: 2023-01-15 .. 2024-02-20 exceeds 13 months
    (limit lands on 2024-02-15), while 2023-01-01 .. 2024-02-01 does not.
    """
    if end < start:
        start, end = end, start
    total = start.month - 1 + months
    year = start.year + total // 12
    month = total % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return end > date(year, month, day)


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
    return any(cast.find(exp.Column) is not None for cast in node.find_all(exp.Cast, exp.TryCast))


def _where_links_sides(
    where: exp.Expression | None,
    left_aliases: set[str],
    right_aliases: set[str],
    select: exp.Select,
) -> bool:
    if where is None:
        return False
    left_aliases = {a.lower() for a in left_aliases if a}
    right_aliases = {a.lower() for a in right_aliases if a}
    for eq in where.find_all(exp.EQ):
        if not _owned_by_select(eq, select):
            continue
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
