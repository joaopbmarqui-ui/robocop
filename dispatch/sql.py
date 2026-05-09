"""SQL detection and preview helpers."""

from __future__ import annotations

import calendar
from datetime import date, datetime


def detect_source(sql_text: str) -> str:
    has_start = "{date_inicio}" in sql_text
    has_end = "{date_fim}" in sql_text
    return "SqlTemplate" if has_start and has_end else "SqlFile"


def template_is_complete(sql_text: str) -> bool:
    return "{date_inicio}" in sql_text and "{date_fim}" in sql_text


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


def monthly_preview(sql_template: str, schema: str, table_name: str, start_iso: str, end_iso: str) -> str:
    start = datetime.strptime(start_iso, "%Y-%m-%d").date()
    end = datetime.strptime(end_iso, "%Y-%m-%d").date()
    lines = [f"Monthly partitions for {schema}.{table_name}:"]
    for month in month_range(start, end):
        last_day = calendar.monthrange(month.year, month.month)[1]
        month_end = month.replace(day=last_day)
        dt_ano_mes = month.strftime("%Y%m")
        resolved = sql_template.format(date_inicio=str(month), date_fim=str(month_end)).strip()
        lines.extend(
            [
                "",
                f"{schema}.{table_name}_temp_{dt_ano_mes}",
                f"date_inicio={month}",
                f"date_fim={month_end}",
                resolved,
            ]
        )
    return "\n".join(lines)


def to_orchestrator_date(iso_date: str) -> str:
    parsed = datetime.strptime(iso_date, "%Y-%m-%d")
    return parsed.strftime("%m/%d/%Y")
