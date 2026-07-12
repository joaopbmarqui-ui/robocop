"""Impala syntax corpus — every catalog rule firing and not firing.

Fixtures cover R01–R15 plus DDL for R17/R18. R16 is a form-field check.
Also nested queries, CTEs, comments, strings, template tokens, both hint
spellings, and analysis-unavailable inputs.
"""

from __future__ import annotations

import pytest

from dispatch.advisor import analyze
from dispatch.advisor.models import badge_markup


def _ids(result) -> set[str]:
    return {f.rule_id for f in result.findings}


def _analyze(sql: str, **kwargs):
    defaults = {
        "source_type": "SqlFile",
        "destination_type": "Table",
        "destination_table": "alice_result",
        "user_id": "alice",
    }
    defaults.update(kwargs)
    return analyze(sql, **defaults)


# ── R01 select-star-unfiltered ──────────────────────────────────────────


def test_r01_fires_on_monitored_star_unfiltered() -> None:
    r = _analyze("SELECT * FROM core.cut_clear_dtl_enc")
    assert "R01" in _ids(r)


def test_r01_fires_with_limit() -> None:
    r = _analyze("SELECT * FROM core.cut_clear_dtl_enc LIMIT 10")
    assert "R01" in _ids(r)


def test_r01_silent_when_where_present() -> None:
    r = _analyze("SELECT * FROM core.cut_clear_dtl_enc WHERE merchant_name = 'x'")
    assert "R01" not in _ids(r)
    assert "R02" in _ids(r)  # missing partition filter


def test_r01_silent_on_unmonitored() -> None:
    r = _analyze("SELECT * FROM my_temp")
    assert "R01" not in _ids(r)


def test_r01_silent_on_filtered_subquery_star() -> None:
    r = _analyze(
        """
        SELECT * FROM (
          SELECT id FROM core.cut_clear_dtl_enc
          WHERE dw_process_date = '2024-01-01'
        ) x
        """
    )
    assert "R01" not in _ids(r)


def test_r01_suppresses_r02_same_block() -> None:
    r = _analyze("SELECT * FROM core.cut_clear_dtl_enc")
    assert "R01" in _ids(r)
    assert "R02" not in _ids(r)


def test_r01_ignores_shadowed_alias_in_nested_query() -> None:
    r = _analyze(
        """
        SELECT * FROM core.cut_clear_dtl_enc c
        WHERE EXISTS (SELECT 1 FROM other c WHERE c.x = 1)
        """
    )
    assert "R01" in _ids(r)


# ── R02 / R03 partition filters ─────────────────────────────────────────


def test_r02_fires_without_partition_predicate() -> None:
    r = _analyze("SELECT id FROM core.cut_clear_dtl_enc WHERE merchant_name = 'x'")
    assert "R02" in _ids(r)


def test_r02_silent_with_partition_predicate() -> None:
    r = _analyze("SELECT id FROM core.cut_clear_dtl_enc WHERE dw_process_date = '2024-01-01'")
    assert "R02" not in _ids(r)
    assert "R03" not in _ids(r)


def test_r02_template_predicate_counts() -> None:
    r = _analyze(
        "SELECT id FROM core.t WHERE dw_process_date BETWEEN '{date_inicio}' AND '{date_fim}'",
        source_type="SqlTemplate",
    )
    assert r.available
    assert "R02" not in _ids(r)


def test_r03_fires_when_partition_only_wrapped() -> None:
    r = _analyze("SELECT id FROM core.cut_clear_dtl_enc WHERE year(dw_process_date) = 2024")
    assert "R03" in _ids(r)
    assert "R02" not in _ids(r)


def test_r03_silent_when_bare_also_present() -> None:
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc
        WHERE dw_process_date >= '2024-01-01'
          AND year(dw_process_date) = 2024
        """
    )
    assert "R03" not in _ids(r)


def test_r03_function_on_literal_side_ok() -> None:
    r = _analyze(
        "SELECT id FROM core.cut_clear_dtl_enc WHERE dw_process_date = cast('2024-01-01' AS DATE)"
    )
    assert "R03" not in _ids(r)
    assert "R02" not in _ids(r)


def test_r02_ignores_partition_column_in_nested_query() -> None:
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc c
        WHERE EXISTS (
          SELECT 1 FROM other c
          WHERE c.dw_process_date = '2024-01-01'
        )
        """
    )
    assert "R02" in _ids(r)


def test_r03_silent_on_arithmetic_partition_expression() -> None:
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc
        WHERE dw_process_date + 0 = '2024-01-01'
        """
    )
    assert "R03" not in _ids(r)


def test_r03_fires_when_arithmetic_is_nested_in_function() -> None:
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc
        WHERE year(dw_process_date + 0) = 2024
        """
    )
    assert "R03" in _ids(r)


# ── R04 date-range-over-13-months ───────────────────────────────────────


def test_r04_fires_on_wide_between() -> None:
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc
        WHERE dw_process_date BETWEEN '2023-01-01' AND '2024-03-01'
        """
    )
    assert "R04" in _ids(r)


def test_r04_silent_within_13_months() -> None:
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc
        WHERE dw_process_date BETWEEN '2024-01-01' AND '2025-01-01'
        """
    )
    assert "R04" not in _ids(r)


def test_r04_fires_on_paired_bounds() -> None:
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc
        WHERE dw_process_date >= '2022-01-01' AND dw_process_date < '2024-01-01'
        """
    )
    assert "R04" in _ids(r)


def test_r04_silent_one_sided() -> None:
    r = _analyze("SELECT id FROM core.cut_clear_dtl_enc WHERE dw_process_date >= '2020-01-01'")
    assert "R04" not in _ids(r)


def test_r04_day_component_exceeds_limit() -> None:
    # 13 calendar months land on 2024-02-15; five more days exceed the limit.
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc
        WHERE dw_process_date BETWEEN '2023-01-15' AND '2024-02-20'
        """
    )
    assert "R04" in _ids(r)


def test_r04_exactly_13_months_passes() -> None:
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc
        WHERE dw_process_date BETWEEN '2023-01-15' AND '2024-02-15'
        """
    )
    assert "R04" not in _ids(r)


def test_r04_uses_effective_bounds_when_predicates_repeat() -> None:
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc
        WHERE dw_process_date >= '2024-01-01'
          AND dw_process_date >= '2020-01-01'
          AND dw_process_date < '2024-06-01'
        """
    )
    assert "R04" not in _ids(r)


def test_r04_ignores_date_range_in_nested_query() -> None:
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc c
        WHERE EXISTS (
          SELECT 1 FROM other c
          WHERE c.dw_process_date BETWEEN '2020-01-01' AND '2024-01-01'
        )
        """
    )
    assert "R04" not in _ids(r)


# ── R05–R08 join hints / large tables ───────────────────────────────────


def test_r05_missing_hint() -> None:
    r = _analyze(
        """
        SELECT a.id FROM my_temp a
        JOIN core.product_hierarchy p ON a.id = p.product_code
        WHERE a.dw_process_date = '2024-01-01'
        """
    )
    assert "R05" in _ids(r)


def test_r05_silent_with_broadcast_hint() -> None:
    r = _analyze(
        """
        SELECT a.id FROM my_temp a
        JOIN [BROADCAST] core.product_hierarchy p ON a.id = p.product_code
        """
    )
    assert "R05" not in _ids(r)


def test_r06_wasteful_shuffle_on_broadcast_table() -> None:
    r = _analyze(
        """
        SELECT a.id FROM my_temp a
        JOIN [SHUFFLE] core.product_hierarchy p ON a.id = p.product_code
        """
    )
    assert "R06" in _ids(r)


def test_r07_dangerous_broadcast_on_shuffle_table() -> None:
    r = _analyze(
        """
        SELECT a.id FROM my_temp a
        JOIN [BROADCAST] core.cut_clear_dtl_enc c ON a.id = c.dw_acct_id
        """
    )
    assert "R07" in _ids(r)


def test_r07_comment_form_hint() -> None:
    r = _analyze(
        """
        SELECT a.id FROM my_temp a
        JOIN /* +BROADCAST */ core.cut_clear_dtl_enc c ON a.id = c.dw_acct_id
        """
    )
    assert "R07" in _ids(r)


def test_r08_direct_join_of_large_table() -> None:
    r = _analyze(
        """
        SELECT a.id FROM core.cut_clear_dtl_enc a
        JOIN [BROADCAST] core.product_hierarchy p ON a.dw_product_cd = p.product_code
        WHERE a.dw_process_date = '2024-01-01'
        """
    )
    assert "R08" in _ids(r)


def test_r08_silent_when_prefiltered_subquery() -> None:
    r = _analyze(
        """
        SELECT x.id FROM (
          SELECT id, dw_product_cd FROM core.cut_clear_dtl_enc
          WHERE dw_process_date = '2024-01-01'
        ) x
        JOIN [BROADCAST] core.product_hierarchy p ON x.dw_product_cd = p.product_code
        """
    )
    assert "R08" not in _ids(r)


def test_join_hint_does_not_leak_to_later_statement() -> None:
    r = _analyze(
        """
        SELECT a.id FROM first_input a
        JOIN [BROADCAST] core.product_hierarchy p ON a.id = p.product_code;

        SELECT b.id FROM second_input b
        JOIN core.product_hierarchy p ON b.id = p.product_code
        """
    )
    assert sum(f.rule_id == "R05" for f in r.findings) == 1


# ── R09 cartesian-product ───────────────────────────────────────────────


def test_r09_fires_on_cross_join() -> None:
    r = _analyze("SELECT * FROM a CROSS JOIN b")
    assert "R09" in _ids(r)


def test_r09_fires_on_join_without_on() -> None:
    r = _analyze("SELECT * FROM a JOIN b")
    assert "R09" in _ids(r)


def test_r09_silent_old_style_with_where_eq() -> None:
    r = _analyze("SELECT * FROM a, b WHERE a.id = b.id")
    assert "R09" not in _ids(r)


def test_r09_silent_with_on() -> None:
    r = _analyze("SELECT * FROM a JOIN b ON a.id = b.id")
    assert "R09" not in _ids(r)


def test_r09_silent_with_using() -> None:
    r = _analyze("SELECT * FROM a JOIN b USING (id)")
    assert "R09" not in _ids(r)


def test_r09_fires_when_derived_cross_join_equality_uses_one_side() -> None:
    r = _analyze(
        """
        SELECT * FROM (SELECT * FROM a) x
        CROSS JOIN b
        WHERE x.id = x.other_id
        """
    )
    assert "R09" in _ids(r)


# ── R10–R15 style / heuristic ───────────────────────────────────────────


def test_r10_cast_in_join() -> None:
    r = _analyze("SELECT * FROM a JOIN b ON CAST(a.id AS STRING) = b.id")
    assert "R10" in _ids(r)


def test_r10_nested_cast_in_join() -> None:
    r = _analyze("SELECT * FROM a JOIN b ON COALESCE(CAST(a.id AS STRING), '') = b.id")
    assert "R10" in _ids(r)


def test_r11_leading_wildcard() -> None:
    r = _analyze("SELECT * FROM t WHERE name LIKE '%abc'")
    assert "R11" in _ids(r)


def test_r11_silent_anchored() -> None:
    r = _analyze("SELECT * FROM t WHERE name LIKE 'abc%'")
    assert "R11" not in _ids(r)


def test_r12_regexp() -> None:
    r = _analyze("SELECT * FROM t WHERE name REGEXP '^a'")
    assert "R12" in _ids(r)


def test_r13_union_distinct() -> None:
    r = _analyze("SELECT 1 UNION SELECT 2")
    assert "R13" in _ids(r)


def test_r13_silent_union_all() -> None:
    r = _analyze("SELECT 1 UNION ALL SELECT 2")
    assert "R13" not in _ids(r)


def test_r14_select_distinct() -> None:
    r = _analyze("SELECT DISTINCT a FROM t")
    assert "R14" in _ids(r)


def test_r14_reports_each_query_block_with_distinct_location() -> None:
    r = _analyze("SELECT DISTINCT a FROM t; SELECT DISTINCT b FROM u")
    findings = [f for f in r.findings if f.rule_id == "R14"]
    assert len(findings) == 2
    assert all(f.location for f in findings)
    assert len({f.location for f in findings}) == 2


def test_r15_count_distinct_monitored() -> None:
    r = _analyze(
        "SELECT COUNT(DISTINCT id) FROM core.cut_clear_dtl_enc WHERE dw_process_date = '2024-01-01'"
    )
    assert "R15" in _ids(r)


def test_r15_silent_on_temp() -> None:
    r = _analyze("SELECT COUNT(DISTINCT id) FROM my_temp")
    assert "R15" not in _ids(r)


# ── R16 form field ──────────────────────────────────────────────────────


def test_r16_fires_without_user_prefix() -> None:
    r = _analyze(
        "SELECT 1",
        destination_table="result",
        user_id="alice",
    )
    assert "R16" in _ids(r)


def test_r16_silent_with_prefix() -> None:
    r = _analyze(
        "SELECT 1",
        destination_table="alice_result",
        user_id="alice",
    )
    assert "R16" not in _ids(r)


def test_r16_silent_for_csv_only() -> None:
    r = _analyze(
        "SELECT 1",
        destination_type="Csv",
        destination_table="result",
        user_id="alice",
    )
    assert "R16" not in _ids(r)


def test_r16_silent_for_existing_table() -> None:
    r = _analyze(
        "",
        source_type="ExistingTable",
        destination_type="Csv",
        destination_table="result",
        user_id="alice",
    )
    assert r.available
    assert r.findings == ()


# ── R17 / R18 DDL ───────────────────────────────────────────────────────


def test_r17_missing_drop() -> None:
    r = _analyze("CREATE TABLE alice.t LOCATION '/ads_storage/alice/t' AS SELECT 1")
    assert "R17" in _ids(r)


def test_r17_silent_with_drop() -> None:
    r = _analyze(
        """
        DROP TABLE IF EXISTS alice.t;
        CREATE TABLE alice.t LOCATION '/ads_storage/alice/t' AS SELECT 1
        """
    )
    assert "R17" not in _ids(r)


def test_r18_missing_location() -> None:
    r = _analyze(
        """
        DROP TABLE IF EXISTS alice.t;
        CREATE TABLE alice.t AS SELECT 1
        """
    )
    assert "R18" in _ids(r)


def test_r18_location_outside_user_dir() -> None:
    r = _analyze(
        """
        DROP TABLE IF EXISTS alice.t;
        CREATE TABLE alice.t LOCATION '/ads_storage/other/t' AS SELECT 1
        """
    )
    assert "R18" in _ids(r)


def test_r18_silent_with_user_segment() -> None:
    r = _analyze(
        """
        DROP TABLE IF EXISTS alice.t;
        CREATE TABLE alice.t LOCATION '/ads_storage/alice/t' AS SELECT 1
        """
    )
    assert "R18" not in _ids(r)


def test_r17_plain_drop_does_not_satisfy() -> None:
    # G#6 requires DROP TABLE IF EXISTS; a plain DROP fails when absent.
    r = _analyze(
        """
        DROP TABLE alice.t;
        CREATE TABLE alice.t LOCATION '/ads_storage/alice/t' AS SELECT 1
        """
    )
    assert "R17" in _ids(r)


def test_ddl_rules_skip_wrapped_select_path() -> None:
    # Bare SELECT is wrapped by table_wrapper — not self-contained DDL.
    r = _analyze("SELECT 1 AS x")
    assert "R17" not in _ids(r)
    assert "R18" not in _ids(r)


# ── analysis unavailable ────────────────────────────────────────────────


def test_unavailable_unquoted_template() -> None:
    r = _analyze("SELECT * FROM t WHERE d = {date_inicio}")
    assert not r.available
    assert r.findings == () or _ids(r) <= {"R16"}  # form findings only


def test_unavailable_keeps_form_findings_visible() -> None:
    r = _analyze(
        "SELECT * FROM t WHERE d = {date_inicio}",
        destination_table="wrong_name",
    )
    assert not r.available
    assert _ids(r) == {"R16"}
    badge = badge_markup(r)
    assert "warning" in badge
    assert "unavailable" in badge


def test_r03_silent_on_is_not_null() -> None:
    # Predicate operands are bare: IS NOT NULL must not count as wrapped.
    r = _analyze(
        """
        SELECT id FROM core.cut_clear_dtl_enc
        WHERE dw_process_date IS NOT NULL
        """
    )
    assert "R03" not in _ids(r)


def test_unavailable_unparseable() -> None:
    r = _analyze("SELECT FROM WHERE", destination_table="alice_x")
    assert not r.available


def test_unavailable_never_gates_errors() -> None:
    r = _analyze("NOT VALID SQL !!!", destination_table="alice_x")
    assert not r.available
    assert r.errors() == ()


def test_cte_and_nested_still_analyze() -> None:
    r = _analyze(
        """
        WITH filtered AS (
          SELECT id FROM core.cut_clear_dtl_enc
          WHERE dw_process_date = '2024-01-01'
        )
        SELECT DISTINCT id FROM filtered
        """
    )
    assert r.available
    assert "R14" in _ids(r)
    assert "R01" not in _ids(r)


def test_comments_and_strings_do_not_false_positive_r12() -> None:
    r = _analyze(
        """
        SELECT id FROM t
        -- name REGEXP 'nope'
        WHERE note = 'REGEXP is fine in a string'
        """
    )
    assert "R12" not in _ids(r)


@pytest.mark.parametrize(
    "sql,rule",
    [
        ("SELECT * FROM core.mmh_location", "R01"),
        ("SELECT id FROM core.mmh_industry WHERE x = 1", "R02"),
        ("SELECT 1 UNION SELECT 2", "R13"),
    ],
)
def test_parametrized_fire(sql: str, rule: str) -> None:
    assert rule in _ids(_analyze(sql))
