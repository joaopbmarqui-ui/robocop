"""Tests for features added in Phase 2-4 hardening."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest

from dispatch import config, manifest
from dispatch.app import DispatchApp
from dispatch.screens.browser import BrowserScreen
from dispatch.screens.dashboard import DashboardScreen
from dispatch.screens.help import HelpScreen
from dispatch.screens.history import HistoryScreen
from dispatch.screens.job_detail import JobDetailScreen
from dispatch.screens.new_job import NewJobScreen
from dispatch.screens.preview import PreviewScreen, _highlight_sql, _numbered_sql


# =============================================================================
# Preview SQL highlighting and scrolling
# =============================================================================

class TestPreviewHighlighting:
    def test_sql_keywords_get_markup(self) -> None:
        line = "SELECT id FROM users WHERE active = 1"
        result = _highlight_sql(line)
        assert "[bold cyan]SELECT[/]" in result
        assert "[bold cyan]FROM[/]" in result
        assert "[bold cyan]WHERE[/]" in result

    def test_non_keywords_unchanged(self) -> None:
        line = "id name email"
        result = _highlight_sql(line)
        assert result == "id name email"

    def test_numbered_sql_adds_line_numbers(self) -> None:
        body = "SELECT 1\nFROM dual"
        lines = _numbered_sql(body)
        assert len(lines) == 2
        assert "1" in lines[0]
        assert "2" in lines[1]


# =============================================================================
# Browser DESCRIBE parsing
# =============================================================================

class TestBrowserDescribeParsing:
    def test_parse_describe_pipe_delimited(self) -> None:
        raw = "id|string|primary key\nname|varchar|user name\nage|int|"
        columns = BrowserScreen._parse_describe(raw)
        assert len(columns) == 3
        assert columns[0] == {"name": "id", "type": "string", "comment": "primary key"}
        assert columns[1]["name"] == "name"
        assert columns[2]["comment"] == ""

    def test_parse_describe_empty_input(self) -> None:
        assert BrowserScreen._parse_describe("") == []

    def test_parse_describe_skips_comments(self) -> None:
        raw = "# Header line\nid|int|pk"
        columns = BrowserScreen._parse_describe(raw)
        assert len(columns) == 1


# =============================================================================
# Job Detail elapsed time
# =============================================================================

class TestJobDetailElapsed:
    def test_format_elapsed_running_job(self) -> None:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        started = (now - __import__("datetime").timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        item = {"state": "Running", "started_at": started}
        result = JobDetailScreen._format_elapsed(item)
        assert "5m" in result or "4m" in result

    def test_format_elapsed_no_started_at(self) -> None:
        item = {"state": "Running", "started_at": None}
        assert JobDetailScreen._format_elapsed(item) == "--"

    def test_format_elapsed_succeeded_job(self) -> None:
        item = {
            "state": "Succeeded",
            "started_at": "2026-05-16T10:00:00Z",
            "finished_at": "2026-05-16T10:45:00Z",
        }
        result = JobDetailScreen._format_elapsed(item)
        assert "45m" in result

    def test_style_log_line_dims_timestamp(self) -> None:
        line = "[2026-05-16 10:00:00] Starting job"
        styled = JobDetailScreen._style_log_line(line)
        assert "[dim]" in styled
        assert "Starting job" in styled

    def test_style_log_line_no_timestamp_unchanged(self) -> None:
        line = "plain log line"
        assert JobDetailScreen._style_log_line(line) == "plain log line"


# =============================================================================
# Config form defaults persistence
# =============================================================================

class TestFormDefaults:
    def test_read_form_defaults_missing_file(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("DISPATCH_DATA_ROOT", str(tmp_path))
        result = config.read_form_defaults()
        assert result == {}

    def test_save_and_read_form_defaults(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("DISPATCH_DATA_ROOT", str(tmp_path))
        dispatch_home = tmp_path / ".dispatch"
        dispatch_home.mkdir(parents=True)
        (dispatch_home / "config.json").write_text("{}", encoding="utf-8")

        config.save_form_defaults({"schema": "dw_test", "email": "a@b.com"})
        result = config.read_form_defaults()
        assert result["schema"] == "dw_test"
        assert result["email"] == "a@b.com"

    def test_save_form_defaults_preserves_existing_config(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("DISPATCH_DATA_ROOT", str(tmp_path))
        dispatch_home = tmp_path / ".dispatch"
        dispatch_home.mkdir(parents=True)
        (dispatch_home / "config.json").write_text(
            json.dumps({"to_email": "existing@example.com"}),
            encoding="utf-8",
        )

        config.save_form_defaults({"schema": "dw_new"})
        cfg = config.read_config()
        assert cfg["to_email"] == "existing@example.com"
        assert cfg["form_defaults"]["schema"] == "dw_new"


# =============================================================================
# Kerberos graceful handling
# =============================================================================

class TestKerberosGraceful:
    def test_parse_ttl_garbage_returns_none(self) -> None:
        from dispatch.kerberos import parse_ttl_seconds
        assert parse_ttl_seconds("completely invalid") is None

    def test_parse_ttl_empty_returns_none(self) -> None:
        from dispatch.kerberos import parse_ttl_seconds
        assert parse_ttl_seconds("") is None


# =============================================================================
# Dashboard display ID
# =============================================================================

class TestDashboardDisplayId:
    def test_display_id_strips_date_prefix(self) -> None:
        job_id = "20260516T100000Z_aabbcc"
        result = DashboardScreen._display_id(job_id)
        assert "aabbcc" in result
        assert "20260516" not in result

    def test_display_id_short_id_unchanged(self) -> None:
        assert DashboardScreen._display_id("short") == "short"


# =============================================================================
# Help screen
# =============================================================================

class TestHelpScreen:
    def test_help_screen_renders(self) -> None:
        async def run() -> None:
            app = DispatchApp()
            async with app.run_test(size=(100, 40)) as pilot:
                app.push_screen(HelpScreen())
                await pilot.pause()
                body = app.screen.query_one("#help-body")
                text = str(body.render())
                assert "Dashboard" in text
                assert "New Job" in text
                assert "Browser" in text

        asyncio.run(run())


# =============================================================================
# New Job Kerberos launch gating
# =============================================================================

class TestNewJobKerberosGating:
    def test_launch_button_disabled_when_kerberos_missing(
        self, mock_env_with_config, monkeypatch
    ) -> None:
        async def fake_ttl() -> None:
            return None

        monkeypatch.setattr("dispatch.kerberos.ticket_ttl_seconds", fake_ttl)

        async def run() -> None:
            app = DispatchApp()
            async with app.run_test(size=(140, 50)) as pilot:
                screen = NewJobScreen(Path.cwd())
                app.push_screen(screen)
                await pilot.pause()
                launch_btn = screen.query_one("#launch")
                assert launch_btn.disabled is True

        asyncio.run(run())

    def test_launch_button_enabled_when_kerberos_healthy(
        self, mock_env_with_config, monkeypatch
    ) -> None:
        async def fake_ttl() -> int:
            return 7200

        monkeypatch.setattr("dispatch.kerberos.ticket_ttl_seconds", fake_ttl)

        async def run() -> None:
            app = DispatchApp()
            async with app.run_test(size=(140, 50)) as pilot:
                screen = NewJobScreen(Path.cwd())
                app.push_screen(screen)
                await pilot.pause()
                launch_btn = screen.query_one("#launch")
                assert launch_btn.disabled is False

        asyncio.run(run())


# =============================================================================
# New Job inline validation
# =============================================================================

class TestNewJobInlineValidation:
    def test_inline_validation_shows_kerberos_status(
        self, mock_env_with_config, monkeypatch
    ) -> None:
        async def fake_ttl() -> int:
            return 7200

        monkeypatch.setattr("dispatch.kerberos.ticket_ttl_seconds", fake_ttl)

        async def run() -> None:
            app = DispatchApp()
            async with app.run_test(size=(140, 50)) as pilot:
                screen = NewJobScreen(Path.cwd())
                app.push_screen(screen)
                await pilot.pause()
                warning = str(screen.query_one("#warning-text").render())
                assert "Kerberos" in warning

        asyncio.run(run())


# =============================================================================
# Preview screen
# =============================================================================

class TestPreviewScreen:
    def test_preview_stores_source_and_dest_types(self) -> None:
        screen = PreviewScreen(
            "SQL Preview", "SELECT 1",
            schema="dw", table="result",
            source_type="SqlFile", dest_type="Table",
        )
        assert screen.source_type == "SqlFile"
        assert screen.dest_type == "Table"

    def test_preview_body_is_scrollable_richlog(self) -> None:
        from textual.widgets import RichLog

        async def run() -> None:
            app = DispatchApp()
            async with app.run_test(size=(120, 40)) as pilot:
                screen = PreviewScreen("Test", "SELECT 1\n" * 100, schema="dw", table="t")
                app.push_screen(screen)
                await pilot.pause()
                log = screen.query_one("#preview-body", RichLog)
                assert log is not None

        asyncio.run(run())
