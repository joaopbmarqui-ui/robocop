"""Textual Pilot tests for the Query Optimization Advisor surfaces."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from textual.widgets import Static

from dispatch.app import DispatchApp
from dispatch.screens.advisor_gate import AdvisorLaunchGate
from dispatch.screens.confirm import ConfirmScreen
from dispatch.screens.new_job import NewJobScreen
from dispatch.screens.preview import PreviewScreen


def _user() -> str:
    return os.environ.get("USER") or "testuser"


def _prefill(sql_path: Path, table_name: str | None = None) -> dict:
    user = _user()
    return {
        "source_type": "SqlFile",
        "dest_type": "Table",
        "sql_file": str(sql_path),
        "schema": "aa_enc",
        "table_name": table_name or f"{user}_result",
        "email": "test@example.com",
    }


def test_new_job_badge_clean(mock_env_with_config, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("USER", "alice")
    sql_path = tmp_path / "clean.sql"
    sql_path.write_text(
        "SELECT id FROM my_temp WHERE dw_process_date = '2024-01-01'\n",
        encoding="utf-8",
    )

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            app.push_screen(NewJobScreen(tmp_path, prefill=_prefill(sql_path)))
            await pilot.pause(0.8)
            summary = str(app.screen.query_one("#validation-summary", Static).render())
            assert "Advisor: clean" in summary
            assert "Ready to launch" in summary

    asyncio.run(run())


def test_new_job_badge_shows_error_counts(mock_env_with_config, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("USER", "alice")
    sql_path = tmp_path / "errors.sql"
    sql_path.write_text(
        "SELECT * FROM core.cut_clear_dtl_enc\n",
        encoding="utf-8",
    )

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            app.push_screen(NewJobScreen(tmp_path, prefill=_prefill(sql_path)))
            await pilot.pause(0.8)
            summary = str(app.screen.query_one("#validation-summary", Static).render())
            assert "Advisor: error" in summary
            assert "error" in summary.lower()

    asyncio.run(run())


def test_preview_findings_panel(mock_env_with_config, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("USER", "alice")
    sql_path = tmp_path / "preview.sql"
    sql_path.write_text(
        """
        SELECT a.id FROM my_temp a
        JOIN [BROADCAST] core.cut_clear_dtl_enc c ON a.id = c.dw_acct_id
        WHERE a.name REGEXP '^x'
        """,
        encoding="utf-8",
    )

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            app.push_screen(NewJobScreen(tmp_path, prefill=_prefill(sql_path)))
            await pilot.pause(0.8)
            await pilot.press("p")
            await pilot.pause(0.5)
            assert isinstance(app.screen, PreviewScreen)
            body = str(app.screen.query_one("#findings-body", Static).render())
            assert "R07" in body
            status = str(app.screen.query_one("#preview-status", Static).render())
            assert "Advisor:" in status

    asyncio.run(run())


def test_launch_gate_appears_only_for_errors(mock_env_with_config, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("USER", "alice")
    monkeypatch.setenv("DISPATCH_MOCK_KLIST_TTL", "3600")
    sql_path = tmp_path / "gate.sql"
    sql_path.write_text(
        "SELECT * FROM core.cut_clear_dtl_enc\n",
        encoding="utf-8",
    )

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = NewJobScreen(tmp_path, prefill=_prefill(sql_path))
            app.push_screen(screen)
            await pilot.pause(0.8)
            # Ensure kerberos looks valid for launch validation.
            screen.kerberos_ttl = 3600
            screen._update_validation_summary()
            await pilot.press("l")
            await pilot.pause(0.5)
            assert isinstance(app.screen, AdvisorLaunchGate)
            title = str(app.screen.query_one("#confirm-title", Static).render())
            assert "error findings" in title.lower()
            # The gate replaces the standard confirm, so it must carry the
            # Launch Job summary (target table, destination) itself.
            body = str(app.screen.query_one("#confirm-body", Static).render())
            assert "Target table:" in body
            assert "aa_enc" in body

    asyncio.run(run())


def test_launch_gate_cancel_on_escape(mock_env_with_config, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("USER", "alice")
    sql_path = tmp_path / "gate_cancel.sql"
    sql_path.write_text(
        "SELECT * FROM core.cut_clear_dtl_enc\n",
        encoding="utf-8",
    )

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = NewJobScreen(tmp_path, prefill=_prefill(sql_path))
            app.push_screen(screen)
            await pilot.pause(0.8)
            screen.kerberos_ttl = 3600
            await pilot.press("l")
            await pilot.pause(0.5)
            assert isinstance(app.screen, AdvisorLaunchGate)
            await pilot.press("escape")
            await pilot.pause(0.5)
            assert isinstance(app.screen, NewJobScreen)

    asyncio.run(run())


def test_launch_gate_proceed_on_confirm(mock_env_with_config, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("USER", "alice")
    sql_path = tmp_path / "gate_ok.sql"
    sql_path.write_text(
        "SELECT * FROM core.cut_clear_dtl_enc\n",
        encoding="utf-8",
    )
    launched: list[Path] = []

    async def fake_launch(job_dir: Path) -> None:
        launched.append(job_dir)

    async def run() -> None:
        from dispatch import process

        monkeypatch.setattr(process, "launch_runner", fake_launch)
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = NewJobScreen(tmp_path, prefill=_prefill(sql_path))
            app.push_screen(screen)
            await pilot.pause(0.8)
            screen.kerberos_ttl = 3600
            await pilot.press("l")
            await pilot.pause(0.5)
            assert isinstance(app.screen, AdvisorLaunchGate)
            await pilot.press("y")
            await pilot.pause(1.0)
            assert launched, "proceed should continue into launch"

    asyncio.run(run())


def test_no_gate_when_analysis_unavailable(mock_env_with_config, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("USER", "alice")
    sql_path = tmp_path / "bad.sql"
    sql_path.write_text("SELECT FROM WHERE\n", encoding="utf-8")

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = NewJobScreen(tmp_path, prefill=_prefill(sql_path))
            app.push_screen(screen)
            await pilot.pause(0.8)
            screen.kerberos_ttl = 3600
            summary = str(screen.query_one("#validation-summary", Static).render())
            assert "unavailable" in summary.lower() or "Advisor:" in summary
            await pilot.press("l")
            await pilot.pause(0.5)
            # Should get the normal Launch Job confirm, not the advisor gate.
            assert isinstance(app.screen, ConfirmScreen)
            assert not isinstance(app.screen, AdvisorLaunchGate)

    asyncio.run(run())


def test_advisory_only_uses_normal_confirm(mock_env_with_config, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("USER", "alice")
    sql_path = tmp_path / "warn.sql"
    sql_path.write_text(
        "SELECT id FROM core.cut_clear_dtl_enc WHERE merchant_name = 'x'\n",
        encoding="utf-8",
    )

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = NewJobScreen(tmp_path, prefill=_prefill(sql_path))
            app.push_screen(screen)
            await pilot.pause(0.8)
            screen.kerberos_ttl = 3600
            summary = str(screen.query_one("#validation-summary", Static).render())
            assert "Advisor: warning" in summary
            await pilot.press("l")
            await pilot.pause(0.5)
            assert isinstance(app.screen, ConfirmScreen)
            assert not isinstance(app.screen, AdvisorLaunchGate)

    asyncio.run(run())
