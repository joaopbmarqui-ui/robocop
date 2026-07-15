"""Tests for EID-prefixed table names in the New Job form."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from dispatch import config, sql
from dispatch.app import DispatchApp
from dispatch.screens.new_job import NewJobScreen


@pytest.mark.parametrize(
    ("full", "suffix"),
    [
        ("alice_dispatch_result", "dispatch_result"),
        ("dispatch_result", "dispatch_result"),
        ("alice_alice_dispatch_result", "alice_dispatch_result"),
    ],
)
def test_split_eid_table_suffix(full: str, suffix: str) -> None:
    assert sql.split_eid_table_suffix(full, "alice") == suffix


def test_join_eid_table_name() -> None:
    assert sql.join_eid_table_name("alice", "dispatch_result") == "alice_dispatch_result"


def test_validate_eid_table_name_requires_prefix() -> None:
    assert sql.validate_eid_table_name("other_dispatch", "alice") == (
        "Table name must start with alice_"
    )


def test_validate_eid_table_name_requires_suffix() -> None:
    assert sql.validate_eid_table_name("alice_", "alice") == (
        "Table name requires a suffix after alice_"
    )


def test_validate_eid_table_name_accepts_full_name() -> None:
    assert sql.validate_eid_table_name("alice_dispatch_result", "alice") is None


class TestNewJobEidTableName:
    def test_table_name_field_shows_fixed_prefix(
        self, mock_env_with_config, monkeypatch, tmp_path: Path
    ) -> None:
        sql_path = tmp_path / "query.sql"
        sql_path.write_text("SELECT 1", encoding="utf-8")
        eid = config.current_user()

        async def fake_ttl() -> int:
            return 7200

        monkeypatch.setattr("dispatch.kerberos.ticket_ttl_seconds", fake_ttl)

        async def run() -> None:
            app = DispatchApp()
            prefill = {
                "source_type": "SqlFile",
                "dest_type": "Table",
                "sql_file": str(sql_path),
                "schema": "aa_enc",
            }
            async with app.run_test(size=(140, 50)) as pilot:
                screen = NewJobScreen(tmp_path, prefill=prefill)
                app.push_screen(screen)
                await pilot.pause(0.5)

                prefix = str(screen.query_one("#table-name-prefix").render())
                assert f"{eid}_" in prefix
                assert screen._table_name_value() == f"{eid}_dispatch_result"

        asyncio.run(run())

    def test_suffix_is_editable_and_builds_full_name(
        self, mock_env_with_config, monkeypatch, tmp_path: Path
    ) -> None:
        sql_path = tmp_path / "query.sql"
        sql_path.write_text("SELECT 1", encoding="utf-8")
        eid = config.current_user()

        async def fake_ttl() -> int:
            return 7200

        monkeypatch.setattr("dispatch.kerberos.ticket_ttl_seconds", fake_ttl)

        async def run() -> None:
            app = DispatchApp()
            prefill = {
                "source_type": "SqlFile",
                "dest_type": "Table",
                "sql_file": str(sql_path),
                "schema": "aa_enc",
            }
            async with app.run_test(size=(140, 50)) as pilot:
                screen = NewJobScreen(tmp_path, prefill=prefill)
                app.push_screen(screen)
                await pilot.pause(0.5)

                screen.query_one("#table-name-suffix").value = "monthly_export"
                await pilot.pause(0.3)

                assert screen._table_name_value() == f"{eid}_monthly_export"

        asyncio.run(run())

    def test_pasted_full_name_strips_eid_prefix(
        self, mock_env_with_config, monkeypatch, tmp_path: Path
    ) -> None:
        sql_path = tmp_path / "query.sql"
        sql_path.write_text("SELECT 1", encoding="utf-8")
        eid = config.current_user()

        async def fake_ttl() -> int:
            return 7200

        monkeypatch.setattr("dispatch.kerberos.ticket_ttl_seconds", fake_ttl)

        async def run() -> None:
            app = DispatchApp()
            prefill = {
                "source_type": "SqlFile",
                "dest_type": "Table",
                "sql_file": str(sql_path),
                "schema": "aa_enc",
            }
            async with app.run_test(size=(140, 50)) as pilot:
                screen = NewJobScreen(tmp_path, prefill=prefill)
                app.push_screen(screen)
                await pilot.pause(0.5)

                screen.query_one("#table-name-suffix").value = f"{eid}_cloned_job"
                await pilot.pause(0.3)

                assert screen.query_one("#table-name-suffix").value == "cloned_job"
                assert screen._table_name_value() == f"{eid}_cloned_job"

        asyncio.run(run())

    def test_prefill_accepts_bare_table_name(
        self, mock_env_with_config, monkeypatch, tmp_path: Path
    ) -> None:
        sql_path = tmp_path / "query.sql"
        sql_path.write_text("SELECT 1", encoding="utf-8")
        eid = config.current_user()

        async def fake_ttl() -> int:
            return 7200

        monkeypatch.setattr("dispatch.kerberos.ticket_ttl_seconds", fake_ttl)

        async def run() -> None:
            app = DispatchApp()
            prefill = {
                "source_type": "SqlFile",
                "dest_type": "Table",
                "sql_file": str(sql_path),
                "schema": "aa_enc",
                "table_name": "smoke_tbl",
            }
            async with app.run_test(size=(140, 50)) as pilot:
                screen = NewJobScreen(tmp_path, prefill=prefill)
                app.push_screen(screen)
                await pilot.pause(0.5)
                assert screen.query_one("#table-name-suffix").value == "smoke_tbl"
                assert screen._table_name_value() == f"{eid}_smoke_tbl"

        asyncio.run(run())

    def test_prefill_accepts_prefixed_table_name(
        self, mock_env_with_config, monkeypatch, tmp_path: Path
    ) -> None:
        sql_path = tmp_path / "query.sql"
        sql_path.write_text("SELECT 1", encoding="utf-8")
        eid = config.current_user()

        async def fake_ttl() -> int:
            return 7200

        monkeypatch.setattr("dispatch.kerberos.ticket_ttl_seconds", fake_ttl)

        async def run() -> None:
            app = DispatchApp()
            prefill = {
                "source_type": "SqlFile",
                "dest_type": "Table",
                "sql_file": str(sql_path),
                "schema": "aa_enc",
                "table_name": f"{eid}_smoke_tbl",
            }
            async with app.run_test(size=(140, 50)) as pilot:
                screen = NewJobScreen(tmp_path, prefill=prefill)
                app.push_screen(screen)
                await pilot.pause(0.5)
                assert screen.query_one("#table-name-suffix").value == "smoke_tbl"
                assert screen._table_name_value() == f"{eid}_smoke_tbl"

        asyncio.run(run())

    def test_csv_only_destination_keeps_bare_suffix_for_csv_path(
        self, mock_env_with_config, monkeypatch, tmp_path: Path
    ) -> None:
        sql_path = tmp_path / "query.sql"
        sql_path.write_text("SELECT 1", encoding="utf-8")

        async def fake_ttl() -> int:
            return 7200

        monkeypatch.setattr("dispatch.kerberos.ticket_ttl_seconds", fake_ttl)

        async def run() -> None:
            app = DispatchApp()
            prefill = {
                "source_type": "SqlFile",
                "dest_type": "Csv",
                "sql_file": str(sql_path),
            }
            async with app.run_test(size=(140, 50)) as pilot:
                screen = NewJobScreen(tmp_path, prefill=prefill)
                app.push_screen(screen)
                await pilot.pause(0.5)

                assert screen.query_one("#row-table-name").display is False
                assert screen._table_name_value() == "dispatch_result"

        asyncio.run(run())

    def test_table_destination_rejects_invalid_suffix(
        self, mock_env_with_config, monkeypatch, tmp_path: Path
    ) -> None:
        sql_path = tmp_path / "query.sql"
        sql_path.write_text("SELECT 1", encoding="utf-8")

        async def fake_ttl() -> int:
            return 7200

        monkeypatch.setattr("dispatch.kerberos.ticket_ttl_seconds", fake_ttl)

        async def run() -> None:
            app = DispatchApp()
            prefill = {
                "source_type": "SqlFile",
                "dest_type": "Table+Csv",
                "sql_file": str(sql_path),
                "schema": "aa_enc",
                "table_name": "../escape",
            }
            async with app.run_test(size=(140, 50)) as pilot:
                screen = NewJobScreen(tmp_path, prefill=prefill)
                app.push_screen(screen)
                await pilot.pause(0.5)

                issues = screen._validation_issues()
                assert any("suffix" in issue.lower() for issue in issues)

        asyncio.run(run())
