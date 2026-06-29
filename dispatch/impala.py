"""Mock-friendly Impala metadata helpers."""

from __future__ import annotations

import asyncio

from . import process, sql

QUERY_TIMEOUT_SECONDS = 30

IMPALA_BASE_ARGV = (
    "impala-shell",
    "-k",
    "-i",
    "dw.prod.impala.mastercard.int:21000",
    "--ssl",
    "--delimited",
    "--print_header",
    "--output_delimiter=|",
)


async def query(sql: str) -> str:
    try:
        rc, stdout, stderr = await process.run_exec(
            *IMPALA_BASE_ARGV, "-q", sql, timeout=QUERY_TIMEOUT_SECONDS
        )
    except (asyncio.TimeoutError, TimeoutError):
        # str(TimeoutError()) is empty, which would surface as a blank error in
        # the Browser; give the user an actionable message instead.
        raise RuntimeError(f"impala-shell timed out after {QUERY_TIMEOUT_SECONDS}s") from None
    if rc != 0:
        raise RuntimeError(stderr or stdout or f"impala-shell exited {rc}")
    return stdout


async def show_tables(schema: str, pattern: str = "*") -> list[str]:
    schema_error = sql.validate_identifier(schema, "Schema")
    if schema_error:
        raise ValueError(schema_error)
    if "'" in pattern:
        raise ValueError("SHOW TABLES pattern must not contain a single quote")
    output = await query(f"SHOW TABLES IN {schema} LIKE '{pattern}';")
    tables: list[str] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("Mock "):
            continue
        # impala-shell runs with --print_header, so SHOW TABLES emits its single
        # "name" column header as the first row. It is not a table: keeping it
        # added a phantom entry, inflated the table count, and made the
        # auto-describe of row 0 fail with "Could not resolve path".
        if line == "name":
            continue
        tables.append(line)
    return tables


def _require_full_table(full_table: str) -> None:
    full_table_error = sql.validate_full_table(full_table, "Table")
    if full_table_error:
        raise ValueError(full_table_error)


async def describe_table(full_table: str) -> str:
    _require_full_table(full_table)
    return await query(f"DESCRIBE {full_table};")


async def drop_table(full_table: str) -> str:
    _require_full_table(full_table)
    return await query(f"DROP TABLE IF EXISTS {full_table};")
