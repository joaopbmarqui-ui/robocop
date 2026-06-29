"""Regression tests for the production monthly Impala orchestrator."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

import pytest

SCR_DIR = Path(__file__).resolve().parents[1] / "scr"
if str(SCR_DIR) not in sys.path:
    sys.path.insert(0, str(SCR_DIR))

import monthly_query_processor as monthly  # noqa: E402

from dispatch import sql as dispatch_sql  # noqa: E402


def _args(tmp_path: Path) -> Namespace:
    sql_file = tmp_path / "monthly.sql"
    sql_file.write_text(
        "SELECT '{date_inicio}' AS start_dt, '{date_fim}' AS end_dt",
        encoding="utf-8",
    )
    return Namespace(
        sql_file=str(sql_file),
        schema="aa_enc",
        table_name="dispatch_smoke",
        start_date="05/01/2026",
        end_date="06/01/2026",
        user="e123456",
        to_email="tester@example.com",
        subject="Dispatch smoke",
    )


def test_build_monthly_job_query_keeps_temp_join_and_cleanup_in_one_script(tmp_path: Path) -> None:
    args = _args(tmp_path)
    sql_template = Path(args.sql_file).read_text(encoding="utf-8")

    query, temp_tables, final_table = monthly.build_monthly_job_query(args, sql_template)

    assert temp_tables == [
        "aa_enc.dispatch_smoke_temp_202605",
        "aa_enc.dispatch_smoke_temp_202606",
    ]
    assert final_table == "aa_enc.dispatch_smoke_fulljoin"
    assert query.count("CREATE TABLE aa_enc.dispatch_smoke_temp_") == 2
    assert "SELECT '2026-05-01' AS start_dt, '2026-05-31' AS end_dt" in query
    assert "SELECT '2026-06-01' AS start_dt, '2026-06-30' AS end_dt" in query
    assert "CREATE TABLE aa_enc.dispatch_smoke_fulljoin" in query
    assert (
        "SELECT * FROM aa_enc.dispatch_smoke_temp_202605\nUNION ALL\nSELECT * FROM aa_enc.dispatch_smoke_temp_202606"
        in query
    )
    assert query.rfind("DROP TABLE IF EXISTS aa_enc.dispatch_smoke_temp_202605") > query.find(
        "CREATE TABLE aa_enc.dispatch_smoke_fulljoin"
    )
    assert "/das/aa/enc/e123456/dispatch_smoke_temp_202605" in query


def test_process_monthly_job_invokes_impala_once_for_whole_job(tmp_path: Path, monkeypatch) -> None:
    args = _args(tmp_path)
    sent_emails = []
    executed = []

    monkeypatch.setattr(
        monthly,
        "send_email",
        lambda body, subject, to_email: sent_emails.append((subject, body, to_email)),
    )
    monkeypatch.setattr(
        monthly,
        "execute_step_with_retry",
        lambda query, operation_desc, args: executed.append((query, operation_desc)),
    )

    monthly.process_monthly_job(args)

    assert len(executed) == 1
    query, operation_desc = executed[0]
    assert operation_desc == "Monthly partitioned job aa_enc.dispatch_smoke_fulljoin"
    assert "CREATE TABLE aa_enc.dispatch_smoke_temp_202605" in query
    assert "CREATE TABLE aa_enc.dispatch_smoke_fulljoin" in query
    assert "All SQL statements will run in one Impala shell session" in sent_emails[0][1]
    assert sent_emails[-1][0] == "Dispatch smoke - Job Finished"


@pytest.mark.parametrize(
    "sql_template",
    [
        "SELECT '{date_inicio}' AS start_dt",
        "SELECT '{date_fim}' AS end_dt",
    ],
)
def test_build_monthly_job_query_requires_both_date_tokens(
    tmp_path: Path, sql_template: str
) -> None:
    args = _args(tmp_path)

    with pytest.raises(ValueError, match=r"\{date_inicio\}.*\{date_fim\}"):
        monthly.build_monthly_job_query(args, sql_template)


def test_build_monthly_job_query_preserves_unrelated_literal_braces(tmp_path: Path) -> None:
    args = _args(tmp_path)
    sql_template = (
        "SELECT regexp_extract(code, '^[A-Z]{2}[0-9]{4}$') AS code, "
        "'{date_inicio}' AS start_dt, '{date_fim}' AS end_dt"
    )

    query, _temp_tables, _final_table = monthly.build_monthly_job_query(args, sql_template)

    assert "regexp_extract(code, '^[A-Z]{2}[0-9]{4}$')" in query
    assert "'2026-05-01' AS start_dt, '2026-05-31' AS end_dt" in query


def test_dispatch_monthly_preview_uses_exact_token_substitution() -> None:
    sql_template = (
        "SELECT regexp_extract(code, '^[A-Z]{2}[0-9]{4}$') AS code, "
        "'{date_inicio}' AS start_dt, '{date_fim}' AS end_dt"
    )

    preview = dispatch_sql.monthly_preview(
        sql_template,
        "aa_enc",
        "dispatch_smoke",
        "2026-05-01",
        "2026-05-01",
    )

    assert "regexp_extract(code, '^[A-Z]{2}[0-9]{4}$')" in preview
    assert "'2026-05-01' AS start_dt, '2026-05-31' AS end_dt" in preview
