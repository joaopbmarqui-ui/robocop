"""Focused argv-boundary tests for the stdlib-only production orchestrators."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

SCR_DIR = Path(__file__).resolve().parents[1] / "scr"
if str(SCR_DIR) not in sys.path:
    sys.path.insert(0, str(SCR_DIR))

import _common  # noqa: E402
import download_to_csv  # noqa: E402
import monthly_query_processor  # noqa: E402


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("dispatch_smoke_1", True),
        ("", False),
        ("bad-name", False),
        ("t;drop", False),
        ("schema.table", False),
    ],
)
def test_validate_identifier_accepts_only_plain_names(value: str, expected: bool) -> None:
    assert _common.validate_identifier(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("aa_enc.dispatch_smoke_1", True),
        ("", False),
        ("schema.table.extra", False),
        ("schema.bad-name", False),
        ("schema.t;drop", False),
    ],
)
def test_validate_full_table_requires_exact_schema_and_table(
    value: str, expected: bool
) -> None:
    assert _common.validate_full_table(value) is expected


def test_download_table_mode_rejects_unsafe_full_table_before_retry(
    monkeypatch, capsys
) -> None:
    retry_calls: list[str] = []
    monkeypatch.setattr(
        download_to_csv,
        "retry_loop",
        lambda query, _output, _queues: retry_calls.append(query),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "download_to_csv.py",
            "--table-name",
            "schema.table.extra",
            "--output-file",
            "output.csv",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        download_to_csv.main()

    assert exc_info.value.code == 2
    assert "plain Impala identifiers" in capsys.readouterr().err
    assert retry_calls == []


@pytest.mark.parametrize(
    ("flag", "unsafe_value"),
    [
        ("--schema", "bad-schema"),
        ("--table-name", "bad/name"),
        ("--user", "user;drop"),
    ],
)
def test_monthly_argv_rejects_unsafe_identifiers_before_processing(
    monkeypatch, capsys, flag: str, unsafe_value: str
) -> None:
    process_calls: list[object] = []
    argv = [
        "monthly_query_processor.py",
        "--sql-file",
        "monthly.sql",
        "--schema",
        "aa_enc",
        "--table-name",
        "dispatch_smoke_1",
        "--start-date",
        "01/01/2026",
        "--end-date",
        "02/01/2026",
        "--user",
        "e123456",
        "--to-email",
        "test@example.com",
        "--subject",
        "Smoke",
    ]
    argv[argv.index(flag) + 1] = unsafe_value
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(
        monthly_query_processor,
        "process_monthly_job",
        lambda args: process_calls.append(args),
    )

    with pytest.raises(SystemExit) as exc_info:
        monthly_query_processor.main()

    assert exc_info.value.code == 2
    assert "plain Impala identifier" in capsys.readouterr().err
    assert process_calls == []
