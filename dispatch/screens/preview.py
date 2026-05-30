"""SQL preview screen with syntax highlighting and metadata."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RichLog, Static

from .sidebar import Sidebar

_SQL_KEYWORDS = {
    "SELECT", "FROM", "WHERE", "INSERT", "INTO", "UPDATE", "DELETE",
    "CREATE", "DROP", "ALTER", "TABLE", "IF", "EXISTS", "NOT",
    "AS", "AND", "OR", "IN", "IS", "NULL", "ON", "JOIN", "LEFT",
    "RIGHT", "INNER", "OUTER", "GROUP", "BY", "ORDER", "HAVING",
    "LIMIT", "OFFSET", "UNION", "ALL", "DISTINCT", "SET",
    "STORED", "PARQUET", "LOCATION", "LIKE", "BETWEEN",
    "CASE", "WHEN", "THEN", "ELSE", "END", "CAST", "WITH",
    "VALUES", "COUNT", "SUM", "AVG", "MIN", "MAX",
}


def _highlight_sql(line: str) -> str:
    """Apply basic keyword highlighting via Rich markup."""
    stripped = line.lstrip()
    if stripped.startswith("--"):
        return f"[dim]{line}[/]"
    tokens = []
    for word in line.split(" "):
        if word.upper() in _SQL_KEYWORDS:
            tokens.append(f"[bold cyan]{word}[/]")
        elif word.startswith("'") or word.startswith('"'):
            tokens.append(f"[green]{word}[/]")
        else:
            tokens.append(word)
    return " ".join(tokens)


def _numbered_sql(body: str) -> list[str]:
    """Add line numbers and keyword highlighting via Rich markup."""
    lines = body.splitlines()
    width = len(str(len(lines)))
    result = []
    for i, line in enumerate(lines, 1):
        num = f"[dim]{i:>{width}}[/]"
        highlighted = _highlight_sql(line)
        result.append(f"{num} \u2502 {highlighted}")
    return result


class PreviewScreen(Screen[None]):
    BINDINGS = [
        ("b", "app.pop_screen", "Back"),
        ("escape", "app.pop_screen", "Back"),
        ("enter", "accept", "Accept"),
        ("y", "copy_sql", "Copy SQL"),
    ]

    def __init__(
        self,
        title: str,
        body: str,
        *,
        schema: str = "",
        table: str = "",
        source_type: str = "",
        dest_type: str = "",
    ) -> None:
        super().__init__()
        self._title = title
        self.body = body
        self.schema = schema
        self.table = table
        self.source_type = source_type or "SqlFile"
        self.dest_type = dest_type or "Table"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        sidebar = Sidebar()
        sidebar.active_screen = "new_job"
        yield sidebar
        with Vertical(id="main-content"):
            with Vertical(id="preview-content"):
                yield Static(
                    "[dim]\u2039[/] New Job / [bold cyan]" + self._title + "[/]",
                    classes="section-title",
                )

                with Horizontal(id="preview-header"):
                    target = self.schema + "." + self.table if self.schema and self.table else ""
                    yield Static("[bold]Target: " + target + "[/]" if target else "")
                    meta = ""
                    if self.schema:
                        meta = "[cyan]Schema:[/] " + self.schema + "  [cyan]Table:[/] " + self.table
                    yield Static(meta, id="preview-meta")

                with Vertical(id="sql-display"):
                    yield RichLog(id="preview-body", highlight=True, markup=True)

                with Horizontal(id="preview-footer-info"):
                    yield Static(f"[dim]Source: {self.source_type}[/]")
                    dest_label = f"[dim]Destination: {self.dest_type}[/]"
                    if self.schema and self.table:
                        dest_label = f"[dim]Destination: {self.dest_type} \u2192 {self.schema}.{self.table}[/]"
                    yield Static(dest_label)

                with Horizontal(classes="button-row"):
                    yield Button("Back to Form [Enter]", id="accept", variant="primary")
                    yield Button("Back [B/Esc]", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#preview-body", RichLog)
        for line in _numbered_sql(self.body):
            log.write(line)

    def action_accept(self) -> None:
        self.app.pop_screen()

    def action_copy_sql(self) -> None:
        try:
            self.app.copy_to_clipboard(self.body)
            self.notify("SQL copied to clipboard", severity="information")
        except Exception:
            self.notify("Copy unavailable in this terminal", severity="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "accept":
            self.action_accept()
