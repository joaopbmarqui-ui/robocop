"""Focused argv-boundary tests for the stdlib-only production orchestrators."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

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
def test_validate_full_table_requires_exact_schema_and_table(value: str, expected: bool) -> None:
    assert _common.validate_full_table(value) is expected


def test_download_table_mode_rejects_unsafe_full_table_before_retry(monkeypatch, capsys) -> None:
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


def test_download_csv_main_passes_optional_email_args_to_retry(monkeypatch, tmp_path) -> None:
    query_file = tmp_path / "query.sql"
    query_file.write_text("select 1", encoding="utf-8")
    retry_calls: list[tuple[str, str, list[str], str, str]] = []
    monkeypatch.setattr(
        download_to_csv,
        "retry_loop",
        lambda query, output, queues, *, to_email="", subject="": retry_calls.append(
            (query, output, queues, to_email, subject)
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "download_to_csv.py",
            "--query-file",
            str(query_file),
            "--output-file",
            "output.csv",
            "--to-email",
            "test@example.com",
            "--subject",
            "Dispatch Export",
        ],
    )

    download_to_csv.main()

    assert retry_calls == [
        (
            "select 1",
            "output.csv",
            ["adhoc_fast", "adhoc_small", "adhoc"],
            "test@example.com",
            "Dispatch Export",
        )
    ]


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


@pytest.mark.parametrize(
    ("stderr_text", "category"),
    [
        ("Memory limit exceeded: Not enough memory available", "MEMORY_EXCEEDED"),
        ("Query timed out while fetching results", "TIMEOUT"),
        ("Admission rejected: queue is full", "QUEUE_FULL"),
        ("Could not connect to host: connection refused", "CONNECTION_ERROR"),
        ("RPC dropped due to backpressure", "BACKPRESSURE"),
        ("Name or service not known for edge-node", "HOST_RESOLUTION_ERROR"),
        ("Coordinator unreachable", "HOST_UNREACHABLE"),
        ("Disk full while writing parquet data", "DISK_FULL"),
        ("Memory available below required reservation", "MEMORY_AVAILABLE"),
        ("Scratch space limit exceeded", "SPACE_LIMIT"),
        ("AnalysisException: duplicate column name id", "DUPLICATE_COLUMN"),
        ("AuthenticationException: unable to obtain Kerberos principal", "AUTH_ERROR"),
        ("AnalysisException: could not resolve path to table: missing_table", "TABLE_NOT_FOUND"),
        ("ParseException: syntax error at line 1", "SYNTAX_ERROR"),
    ],
)
def test_impala_error_classifier_categories(stderr_text: str, category: str) -> None:
    assert _common.classificar_erro_impala(stderr_text)["categoria"] == category


def test_unmatched_stderr_maps_to_generic_error() -> None:
    assert (
        _common.classificar_erro_impala("unexpected impala stderr")["categoria"] == "GENERIC_ERROR"
    )


@pytest.mark.parametrize(
    ("stderr_text", "category"),
    [
        ("AnalysisException: could not resolve path to table: missing_table", "TABLE_NOT_FOUND"),
        ("ParseException: syntax error at line 1", "SYNTAX_ERROR"),
        ("AnalysisException: duplicate column name id", "DUPLICATE_COLUMN"),
        ("AuthenticationException: unable to obtain Kerberos principal", "AUTH_ERROR"),
        ("unexpected impala stderr", "GENERIC_ERROR"),
    ],
)
def test_fatal_error_categories_are_in_fatal_set(stderr_text: str, category: str) -> None:
    result = _common.classificar_erro_impala(stderr_text)
    assert result["categoria"] == category
    assert result["categoria"] in _common.FATAL_ERRORS


@pytest.mark.parametrize(
    "category",
    ["TABLE_NOT_FOUND", "SYNTAX_ERROR", "DUPLICATE_COLUMN", "AUTH_ERROR", "GENERIC_ERROR"],
)
def test_each_declared_fatal_error_is_pinned(category: str) -> None:
    assert category in _common.FATAL_ERRORS


DEFAULT_POOLS = ["adhoc_fast", "acs_small", "adhoc_small", "acs_large", "adhoc"]


def test_resolve_pools_defaults_when_env_unset(monkeypatch) -> None:
    monkeypatch.delenv("DISPATCH_REQUEST_POOL", raising=False)
    assert _common.resolve_pools(DEFAULT_POOLS) == DEFAULT_POOLS


def test_resolve_pools_defaults_when_env_blank(monkeypatch) -> None:
    monkeypatch.setenv("DISPATCH_REQUEST_POOL", "   ")
    assert _common.resolve_pools(DEFAULT_POOLS) == DEFAULT_POOLS


def test_resolve_pools_pins_single_selected_queue(monkeypatch) -> None:
    monkeypatch.setenv("DISPATCH_REQUEST_POOL", "acs_large")
    assert _common.resolve_pools(DEFAULT_POOLS) == ["acs_large"]


def test_resolve_pools_parses_comma_separated_list(monkeypatch) -> None:
    monkeypatch.setenv("DISPATCH_REQUEST_POOL", " adhoc_fast , adhoc ")
    assert _common.resolve_pools(DEFAULT_POOLS) == ["adhoc_fast", "adhoc"]


def test_resolve_pools_does_not_mutate_default(monkeypatch) -> None:
    monkeypatch.delenv("DISPATCH_REQUEST_POOL", raising=False)
    default = ["adhoc_fast", "adhoc"]
    result = _common.resolve_pools(default)
    result.append("mutated")
    assert default == ["adhoc_fast", "adhoc"]


def test_cycle_through_pools_propagates_unexpected_operation_errors(monkeypatch) -> None:
    failures: list[int] = []
    sleeps: list[int] = []

    monkeypatch.setattr(_common.time, "sleep", lambda seconds: sleeps.append(seconds))

    def operation(_pool: str) -> bool:
        raise RuntimeError("local subprocess startup failed")

    with pytest.raises(RuntimeError, match="local subprocess startup failed"):
        _common.cycle_through_pools(
            ["adhoc_fast"],
            operation,
            failures.append,
            retry_interval=30,
            max_cycles=1,
        )

    assert failures == []
    assert sleeps == []


def test_cycle_through_pools_raises_timeout_without_promising_unavailable_retry(
    monkeypatch,
) -> None:
    failures: list[int] = []
    sleeps: list[int] = []

    monkeypatch.setattr(_common.time, "sleep", lambda seconds: sleeps.append(seconds))

    with pytest.raises(TimeoutError, match="Retry cycle limit reached"):
        _common.cycle_through_pools(
            ["adhoc_fast"],
            lambda _pool: False,
            failures.append,
            retry_interval=30,
            max_cycles=1,
        )

    assert failures == []
    assert sleeps == []


def test_cycle_through_pools_keeps_retry_interval_between_retryable_cycles(
    monkeypatch,
) -> None:
    attempts: list[str] = []
    failures: list[int] = []
    sleeps: list[int] = []

    monkeypatch.setattr(_common.time, "sleep", lambda seconds: sleeps.append(seconds))

    def operation(pool: str) -> bool:
        attempts.append(pool)
        return False

    with pytest.raises(TimeoutError, match="Retry cycle limit reached"):
        _common.cycle_through_pools(
            ["adhoc_fast"],
            operation,
            failures.append,
            retry_interval=30,
            max_cycles=2,
        )

    assert attempts == ["adhoc_fast", "adhoc_fast"]
    assert failures == [1]
    assert sleeps == [30]


def test_download_csv_retry_loop_sends_start_notification(monkeypatch) -> None:
    sent_emails: list[tuple[str, str, str]] = []
    attempts: list[str] = []

    def fake_run_export(
        query: str, output_file: str, *, to_email: str, subject: str, queue: str
    ) -> bool:
        attempts.append(queue)
        return queue == "adhoc_small"

    monkeypatch.setattr(
        download_to_csv,
        "send_email",
        lambda body, subject, to_email: sent_emails.append((subject, body, to_email)),
    )
    monkeypatch.setattr(download_to_csv, "run_export_on_impala", fake_run_export)

    download_to_csv.retry_loop(
        "select 1",
        "output.csv",
        ["adhoc_fast", "adhoc_small"],
        to_email="test@example.com",
        subject="Dispatch Export",
    )

    assert attempts == ["adhoc_fast", "adhoc_small"]
    assert [item[0] for item in sent_emails] == [
        "Dispatch Export - PROCESSO INICIADO",
    ]
    assert all(item[2] == "test@example.com" for item in sent_emails)


def test_download_csv_run_export_sends_success_notification(monkeypatch, tmp_path) -> None:
    output_file = tmp_path / "export.csv"
    sent_emails: list[tuple[str, str, str]] = []

    class FakeProcess:
        returncode = 0

        def __init__(self, command: list[str], stdout, stderr) -> None:
            target = Path(command[command.index("-o") + 1])
            target.write_text("csv\n", encoding="utf-8")

        def communicate(self) -> tuple[bytes, bytes]:
            return b"ok", b""

    monkeypatch.setattr(download_to_csv.subprocess, "Popen", FakeProcess)
    monkeypatch.setattr(
        download_to_csv,
        "send_email",
        lambda body, subject, to_email: sent_emails.append((subject, body, to_email)),
    )

    assert download_to_csv.run_export_on_impala(
        "select 1",
        str(output_file),
        to_email="test@example.com",
        subject="Dispatch Export",
        queue="adhoc_fast",
    )

    assert sent_emails[0][0] == "Dispatch Export - PROCESSO FINALIZADO"
    assert "Status: SUCCESS" in sent_emails[0][1]
    assert sent_emails[0][2] == "test@example.com"


def test_download_csv_run_export_sends_fatal_error_notification(monkeypatch, tmp_path) -> None:
    output_file = tmp_path / "export.csv"
    sent_emails: list[tuple[str, str, str]] = []

    class FakeProcess:
        returncode = 1

        def __init__(self, command: list[str], stdout, stderr) -> None:
            pass

        def communicate(self) -> tuple[bytes, bytes]:
            return b"", b"ParseException: syntax error at line 1"

    monkeypatch.setattr(download_to_csv.subprocess, "Popen", FakeProcess)
    monkeypatch.setattr(
        download_to_csv,
        "send_email",
        lambda body, subject, to_email: sent_emails.append((subject, body, to_email)),
    )

    with pytest.raises(SystemExit) as exc_info:
        download_to_csv.run_export_on_impala(
            "select",
            str(output_file),
            to_email="test@example.com",
            subject="Dispatch Export",
            queue="adhoc_fast",
        )

    assert exc_info.value.code == 1
    assert sent_emails[0][0] == "Dispatch Export - ERRO (SYNTAX_ERROR)"
    assert "FATAL ERROR" in sent_emails[0][1]
    assert sent_emails[0][2] == "test@example.com"


def test_send_email_uses_finite_timeout_and_closes_connection(monkeypatch) -> None:
    smtp_calls: list[tuple[str, int, float]] = []
    sent: list[tuple[str, list[str], str]] = []
    closed: list[str] = []

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: float) -> None:
            smtp_calls.append((host, port, timeout))

        def sendmail(self, from_email: str, recipients: list[str], message: str) -> None:
            sent.append((from_email, recipients, message))

        def quit(self) -> None:
            closed.append("quit")

    monkeypatch.setenv("MAILHOST", "smtp.example.test:2525")
    monkeypatch.setattr(_common.smtplib, "SMTP", FakeSMTP)

    _common.send_email("body", "Subject", "a@example.com;b@example.com")

    assert smtp_calls == [("smtp.example.test", 2525, _common.SMTP_TIMEOUT_SECONDS)]
    assert sent[0][0] == "AutoQueryExecution_Analytics@mastercard.com"
    assert sent[0][1] == ["a@example.com", "b@example.com"]
    assert "Subject" in sent[0][2]
    assert closed == ["quit"]


def test_send_email_closes_connection_when_sendmail_fails(monkeypatch) -> None:
    closed: list[str] = []

    class FakeSMTP:
        def __init__(self, _host: str, _port: int, timeout: float) -> None:
            pass

        def sendmail(self, *_args: Any) -> None:
            raise OSError("relay unavailable")

        def quit(self) -> None:
            closed.append("quit")

    monkeypatch.setattr(_common.smtplib, "SMTP", FakeSMTP)

    _common.send_email("body", "Subject", "a@example.com")

    assert closed == ["quit"]
