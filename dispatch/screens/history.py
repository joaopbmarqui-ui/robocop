"""History screen for Jobs older than the dashboard window."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from .. import jobs
from .job_detail import JobDetailScreen


class HistoryScreen(Screen[None]):
    BINDINGS = [
        ("b", "app.pop_screen", "Back"),
        ("enter", "view_logs", "View Logs"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="history"):
            yield Static("History")
            yield Input(placeholder="Search by table/date/job id", id="search")
            yield Input(placeholder="Job id to view", id="job-id")
            yield Static("", id="history-table")
            yield Button("View Logs", id="view-logs")
            yield Button("Back", id="back")

    def on_mount(self) -> None:
        self.refresh_history()

    def on_input_changed(self, _event: Input.Changed) -> None:
        self.refresh_history()

    def refresh_history(self) -> None:
        needle = self.query_one("#search", Input).value.lower().strip()
        rows = []
        for item in jobs.history_jobs():
            destination = item["destination"]
            table = f"{destination.get('schema', '')}.{destination.get('table_name', '')}"
            haystack = f"{item['id']} {table} {item['finished_at']}".lower()
            if needle and needle not in haystack:
                continue
            rows.append(f"{item['id'][:19]:19} {table[:25]:25} {item['state']:10} {item['finished_at']}")
        self.query_one("#history-table", Static).update("\n".join(rows) if rows else "(no history)")

    def action_view_logs(self) -> None:
        job_id = self.query_one("#job-id", Input).value.strip()
        if job_id:
            self.app.push_screen(JobDetailScreen(job_id))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "view-logs":
            self.action_view_logs()
        elif event.button.id == "back":
            self.app.pop_screen()
