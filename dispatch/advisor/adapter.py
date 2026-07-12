"""Impala compatibility adapter for SQLGlot Hive parsing.

Scans the original SQL (respecting strings, quoted identifiers, and comments),
records Impala-only constructs with source spans, and builds a length-preserving
parse copy for ``read="hive"``. The original SQL is never mutated or replaced
as launch/preview input. See the engine research adapter contract and ADR-0006.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

import sqlglot
from sqlglot import exp

HintKind = Literal["BROADCAST", "SHUFFLE", "STRAIGHT_JOIN"]
HintForm = Literal["bracket", "comment", "keyword"]

_TEMPLATE_TOKENS = ("{date_inicio}", "{date_fim}")
_BRACKET_HINT_RE = re.compile(r"\[\s*(BROADCAST|SHUFFLE)\s*\]", re.IGNORECASE)
_COMMENT_HINT_RE = re.compile(
    r"/\*\s*\+\s*(BROADCAST|SHUFFLE)\s*\*/",
    re.IGNORECASE,
)
_STRAIGHT_JOIN_RE = re.compile(r"\bSTRAIGHT_JOIN\b", re.IGNORECASE)
_JOIN_KEYWORD_RE = re.compile(r"\bJOIN\b", re.IGNORECASE)
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass(frozen=True)
class HintRecord:
    """A recognized Impala hint with its original source span."""

    kind: HintKind
    form: HintForm
    start: int
    end: int
    # For join hints: the table reference immediately following JOIN + hint.
    table_sql: str | None = None
    table_start: int | None = None
    table_end: int | None = None


@dataclass(frozen=True)
class AdapterResult:
    """Outcome of adapting SQL for structural analysis."""

    available: bool
    original_sql: str
    parse_sql: str
    hints: tuple[HintRecord, ...]
    expressions: tuple[exp.Expression, ...]
    reason: str = ""


def adapt(sql_text: str) -> AdapterResult:
    """Mask Impala-only tokens and parse with Hive, or report unavailable."""
    if _has_executable_template_token(sql_text):
        return AdapterResult(
            available=False,
            original_sql=sql_text,
            parse_sql=sql_text,
            hints=(),
            expressions=(),
            reason="template token outside string or comment",
        )

    hints, mask_ranges = _collect_hints_and_masks(sql_text)
    parse_sql = _apply_masks(sql_text, mask_ranges)
    try:
        expressions = tuple(
            node for node in sqlglot.parse(parse_sql, read="hive") if node is not None
        )
    except sqlglot.errors.SqlglotError as exc:
        return AdapterResult(
            available=False,
            original_sql=sql_text,
            parse_sql=parse_sql,
            hints=tuple(hints),
            expressions=(),
            reason=f"token/parse error: {exc}",
        )
    return AdapterResult(
        available=True,
        original_sql=sql_text,
        parse_sql=parse_sql,
        hints=tuple(hints),
        expressions=expressions,
    )


def _has_executable_template_token(sql_text: str) -> bool:
    for start, end, kind in _iter_lexical_regions(sql_text):
        if kind != "code":
            continue
        chunk = sql_text[start:end]
        for token in _TEMPLATE_TOKENS:
            if token in chunk:
                return True
    return False


def _collect_hints_and_masks(sql_text: str) -> tuple[list[HintRecord], list[tuple[int, int]]]:
    """Find maskable hints in documented positions; leave unrecognized alone."""
    hints: list[HintRecord] = []
    masks: list[tuple[int, int]] = []
    code_spans = [(s, e) for s, e, kind in _iter_lexical_regions(sql_text) if kind == "code"]
    n = len(sql_text)

    # STRAIGHT_JOIN anywhere in executable SQL.
    for start, end in code_spans:
        for match in _STRAIGHT_JOIN_RE.finditer(sql_text, start, end):
            hints.append(
                HintRecord(
                    kind="STRAIGHT_JOIN",
                    form="keyword",
                    start=match.start(),
                    end=match.end(),
                )
            )
            masks.append((match.start(), match.end()))

    # Join hints immediately after JOIN. Comment-form hints are lexical comments,
    # so the peek after JOIN consults the raw SQL (not only the code span).
    for start, end in code_spans:
        for join_match in _JOIN_KEYWORD_RE.finditer(sql_text, start, end):
            cursor = join_match.end()
            while cursor < n and sql_text[cursor].isspace():
                cursor += 1
            if cursor >= n:
                continue
            bracket = _BRACKET_HINT_RE.match(sql_text, cursor)
            comment = None if bracket else _COMMENT_HINT_RE.match(sql_text, cursor)
            match = bracket or comment
            if not match:
                continue
            # Bracket hints must sit in executable SQL (not inside a string).
            if bracket and not any(s <= match.start() < e for s, e in code_spans):
                continue
            kind = match.group(1).upper()
            assert kind in ("BROADCAST", "SHUFFLE")
            form: HintForm = "bracket" if bracket else "comment"
            table_sql, table_start, table_end = _read_table_ref(sql_text, match.end(), n)
            hints.append(
                HintRecord(
                    kind=kind,  # type: ignore[arg-type]
                    form=form,
                    start=match.start(),
                    end=match.end(),
                    table_sql=table_sql,
                    table_start=table_start,
                    table_end=table_end,
                )
            )
            masks.append((match.start(), match.end()))

    masks.sort()
    return hints, masks


def _read_table_ref(
    sql_text: str, start: int, limit: int
) -> tuple[str | None, int | None, int | None]:
    """Read ``schema.table`` / ``table`` / backtick form after a join hint."""
    cursor = start
    while cursor < limit and sql_text[cursor].isspace():
        cursor += 1
    if cursor >= limit:
        return None, None, None
    # Optional catalog/schema qualifiers and backticks.
    parts: list[str] = []
    table_start = cursor
    while cursor < limit:
        if sql_text[cursor] == "`":
            close = sql_text.find("`", cursor + 1, limit)
            if close < 0:
                break
            parts.append(sql_text[cursor + 1 : close])
            cursor = close + 1
        else:
            ident = _IDENT_RE.match(sql_text, cursor, limit)
            if not ident:
                break
            parts.append(ident.group(0))
            cursor = ident.end()
        if cursor < limit and sql_text[cursor] == ".":
            cursor += 1
            continue
        break
    if not parts:
        return None, None, None
    return ".".join(parts), table_start, cursor


def _apply_masks(sql_text: str, masks: list[tuple[int, int]]) -> str:
    if not masks:
        return sql_text
    chars = list(sql_text)
    for start, end in masks:
        for i in range(start, end):
            chars[i] = " "
    return "".join(chars)


def _iter_lexical_regions(sql_text: str) -> list[tuple[int, int, str]]:
    """Partition SQL into code / string / identifier / comment regions."""
    regions: list[tuple[int, int, str]] = []
    i = 0
    n = len(sql_text)
    code_start = 0
    while i < n:
        ch = sql_text[i]
        nxt = sql_text[i + 1] if i + 1 < n else ""

        if ch == "-" and nxt == "-":
            if i > code_start:
                regions.append((code_start, i, "code"))
            j = sql_text.find("\n", i + 2)
            j = n if j < 0 else j + 1
            regions.append((i, j, "comment"))
            i = j
            code_start = i
            continue

        if ch == "/" and nxt == "*":
            if i > code_start:
                regions.append((code_start, i, "code"))
            j = sql_text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            regions.append((i, j, "comment"))
            i = j
            code_start = i
            continue

        if ch in ("'", '"', "`"):
            if i > code_start:
                regions.append((code_start, i, "code"))
            j = i + 1
            quote = ch
            kind = "identifier" if quote == "`" else "string"
            while j < n:
                if sql_text[j] == "\\" and quote != "`":
                    j += 2
                    continue
                if sql_text[j] == quote:
                    # SQL doubled-quote escape inside strings
                    if quote != "`" and j + 1 < n and sql_text[j + 1] == quote:
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            regions.append((i, j, kind))
            i = j
            code_start = i
            continue

        i += 1

    if code_start < n:
        regions.append((code_start, n, "code"))
    return regions
