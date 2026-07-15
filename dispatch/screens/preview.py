"""SQL preview screen with syntax highlighting and metadata."""

from __future__ import annotations

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RichLog, Static

from .. import advisor_data, manifest
from ..advisor.models import AnalysisResult, badge_markup, counts_label
from .findings import FindingBlock
from .sidebar import Sidebar


def sql_syntax(body: str) -> Syntax:
    """Build the shared SQL renderable: real lexer, line numbers, no background."""
    return Syntax(
        body,
        "sql",
        line_numbers=True,
        word_wrap=True,
        indent_guides=False,
        background_color="default",
        theme="ansi_dark",
    )


class PreviewScreen(Screen[None]):
    BINDINGS = [
        ("b", "app.pop_screen", "Back"),
        ("escape", "app.pop_screen", "Back"),
        ("enter", "accept", "Back"),
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
        analysis: AnalysisResult | None = None,
    ) -> None:
        super().__init__()
        self._title = title
        self.body = body
        self.schema = schema
        self.table = table
        self.source_type = source_type or "SqlFile"
        self.dest_type = dest_type or "Table"
        self.analysis = analysis or AnalysisResult(available=True, findings=())

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        sidebar = Sidebar()
        sidebar.active_screen = "new_job"
        yield sidebar
        with Vertical(id="main-content"):
            with Vertical(id="preview-content"):
                yield Static(
                    "[dim]\u2039 New Job /[/] [bold]" + self._title + "[/]"
                    " [dim]— review before launching[/]",
                    classes="section-title",
                )

                with Horizontal(id="preview-header"):
                    target = self.schema + "." + self.table if self.schema and self.table else ""
                    yield Static("[bold]Target:[/] " + target if target else "")
                    yield Static(
                        f"{manifest.source_display_label(self.source_type)} \u2192 {self.dest_type}",
                        id="preview-meta",
                    )

                with Vertical(id="sql-display"):
                    yield RichLog(
                        id="preview-body", highlight=False, markup=False, auto_scroll=False
                    )

                counts = counts_label(self.analysis)
                counts_part = f"{counts} · " if counts else ""
                yield Static(
                    "[bold]Advisor findings[/] "
                    f"[dim]· {counts_part}manual {advisor_data.MANUAL_VERSION}[/]",
                    classes="section-title",
                    id="findings-heading",
                )
                with VerticalScroll(id="findings-panel"):
                    if not self.analysis.available:
                        yield Static(
                            "[dim]SQL analysis unavailable — SQL findings cannot be "
                            "computed; launch is not gated.[/]",
                            classes="findings-note",
                        )
                    for finding in self.analysis.findings:
                        yield FindingBlock(finding)
                    if self.analysis.available and not self.analysis.findings:
                        yield Static(
                            "[green]✓ No findings[/] [dim]— nothing in the manual's "
                            "checklist fired.[/]",
                            classes="findings-note",
                        )

            with Horizontal(classes="action-bar"):
                yield Static("", id="preview-status", classes="action-status")
                yield Button("Copy SQL [Y]", id="copy", variant="default")
                yield Button("Back [Esc]", id="back", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#preview-body", RichLog)
        log.write(sql_syntax(self.body))
        line_count = len(self.body.splitlines())
        self.query_one("#preview-status", Static).update(
            f"{badge_markup(self.analysis)} [dim]· {line_count} lines[/]"
        )

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
        elif event.button.id == "copy":
            self.action_copy_sql()
