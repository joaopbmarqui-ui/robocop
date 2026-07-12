"""Tests for dispatch/advisor_data.py — Guideline #3 seed expansion."""

from __future__ import annotations

from dispatch import advisor_data


def test_monitored_schemas_and_defaults() -> None:
    assert advisor_data.MONITORED_SCHEMAS == frozenset({"core", "gco", "mrs"})
    assert advisor_data.DEFAULT_PARTITION_COLUMN == "dw_process_date"
    assert advisor_data.MANUAL_VERSION == "v2.0"
    assert advisor_data.DATA_VERSION == "2026-07-10"


def test_slash_variants_expanded() -> None:
    assert advisor_data.join_strategy_for("core", "cut_clear_dtl_hsh") == "shuffle"
    assert advisor_data.join_strategy_for("core", "cut_clear_dtl_enc") == "shuffle"
    assert advisor_data.join_strategy_for("core", "auth_dtl_enc") == "shuffle"
    assert advisor_data.join_strategy_for("core", "auth_dtl_hsh") == "shuffle"
    assert advisor_data.join_strategy_for("gco", "clear_dtl_enc") == "shuffle"
    assert advisor_data.join_strategy_for("gco", "clear_dtl_hsh") == "shuffle"


def test_multi_database_rows_expanded() -> None:
    assert advisor_data.join_strategy_for("core", "product_hierarchy") == "broadcast"
    assert advisor_data.join_strategy_for("gco", "product_hierarchy") == "broadcast"


def test_same_name_differs_by_schema() -> None:
    assert advisor_data.join_strategy_for("core", "aggregate_merchant") == "broadcast"
    assert advisor_data.join_strategy_for("mrs", "aggregate_merchant") == "shuffle"


def test_keys_are_lowercase() -> None:
    assert all(key == key.lower() for key in advisor_data.TABLES)
    assert "core.auth_dtl_enc" in advisor_data.TABLES
    assert "mrs.program" in advisor_data.TABLES


def test_partition_default_for_monitored_unlisted() -> None:
    # Monitored schema, table not in Guideline #3 list → default partition col.
    assert advisor_data.partition_columns_for("core", "some_other_table") == ("dw_process_date",)
    assert advisor_data.partition_columns_for("temp", "my_table") == ()


def test_guideline3_row_count() -> None:
    # Verbatim expansion of the manual table:
    # cut_clear×2, mmh_location, mmh_industry, product_hierarchy×2,
    # member_hierarchy, aggregate_merchant, auth×2, clear_dtl core×2,
    # clear_dtl gco×2, plus 14 MRS rows = 28 entries.
    assert len(advisor_data.TABLES) == 28
