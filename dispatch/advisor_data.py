"""Embedded Impala join-strategy and partition metadata for the Advisor.

Seeded verbatim from Guideline #3 of the Impala optimization manual (v2.0).
Slash variants and multi-database rows are expanded into separate
``schema.table`` entries. Revisions land as ordinary reviewed PRs; git
history is the changelog.
"""

from __future__ import annotations

from typing import TypedDict

DATA_VERSION = "2026-07-10"
MANUAL_VERSION = "v2.0"

MONITORED_SCHEMAS: frozenset[str] = frozenset({"core", "gco", "mrs"})
DEFAULT_PARTITION_COLUMN = "dw_process_date"


class TableAdvice(TypedDict, total=False):
    join_strategy: str  # "broadcast" | "shuffle"
    partition_columns: tuple[str, ...]


# Keys are exact lowercase "schema.table". Values carry the recommended join
# strategy; partition_columns is optional and defaults to (DEFAULT_PARTITION_COLUMN,).
TABLES: dict[str, TableAdvice] = {
    # CORE — Guideline #3
    "core.cut_clear_dtl_hsh": {"join_strategy": "shuffle"},
    "core.cut_clear_dtl_enc": {"join_strategy": "shuffle"},
    "core.mmh_location": {"join_strategy": "shuffle"},
    "core.mmh_industry": {"join_strategy": "broadcast"},
    "core.product_hierarchy": {"join_strategy": "broadcast"},
    "core.member_hierarchy": {"join_strategy": "broadcast"},
    "core.aggregate_merchant": {"join_strategy": "broadcast"},
    "core.auth_dtl_enc": {"join_strategy": "shuffle"},
    "core.auth_dtl_hsh": {"join_strategy": "shuffle"},
    "core.clear_dtl_hsh": {"join_strategy": "shuffle"},
    "core.clear_dtl_enc": {"join_strategy": "shuffle"},
    # GCO — Guideline #3 (incl. CORE/GCO shared product_hierarchy)
    "gco.product_hierarchy": {"join_strategy": "broadcast"},
    "gco.clear_dtl_hsh": {"join_strategy": "shuffle"},
    "gco.clear_dtl_enc": {"join_strategy": "shuffle"},
    # MRS — Guideline #3
    "mrs.program": {"join_strategy": "broadcast"},
    "mrs.aggregate_merchant": {"join_strategy": "shuffle"},
    "mrs.bank_product": {"join_strategy": "broadcast"},
    "mrs.member_product_hierarchy": {"join_strategy": "broadcast"},
    "mrs.call_statistics": {"join_strategy": "broadcast"},
    "mrs.card_input_mode": {"join_strategy": "broadcast"},
    "mrs.cardholder_present": {"join_strategy": "broadcast"},
    "mrs.cardholder_redtemp_history": {"join_strategy": "shuffle"},
    "mrs.customer_account": {"join_strategy": "broadcast"},
    "mrs.member_hierarchy": {"join_strategy": "broadcast"},
    "mrs.redemption_history": {"join_strategy": "shuffle"},
    "mrs.reward_item": {"join_strategy": "shuffle"},
    "mrs.reward_matrix_item": {"join_strategy": "shuffle"},
    "mrs.trans_detail": {"join_strategy": "shuffle"},
}


def is_monitored_schema(schema: str) -> bool:
    return schema.lower() in MONITORED_SCHEMAS


def table_key(schema: str, table: str) -> str:
    return f"{schema.lower()}.{table.lower()}"


def lookup_table(schema: str, table: str) -> TableAdvice | None:
    return TABLES.get(table_key(schema, table))


def partition_columns_for(schema: str, table: str) -> tuple[str, ...]:
    """Return partition columns for a monitored-schema table.

    Unlisted monitored tables default to ``dw_process_date``. Non-monitored
    schemas return an empty tuple (no partition-filter rules apply).
    """
    if not is_monitored_schema(schema):
        return ()
    entry = lookup_table(schema, table)
    if entry and "partition_columns" in entry:
        return entry["partition_columns"]
    return (DEFAULT_PARTITION_COLUMN,)


def join_strategy_for(schema: str, table: str) -> str | None:
    entry = lookup_table(schema, table)
    if entry is None:
        return None
    return entry["join_strategy"]
