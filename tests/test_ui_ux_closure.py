"""Focused UI/UX closure tests for high-risk screenshot review findings."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from textual.widgets import Input

from dispatch import manifest
from dispatch.app import DispatchApp
from dispatch.screens.browser import BrowserScreen
from dispatch.screens.history import PAGE_SIZE, HistoryScreen
from dispatch.screens.job_detail import JobDetailScreen


def _seed_history_job(jobs_dir: Path, index: int) -> str:
    job_id = f"20260401T10{index:04d}00Z_hist{index:02d}"
    job_dir = jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    data: manifest.JobManifest = {
        "schema_version": 1,
        "id": job_id,
        "tool": "dispatch",
        "user": "testuser",
        "source": {"type": "SqlFile", "sql_path_at_launch": f"/tmp/query_{index}.sql"},
        "destination": {
            "type": "Csv",
            "schema": "dw_settle",
            "table_name": f"history_{index}",
            "csv_path": f"/tmp/history_{index}.csv",
        },
        "params": {},
        "orchestrator_calls": [{"script": "download_to_csv.py", "argv": ["python3", "x.py"]}],
        "state": "Succeeded",
        "pid": None,
        "started_at": "2026-04-01T10:00:00Z",
        "finished_at": "2026-04-01T10:05:00Z",
        "exit_code": 0,
    }
    manifest.write(job_dir / "manifest.json", data)
    return job_id


def test_history_pagination_keys_move_between_pages(mock_env_with_config) -> None:
    """History next/previous bindings move the visible page for large histories."""
    data_root = Path(os.environ["DISPATCH_DATA_ROOT"])
    jobs_dir = data_root / ".dispatch" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    for index in range(PAGE_SIZE + 3):
        _seed_history_job(jobs_dir, index)

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = HistoryScreen()
            app.push_screen(screen)
            await pilot.pause()

            page_info = screen.query_one("#page-info")
            page_controls = screen.query_one("#page-controls")
            assert "Showing 1-17 of 20" in str(page_info.render())
            assert "Page 1 of 2" in str(page_controls.render())

            await pilot.press("]")
            await pilot.pause()
            assert "Showing 18-20 of 20" in str(page_info.render())
            assert "Page 2 of 2" in str(page_controls.render())

            await pilot.press("[")
            await pilot.pause()
            assert "Showing 1-17 of 20" in str(page_info.render())
            assert "Page 1 of 2" in str(page_controls.render())

    asyncio.run(run())


def test_history_enter_opens_full_job_id_not_truncated_value(
    mock_env_with_config,
) -> None:
    """Enter on a history row opens the full durable row key, not the visible ID."""
    data_root = Path(os.environ["DISPATCH_DATA_ROOT"])
    jobs_dir = data_root / ".dispatch" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_id = _seed_history_job(jobs_dir, 12345)
    assert len(job_id) > 24

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = HistoryScreen()
            app.push_screen(screen)
            await pilot.pause()

            screen.action_view_logs()
            await pilot.pause()
            assert isinstance(app.screen, JobDetailScreen)
            assert app.screen.job_id == job_id

    asyncio.run(run())


def test_browser_placeholder_and_auto_describe_after_show_tables(
    mock_env_with_config, monkeypatch
) -> None:
    """Browser explains the empty detail pane and fills it after loading tables."""

    async def fake_show_tables(schema: str, pattern: str = "*") -> list[str]:
        return ["dispatch_result", "dispatch_archive"]

    async def fake_describe_table(full_table: str) -> str:
        return "name|type|comment\nid|string|primary key"

    monkeypatch.setattr("dispatch.impala.show_tables", fake_show_tables)
    monkeypatch.setattr("dispatch.impala.describe_table", fake_describe_table)

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = BrowserScreen()
            app.push_screen(screen)
            await pilot.pause()

            body = screen.query_one("#describe-body")
            assert "Select a table and press Enter" in str(body.render())

            await screen.action_show_tables()
            await pilot.pause()
            assert "dw_settle.dispatch_result" in str(
                screen.query_one("#file-preview-title").render()
            )
            assert "id" in str(body.render())

    asyncio.run(run())


def test_browser_drop_requires_typing_full_table_name(
    mock_env_with_config, monkeypatch
) -> None:
    """DROP confirmation requires the fully-qualified table name, not just Y."""
    calls: list[str] = []

    async def fake_drop_table(full_table: str) -> str:
        calls.append(full_table)
        return f"Dropped {full_table}"

    monkeypatch.setattr("dispatch.impala.drop_table", fake_drop_table)

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = BrowserScreen()
            app.push_screen(screen)
            await pilot.pause()
            table = screen.query_one("#browser-table")
            table.add_row("danger_table", "table")

            task = asyncio.create_task(screen.action_drop())
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            assert calls == []
            assert not task.done()

            confirm_input = app.screen.query_one("#confirm-input", Input)
            confirm_input.value = "dw_settle.danger_table"
            await pilot.press("enter")
            await task
            assert calls == ["dw_settle.danger_table"]

    asyncio.run(run())


def test_typed_drop_confirmation_button_does_not_bypass_input(
    mock_env_with_config, monkeypatch
) -> None:
    """Clicking the danger button still requires the exact typed table name."""
    calls: list[str] = []

    async def fake_drop_table(full_table: str) -> str:
        calls.append(full_table)
        return f"Dropped {full_table}"

    monkeypatch.setattr("dispatch.impala.drop_table", fake_drop_table)

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = BrowserScreen()
            app.push_screen(screen)
            await pilot.pause()
            table = screen.query_one("#browser-table")
            table.add_row("danger_table", "table")

            task = asyncio.create_task(screen.action_drop())
            await pilot.pause()
            app.screen.query_one("#confirm-yes").press()
            await pilot.pause()
            assert calls == []
            assert not task.done()

            app.screen.query_one("#confirm-input", Input).value = "dw_settle.danger_table"
            app.screen.query_one("#confirm-yes").press()
            await task
            assert calls == ["dw_settle.danger_table"]

    asyncio.run(run())
