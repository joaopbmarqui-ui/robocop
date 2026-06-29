"""SQL detection and preview helpers."""

from __future__ import annotations

import calendar
import re
from datetime import date, datetime
from pathlib import Path

IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
FULL_TABLE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*")
DATE_INICIO_TOKEN = "{date_inicio}"
DATE_FIM_TOKEN = "{date_fim}"


def validate_identifier(value: str, label: str) -> str | None:
    """Return a clear error when ``value`` is not a plain Impala identifier."""
    if not IDENTIFIER_RE.fullmatch(value):
        return f"{label} must be a plain Impala identifier"
    return None


def validate_full_table(value: str, label: str = "table") -> str | None:
    """Return a clear error unless ``value`` is exactly ``schema.table``."""
    if not FULL_TABLE_RE.fullmatch(value):
        return f"{label} must be schema.table using plain Impala identifiers"
    return None


def safe_csv_path(launch_cwd: Path, table: str) -> Path:
    """Build a CSV path whose plain filename stem cannot escape ``launch_cwd``."""
    if not table or "/" in table or "\\" in table or ".." in table:
        raise ValueError("Table name must be a safe CSV filename stem")
    identifier_error = validate_identifier(table, "Table name")
    if identifier_error:
        raise ValueError(identifier_error)

    resolved_cwd = launch_cwd.resolve()
    output_path = (resolved_cwd / f"{table}.csv").resolve()
    if not output_path.is_relative_to(resolved_cwd):
        raise ValueError("CSV output path must stay within the launch directory")
    return output_path


def detect_source(sql_text: str) -> str:
    has_start = "{date_inicio}" in sql_text
    has_end = "{date_fim}" in sql_text
    return "SqlTemplate" if has_start and has_end else "SqlFile"


def template_is_complete(sql_text: str) -> bool:
    return "{date_inicio}" in sql_text and "{date_fim}" in sql_text


def is_malformed_template(sql_text: str) -> bool:
    """True when only one of `{date_inicio}` / `{date_fim}` appears - a likely typo."""
    has_start = "{date_inicio}" in sql_text
    has_end = "{date_fim}" in sql_text
    return has_start != has_end


_DDL_LEADERS = ("create", "drop", "insert", "alter", "truncate", "merge")


def is_self_contained_ddl(sql_text: str) -> bool:
    """True when ``sql_text`` already begins with its own DDL/DML statement.

    A ``SqlFile -> Table`` job normally holds a bare ``SELECT`` that we wrap in
    ``DROP/CREATE TABLE ... AS``. If the file instead already opens with
    ``CREATE``/``INSERT``/etc., wrapping it again produces invalid nested DDL,
    so callers should write/preview it verbatim. Leading ``--`` line comments
    and ``/* ... */`` block comments are skipped before inspecting the first
    keyword; a leading ``WITH`` CTE is treated as a SELECT (wrappable).
    """
    remaining = sql_text.lstrip()
    while remaining:
        if remaining.startswith("--"):
            _, _, remaining = remaining.partition("\n")
            remaining = remaining.lstrip()
        elif remaining.startswith("/*"):
            _, _, remaining = remaining.partition("*/")
            remaining = remaining.lstrip()
        else:
            break
    first = remaining[:16].lower()
    return any(first.startswith(leader) for leader in _DDL_LEADERS)


def table_wrapper(sql_text: str, schema: str, table_name: str, user: str) -> str:
    prefix = schema.split("_", 1)[0]
    full_table = f"{schema}.{table_name}"
    return (
        f"DROP TABLE IF EXISTS {full_table};\n"
        f"CREATE TABLE {full_table}\n"
        "STORED AS PARQUET\n"
        f"LOCATION '/das/{prefix}/enc/{user}/{table_name}'\n"
        "AS\n"
        f"{sql_text.strip()}\n"
    )


def month_range(start: date, end: date) -> list[date]:
    months = []
    current = start.replace(day=1)
    while current <= end:
        months.append(current)
        year = current.year + (current.month // 12)
        month = (current.month % 12) + 1
        current = current.replace(year=year, month=month)
    return months


def monthly_preview(
    sql_template: str, schema: str, table_name: str, start_iso: str, end_iso: str
) -> str:
    if DATE_INICIO_TOKEN not in sql_template or DATE_FIM_TOKEN not in sql_template:
        raise ValueError("Monthly SQL template must include {date_inicio} and {date_fim} tokens.")
    start = datetime.strptime(start_iso, "%Y-%m-%d").date()
    end = datetime.strptime(end_iso, "%Y-%m-%d").date()
    # Metadata lines are SQL comments so the preview tokenizes cleanly.
    lines = [f"-- Monthly partitions for {schema}.{table_name}:"]
    for month in month_range(start, end):
        last_day = calendar.monthrange(month.year, month.month)[1]
        month_end = month.replace(day=last_day)
        dt_ano_mes = month.strftime("%Y%m")
        resolved = (
            sql_template.replace(DATE_INICIO_TOKEN, str(month))
            .replace(DATE_FIM_TOKEN, str(month_end))
            .strip()
        )
        lines.extend(
            [
                "",
                f"-- {schema}.{table_name}_temp_{dt_ano_mes}",
                f"-- date_inicio={month}  date_fim={month_end}",
                resolved,
            ]
        )
    return "\n".join(lines)


def to_orchestrator_date(iso_date: str) -> str:
    parsed = datetime.strptime(iso_date, "%Y-%m-%d")
    return parsed.strftime("%m/%d/%Y")


def from_orchestrator_date(orchestrator_date: str) -> str:
    """Inverse of :func:`to_orchestrator_date`: ``MM/DD/YYYY`` -> ``YYYY-MM-DD``.

    Returns the input unchanged when it is not in the expected orchestrator
    format, so clone prefill degrades gracefully on hand-edited manifests.
    """
    try:
        return datetime.strptime(orchestrator_date, "%m/%d/%Y").strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return orchestrator_date


def validate_date_range(start_iso: str, end_iso: str) -> str | None:
    """Return an error message for a bad template date range, else ``None``.

    Guards the ``SqlTemplate`` launch/preview path, where unchecked input is
    fed to ``datetime.strptime`` and would otherwise raise mid-flight.
    """
    try:
        start = datetime.strptime(start_iso, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return "Start date must be YYYY-MM-DD"
    try:
        end = datetime.strptime(end_iso, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return "End date must be YYYY-MM-DD"
    if start > end:
        return "Start date must not be after end date"
    return None
