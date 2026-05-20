"""History screen for Jobs older than the dashboard window."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from .. import jobs
from .job_detail import JobDetailScreen
from .sidebar import Sidebar

PAGE_SIZE = 17


class HistoryScreen(Screen[None]):
    BINDINGS = [
        ("b", "app.pop_screen", "Back"),
        ("escape", "app.pop_screen", "Back"),
        ("enter", "view_logs", "View Logs"),
        ("[", "prev_page", "Prev Page"),
        ("]", "next_page", "Next Page"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._page = 0
        self._filtered: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        sidebar = Sidebar()
        sidebar.active_screen = "history"
        yield sidebar
        with Vertical(id="main-content"):
            with Vertical(id="history-content"):
                yield Static("Recently Finished (all time)", classes="section-title")

                with Horizontal(id="search-row"):
                    yield Static("[dim]Search:[/]", id="search-label")
                    yield Input(
                        placeholder="\U0001f50d table \u00b7 date \u00b7 job-id",
                        id="search",
                    )

                yield DataTable(id="history-table")
                with Vertical(id="history-empty", classes="empty-state"):
                    yield Static("\u25a1", classes="empty-icon")
                    yield Static("No history found", classes="summary-label")
                    yield Static("[dim]Adjust your search or run some jobs[/]", classes="empty-hint")

                with Horizontal(id="pagination"):
                    yield Static("", id="page-info")
                    yield Static("", id="page-controls")

                with Horizontal(classes="button-row"):
                    yield Button("View Logs [Enter]", id="view-logs", variant="primary")
                    yield Button("Back [B]", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#history-table", DataTable)
        table.add_columns("ID", "Table/Target", "State", "Finished At")
        table.cursor_type = "row"
        self.query_one("#history-empty").display = False
        self._all_jobs = jobs.history_jobs()
        self._filtered = self._all_jobs
        self.refresh_history()
        if self._filtered:
            table.focus()
        else:
            self.query_one("#search", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search":
            self._page = 0
            self.refresh_history()

    def refresh_history(self) -> None:
        self._all_jobs = jobs.history_jobs()
        needle = self.query_one("#search", Input).value.lower().strip()
        self._filtered = []
        for item in self._all_jobs:
            dest = item["destination"]
            table_name = f"{dest.get('schema', '')}.{dest.get('table_name', '')}"
            haystack = f"{item['id']} {table_name} {item['finished_at']}".lower()
            if needle and needle not in haystack:
                continue
            self._filtered.append(item)

        total = len(self._filtered)
        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        self._page = min(self._page, total_pages - 1)
        start = self._page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_items = self._filtered[start:end]

        table = self.query_one("#history-table", DataTable)
        table.clear()
        for item in page_items:
            state = item["state"]
            if state == "Succeeded":
                state_display = "[green]\u25cf SUCCEEDED[/]"
            elif state == "Failed":
                state_display = "[red]\u25cf FAILED[/]"
            elif state == "Cancelled":
                state_display = "[dim]\u25cf CANCELLED[/]"
            else:
                state_display = f"\u25cf {state}"

            dest = item["destination"]
            table_name = dest.get("table_name") or dest.get("csv_path", "")
            if "/" in table_name:
                table_name = table_name.split("/")[-1]

            table.add_row(
                self._display_id(item["id"]),
                table_name[:25],
                state_display,
                item["finished_at"] or "",
                key=item["id"],
            )

        if not self._filtered:
            table.display = False
            self.query_one("#history-empty").display = True
            self.query_one("#pagination").display = False
            if table.has_focus:
                self.query_one("#search", Input).focus()
        else:
            table.display = True
            self.query_one("#history-empty").display = False
            self.query_one("#pagination").display = True

        self.query_one("#page-info", Static).update(
            f"[dim]Showing {start + 1}-{min(end, total)} of {total}[/]"
            if total > 0
            else "[dim]No results[/]"
        )
        self.query_one("#page-controls", Static).update(
            f"[dim]\u276e Prev    Page {self._page + 1} of {total_pages}    Next \u276f[/]"
        )

    def action_next_page(self) -> None:
        total_pages = max(1, (len(self._filtered) + PAGE_SIZE - 1) // PAGE_SIZE)
        if self._page < total_pages - 1:
            self._page += 1
            self.refresh_history()

    def action_prev_page(self) -> None:
        if self._page > 0:
            self._page -= 1
            self.refresh_history()

    @staticmethod
    def _display_id(job_id: str) -> str:
        """Strip date prefix from job ID if it matches 202xxxxxTxxxxxxZ_ format."""
        if len(job_id) > 17 and job_id[15] == "Z" and "_" in job_id:
            return job_id.split("_", 1)[1]
        return job_id

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_key = str(event.row_key.value) if event.row_key else ""
        if row_key and row_key != "__empty__":
            self.app.push_screen(JobDetailScreen(row_key))

    def _selected_job_id(self) -> str | None:
        table = self.query_one("#history-table", DataTable)
        try:
            cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            row_key = str(cell_key.row_key.value)
        except Exception:
            return None
        if row_key and row_key != "__empty__":
            return row_key
        return None

    def action_view_logs(self) -> None:
        row_key = self._selected_job_id()
        if row_key:
            self.app.push_screen(JobDetailScreen(row_key))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "view-logs":
            self.action_view_logs()
        elif event.button.id == "back":
            self.app.pop_screen()
