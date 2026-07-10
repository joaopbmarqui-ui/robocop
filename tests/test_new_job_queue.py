"""Tests for the New Job execution-queue selection control (multi-select)."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from textual.widgets import SelectionList

from dispatch.app import DispatchApp
from dispatch.screens.new_job import _QUEUE_AUTO, NewJobScreen


def _write_sql(data_root: Path) -> Path:
    sql_path = data_root / "queue.sql"
    sql_path.write_text("SELECT 1 AS smoke_check;\n", encoding="utf-8")
    return sql_path


def test_queue_defaults_to_auto_when_nothing_selected(mock_env_with_config) -> None:
    """A fresh form selects no queue; params carry the ``auto`` sentinel."""
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
            assert screen._selected_queues() == []
            assert screen._params()["queue"] == _QUEUE_AUTO

    asyncio.run(run())


def test_selecting_single_queue_flows_into_params(mock_env_with_config) -> None:
    """Choosing one queue is reflected in the launch params."""
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
            screen.query_one("#queue", SelectionList).select("acs_large")
            await pilot.pause(0.1)
            assert screen._selected_queues() == ["acs_large"]
            assert screen._params()["queue"] == "acs_large"

    asyncio.run(run())


def test_selecting_multiple_queues_serialises_in_priority_order(mock_env_with_config) -> None:
    """Multiple queues are allowed and normalised to display (priority) order."""
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
            selection = screen.query_one("#queue", SelectionList)
            # Toggle out of display order to prove deterministic normalisation.
            selection.select("acs_large")
            selection.select("adhoc_fast")
            await pilot.pause(0.1)
            assert screen._selected_queues() == ["adhoc_fast", "acs_large"]
            assert screen._params()["queue"] == "adhoc_fast,acs_large"

    asyncio.run(run())


def test_prefill_restores_multiple_selected_queues(mock_env_with_config) -> None:
    """Re-running a job restores every queue it was launched with."""
    data_root = Path(os.environ["DISPATCH_DATA_ROOT"])
    sql_path = _write_sql(data_root)
    prefill = {
        "source_type": "SqlFile",
        "dest_type": "Csv",
        "sql_file": str(sql_path),
        "table_name": "queued_export",
        "queue": "adhoc_fast,acs_large",
    }

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            app.push_screen(NewJobScreen(app.launch_cwd, prefill=prefill))
            await pilot.pause(0.5)
            screen = app.screen
            assert isinstance(screen, NewJobScreen)
            assert screen._selected_queues() == ["adhoc_fast", "acs_large"]

    asyncio.run(run())
