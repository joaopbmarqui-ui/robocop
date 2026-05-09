"""Dashboard screen for active and recently finished Jobs."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from .. import jobs
from .job_detail import JobDetailScreen
from .new_job import NewJobScreen


class DashboardScreen(Screen[None]):
    BINDINGS = [
        ("n", "new_job", "New Job"),
        ("v", "view_logs", "View Logs"),
        ("a", "view_logs", "Attach"),
        ("c", "cancel", "Cancel"),
        ("h", "history", "History"),
        ("b", "browser", "Browse"),
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self, launch_cwd: Path) -> None:
        super().__init__()
        self.launch_cwd = launch_cwd

    def compose(self) -> ComposeResult:
        with Vertical(id="dashboard"):
            yield Static("Dispatch")
            yield Static("", id="active")
            yield Static("", id="recent")
            yield Input(placeholder="Job id for attach/cancel (blank = first active)", id="job-id")
            yield Button("New Job", id="new-job", variant="primary")
            yield Button("View Logs", id="view-logs")
            yield Button("Cancel", id="cancel", variant="error")
            yield Static("[N]ew Job [A]ttach [C]ancel [V]iew Logs [H]istory [B]rowse [Q]uit")

    def on_mount(self) -> None:
        self.refresh_jobs()
        self.set_interval(2.0, self.refresh_jobs)

    def refresh_jobs(self) -> None:
        active = jobs.active_jobs()
        running = [item for item in active if item["state"] == "Running"]
        recent = [item for item in active if item["state"] != "Running"]
        self.query_one("#active", Static).update(self._table("Active Jobs", running, f"{len(running)} / 2"))
        self.query_one("#recent", Static).update(self._table("Recently Finished", recent[:8], "last 7 days"))

    def _table(self, title: str, items: list[dict], suffix: str) -> str:
        lines = [f"{title} ({suffix})", "ID                  Source       Destination   State"]
        if not items:
            lines.append("(none)")
        for item in items:
            lines.append(
                f"{item['id'][:19]:19} {item['source']['type'][:11]:11} "
                f"{item['destination']['type'][:13]:13} {item['state']}"
            )
        return "\n".join(lines)

    def _selected_job_id(self) -> str | None:
        value = self.query_one("#job-id", Input).value.strip()
        if value:
            return value
        active = jobs.active_jobs()
        return active[0]["id"] if active else None

    def action_new_job(self) -> None:
        self.app.push_screen(NewJobScreen(self.launch_cwd))

    def action_view_logs(self) -> None:
        job_id = self._selected_job_id()
        if job_id:
            self.app.push_screen(JobDetailScreen(job_id))

    def action_cancel(self) -> None:
        job_id = self._selected_job_id()
        if job_id:
            self.app.push_screen(JobDetailScreen(job_id, cancel_on_mount=True))

    def action_history(self) -> None:
        from .history import HistoryScreen

        self.app.push_screen(HistoryScreen())

    def action_browser(self) -> None:
        from .browser import BrowserScreen

        self.app.push_screen(BrowserScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-job":
            self.action_new_job()
        elif event.button.id == "view-logs":
            self.action_view_logs()
        elif event.button.id == "cancel":
            self.action_cancel()
