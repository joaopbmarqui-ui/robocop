"""Impala metadata browser screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from .. import impala


class BrowserScreen(Screen[None]):
    BINDINGS = [
        ("b", "app.pop_screen", "Back"),
        ("enter", "describe", "Describe"),
        ("d", "drop", "Drop"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="browser"):
            yield Static("Browse Impala Metadata")
            yield Input(value="dw_settle", placeholder="Schema", id="schema")
            yield Input(value="*", placeholder="Filter", id="filter")
            yield Input(placeholder="Selected table", id="table")
            yield Button("SHOW TABLES", id="show")
            yield Button("DESCRIBE", id="describe")
            yield Button("DROP", id="drop", variant="error")
            yield Button("Back", id="back")
            yield Static("", id="results")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "show":
            await self.action_show_tables()
        elif event.button.id == "describe":
            await self.action_describe()
        elif event.button.id == "drop":
            await self.action_drop()
        elif event.button.id == "back":
            self.app.pop_screen()

    def _schema(self) -> str:
        return self.query_one("#schema", Input).value.strip()

    def _full_table(self) -> str:
        table = self.query_one("#table", Input).value.strip()
        return table if "." in table else f"{self._schema()}.{table}"

    async def action_show_tables(self) -> None:
        try:
            rows = await impala.show_tables(self._schema(), self.query_one("#filter", Input).value.strip() or "*")
            self.query_one("#results", Static).update("\n".join(rows) if rows else "(no tables)")
        except Exception as exc:
            self.query_one("#results", Static).update(str(exc))

    async def action_describe(self) -> None:
        try:
            self.query_one("#results", Static).update(await impala.describe_table(self._full_table()))
        except Exception as exc:
            self.query_one("#results", Static).update(str(exc))

    async def action_drop(self) -> None:
        try:
            self.query_one("#results", Static).update(await impala.drop_table(self._full_table()))
        except Exception as exc:
            self.query_one("#results", Static).update(str(exc))
