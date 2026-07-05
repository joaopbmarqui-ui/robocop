"""Tests for ExistingTable schema selection on the New Job screen."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.widgets import Input, RadioButton

from dispatch.app import DispatchApp
from dispatch.screens.new_job import NewJobScreen


def test_existing_table_shows_schema_selector(mock_env_with_config, tmp_path: Path) -> None:
    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(140, 50)) as pilot:
            screen = NewJobScreen(tmp_path)
            app.push_screen(screen)
            await pilot.pause(0.5)
            screen.query_one("#src-existingtable", RadioButton).value = True
            await pilot.pause(0.2)

            assert screen.query_one("#row-existing-schema").display is True
            assert screen.query_one("#row-existing-table").display is True
            assert screen._existing_schema_selection() == "aa_enc"
            assert screen.query_one("#row-schema").display is False

    asyncio.run(run())


def test_existing_table_other_shows_manual_schema(mock_env_with_config, tmp_path: Path) -> None:
    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(140, 50)) as pilot:
            screen = NewJobScreen(tmp_path)
            app.push_screen(screen)
            await pilot.pause(0.5)
            screen.query_one("#src-existingtable", RadioButton).value = True
            await pilot.pause(0.2)
            screen.query_one("#existing-schema-other", RadioButton).value = True
            await pilot.pause(0.2)

            assert screen._existing_schema_selection() == "other"
            assert screen.query_one("#row-schema").display is True
            assert screen.query_one("#schema", Input).disabled is False

    asyncio.run(run())


def test_existing_table_preset_uses_selected_schema(mock_env_with_config, tmp_path: Path) -> None:
    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(140, 50)) as pilot:
            screen = NewJobScreen(tmp_path)
            app.push_screen(screen)
            await pilot.pause(0.5)
            screen.query_one("#src-existingtable", RadioButton).value = True
            await pilot.pause(0.2)
            screen.query_one("#existing-schema-coe", RadioButton).value = True
            screen.query_one("#existing-table", Input).value = "events_existing"
            await pilot.pause(0.2)

            assert screen._existing_schema_value() == "coe_enc"
            assert screen._existing_table_full() == "coe_enc.events_existing"
            source, _destination = screen._source_destination()
            assert source == {
                "type": "ExistingTable",
                "table_name": "coe_enc.events_existing",
            }

    asyncio.run(run())


def test_prefill_existing_table_splits_schema_and_table(
    mock_env_with_config, tmp_path: Path
) -> None:
    prefill = {
        "source_type": "ExistingTable",
        "dest_type": "Csv",
        "existing_table": "aa_enc.dispatch_smoke_seed",
    }

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(140, 50)) as pilot:
            app.push_screen(NewJobScreen(tmp_path, prefill=prefill))
            await pilot.pause(0.8)
            screen = app.screen
            assert isinstance(screen, NewJobScreen)
            assert screen._existing_schema_selection() == "aa_enc"
            assert screen.query_one("#existing-table", Input).value == "dispatch_smoke_seed"
            assert screen._existing_table_full() == "aa_enc.dispatch_smoke_seed"

    asyncio.run(run())


def test_prefill_existing_table_custom_schema_uses_other(
    mock_env_with_config, tmp_path: Path
) -> None:
    prefill = {
        "source_type": "ExistingTable",
        "dest_type": "Csv",
        "existing_table": "analytics.events_existing",
    }

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(140, 50)) as pilot:
            app.push_screen(NewJobScreen(tmp_path, prefill=prefill))
            await pilot.pause(0.8)
            screen = app.screen
            assert isinstance(screen, NewJobScreen)
            assert screen._existing_schema_selection() == "other"
            assert screen.query_one("#schema", Input).value == "analytics"
            assert screen.query_one("#existing-table", Input).value == "events_existing"
            assert screen.query_one("#row-schema").display is True

    asyncio.run(run())
