"""Impala adapter contract tests — masking, spans, analysis-unavailable."""

from __future__ import annotations

import pytest

from dispatch.advisor.adapter import adapt


def test_bracket_broadcast_hint_masked_length_preserving() -> None:
    sql = "SELECT * FROM a INNER JOIN [BROADCAST] b ON a.id = b.id"
    result = adapt(sql)
    assert result.available
    assert len(result.parse_sql) == len(sql)
    assert "[BROADCAST]" not in result.parse_sql
    assert sql == result.original_sql  # never mutate original
    assert any(h.kind == "BROADCAST" and h.form == "bracket" for h in result.hints)
    hint = next(h for h in result.hints if h.kind == "BROADCAST")
    assert hint.table_sql and hint.table_sql.lower() == "b"


def test_comment_shuffle_hint_masked() -> None:
    sql = "SELECT * FROM a JOIN /* +SHUFFLE */ core.cut_clear_dtl_enc AS c ON a.id = c.id"
    result = adapt(sql)
    assert result.available
    assert "/* +SHUFFLE */" not in result.parse_sql
    assert any(h.kind == "SHUFFLE" and h.form == "comment" for h in result.hints)
    hint = next(h for h in result.hints if h.kind == "SHUFFLE")
    assert hint.table_sql and "cut_clear_dtl_enc" in hint.table_sql.lower()


def test_hint_table_span_allows_whitespace_around_qualifier_dot() -> None:
    sql = "SELECT * FROM a JOIN [BROADCAST] core . cut_clear_dtl_enc c ON a.id = c.id"
    result = adapt(sql)
    assert result.available
    hint = next(h for h in result.hints if h.kind == "BROADCAST")
    assert hint.table_sql == "core.cut_clear_dtl_enc"
    assert sql[hint.table_start : hint.table_end] == "core . cut_clear_dtl_enc"


def test_straight_join_masked() -> None:
    sql = "SELECT STRAIGHT_JOIN * FROM a JOIN b ON a.id = b.id"
    result = adapt(sql)
    assert result.available
    assert "STRAIGHT_JOIN" not in result.parse_sql
    assert any(h.kind == "STRAIGHT_JOIN" for h in result.hints)
    assert len(result.parse_sql) == len(sql)


def test_hint_inside_string_not_masked() -> None:
    sql = "SELECT '[BROADCAST]' AS note FROM a"
    result = adapt(sql)
    assert result.available
    assert "[BROADCAST]" in result.parse_sql
    assert result.hints == ()


def test_hint_inside_comment_not_treated_as_join_hint() -> None:
    sql = "SELECT * FROM a -- JOIN [BROADCAST] ignored\nJOIN b ON a.id = b.id"
    result = adapt(sql)
    assert result.available
    assert not any(h.kind == "BROADCAST" for h in result.hints)


def test_unquoted_template_token_makes_analysis_unavailable() -> None:
    sql = "SELECT * FROM t WHERE dw_process_date = {date_inicio}"
    result = adapt(sql)
    assert not result.available
    assert "template" in result.reason


def test_quoted_template_token_parses() -> None:
    sql = "SELECT * FROM t WHERE dw_process_date BETWEEN '{date_inicio}' AND '{date_fim}'"
    result = adapt(sql)
    assert result.available
    assert len(result.expressions) == 1


def test_unparseable_sql_unavailable() -> None:
    sql = "SELECT FROM WHERE"
    result = adapt(sql)
    assert not result.available
    assert "parse" in result.reason.lower()


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 'unterminated",
        'SELECT "unterminated',
        "SELECT /* unterminated",
    ],
)
def test_tokenization_failure_unavailable(sql: str) -> None:
    result = adapt(sql)
    assert not result.available
    assert "token" in result.reason.lower()


def test_bracket_hint_not_after_join_left_unmasked_may_fail() -> None:
    # Unrecognized position: left unmasked; Hive parse fails → unavailable.
    sql = "SELECT [BROADCAST] * FROM a"
    result = adapt(sql)
    assert not result.available
