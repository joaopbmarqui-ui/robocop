"""Tests for the New Job execution-queue selection control."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from textual.widgets import Select

from dispatch.app import DispatchApp
from dispatch.screens.new_job import _QUEUE_AUTO, NewJobScreen


def _write_sql(data_root: Path) -> Path:
    sql_path = data_root / "queue.sql"
    sql_path.write_text("SELECT 1 AS smoke_check;\n", encoding="utf-8")
    return sql_path


def test_queue_defaults_to_auto_and_stays_out_of_params(mock_env_with_config) -> None:
    """A fresh form defaults to Auto; params carry the ``auto`` sentinel."""
    data_root = Path(os.environ["DISPATCH_DATA_ROOT"])
    _write_sql(data_root)

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            app.push_screen(NewJobScreen(app.launch_cwd))
            await pilot.pause(0.5)
            screen = app.screen
            assert isinstance(screen, NewJobScreen)
            assert screen._selected_queue() == _QUEUE_AUTO
            assert screen._params()["queue"] == _QUEUE_AUTO

    asyncio.run(run())


def test_selecting_queue_flows_into_params(mock_env_with_config) -> None:
    """Choosing a specific queue is reflected in the launch params."""
    data_root = Path(os.environ["DISPATCH_DATA_ROOT"])
    _write_sql(data_root)

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            app.push_screen(NewJobScreen(app.launch_cwd))
            await pilot.pause(0.5)
            screen = app.screen
            assert isinstance(screen, NewJobScreen)
            screen.query_one("#queue", Select).value = "acs_large"
            await pilot.pause(0.1)
            assert screen._selected_queue() == "acs_large"
            assert screen._params()["queue"] == "acs_large"

    asyncio.run(run())


def test_prefill_restores_selected_queue(mock_env_with_config) -> None:
    """Re-running a job restores the queue it was launched with."""
    data_root = Path(os.environ["DISPATCH_DATA_ROOT"])
    sql_path = _write_sql(data_root)
    prefill = {
        "source_type": "SqlFile",
        "dest_type": "Csv",
        "sql_file": str(sql_path),
        "table_name": "queued_export",
        "queue": "adhoc_fast",
    }

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            app.push_screen(NewJobScreen(app.launch_cwd, prefill=prefill))
            await pilot.pause(0.5)
            screen = app.screen
            assert isinstance(screen, NewJobScreen)
            assert screen._selected_queue() == "adhoc_fast"

    asyncio.run(run())
