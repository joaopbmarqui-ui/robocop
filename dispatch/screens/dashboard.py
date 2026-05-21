"""Dashboard screen for active and recently finished Jobs."""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, cast

logger = logging.getLogger("dispatch.dashboard")

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static

from .. import jobs, kerberos
from .sidebar import Sidebar

if TYPE_CHECKING:
    from ..app import DispatchApp


class DashboardScreen(Screen[None]):
    BINDINGS = [
        ("n", "new_job", "New Job"),
        ("v", "view_logs", "View / Attach"),
        ("c", "cancel", "Cancel"),
        ("h", "history", "History"),
        ("b", "browser", "Browse"),
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.kerberos_ttl: int | None = None
        self._events: deque[str] = deque(maxlen=5)
        self._selected_job_id_cache: str | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        sidebar = Sidebar()
        sidebar.active_screen = "overview"
        yield sidebar
        with Vertical(id="main-content"):
            with Vertical(id="dashboard-content"):
                with Horizontal(id="stats-row"):
                    with Vertical(classes="stat-card"):
                        yield Static("RUNNING", classes="stat-label")
                        yield Static("0 / 2", id="stat-running", classes="stat-value stat-green")
                        yield Static("running / cap", classes="stat-sub")
                    with Vertical(classes="stat-card"):
                        yield Static("FINISHED (7D)", classes="stat-label")
                        yield Static("0", id="stat-finished", classes="stat-value stat-green")
                        yield Static("last 7 days", classes="stat-sub")
                    with Vertical(classes="stat-card"):
                        yield Static("FAILED (7D)", classes="stat-label")
                        yield Static("0", id="stat-failed", classes="stat-value stat-red")
                        yield Static("last 7 days", classes="stat-sub")
                    with Vertical(classes="stat-card"):
                        yield Static("KERBEROS", classes="stat-label")
                        yield Static("--", id="stat-kerberos", classes="stat-value stat-yellow")
                        yield Static("remaining", classes="stat-sub")
                yield Static("Active Jobs", classes="section-title")
                yield DataTable(id="active-table")
                with Vertical(id="active-empty", classes="empty-state"):
                    yield Static("\u25a1", classes="empty-icon")
                    yield Static("No active jobs", classes="summary-label")
                    yield Static("[dim]Press [bold]N[/bold] to create one[/]", classes="empty-hint")
                yield Static("Recently Finished (last 7 days)", classes="section-title")
                yield DataTable(id="recent-table")
                with Vertical(id="recent-empty", classes="empty-state"):
                    yield Static("\u25a1", classes="empty-icon")
                    yield Static("No recently finished jobs", classes="summary-label")
                    yield Static("[dim]Completed jobs appear here for 7 days[/]", classes="empty-hint")
                yield Static("", id="event-trail")
                with Horizontal(classes="button-row"):
                    yield Button("New Job [N]", id="new-job", variant="primary")
                    yield Button("View / Attach [V]", id="view-logs", variant="default")
                    yield Button("Cancel [C]", id="cancel", variant="error")
        yield Footer()

    async def on_mount(self) -> None:
        active_table = self.query_one("#active-table", DataTable)
        active_table.add_columns("ID", "Source", "Destination", "State", "Elapsed")
        active_table.cursor_type = "row"
        recent_table = self.query_one("#recent-table", DataTable)
        recent_table.add_columns("ID", "Source", "Destination", "State", "Elapsed")
        recent_table.cursor_type = "row"
        # Hide empty states initially
        self.query_one("#active-empty").display = False
        self.query_one("#recent-empty").display = False
        self._add_event("dispatch started")
        self.refresh_jobs()
        self.set_interval(2.0, self.refresh_jobs)
        self.kerberos_ttl = await kerberos.ticket_ttl_seconds()
        self._refresh_kerberos()

    def _add_event(self, text: str, severity: str = "info") -> None:
        now_str = datetime.now().strftime("%H:%M")
        color_map = {"error": "red", "warning": "yellow", "success": "green", "info": "dim"}
        color = color_map.get(severity, "dim")
        self._events.append(f"[{color}][{now_str}] {text}[/]")
        trail = self.query_one("#event-trail", Static)
        trail.update("\n".join(self._events))

    def _refresh_kerberos(self) -> None:
        label = self.query_one("#stat-kerberos", Static)
        if self.kerberos_ttl is None:
            label.update("N/A")
        else:
            minutes = self.kerberos_ttl // 60
            label.update(f"{minutes}m")

    def _elapsed(self, item: dict) -> str:
        started = item.get("started_at")
        if not started:
            return "--"
        try:
            start_dt = datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            return "--"
        if item["state"] == "Running":
            delta = datetime.now(timezone.utc) - start_dt
        else:
            finished = item.get("finished_at")
            if not finished:
                return "--"
            try:
                end_dt = datetime.strptime(finished, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                return "--"
            delta = end_dt - start_dt
        total_seconds = max(0, int(delta.total_seconds()))
        if total_seconds < 60:
            return f"{total_seconds}s"
        minutes = total_seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        return f"{hours}h {minutes % 60}m"

    def refresh_jobs(self) -> None:
        active = jobs.active_jobs()
        running = [j for j in active if j["state"] == "Running"]
        recent = [j for j in active if j["state"] != "Running"]

        self.query_one("#stat-running", Static).update(f"{len(running)} / 2")
        finished_count = sum(1 for j in active if j["state"] == "Succeeded")
        failed_count = sum(1 for j in active if j["state"] == "Failed")
        self.query_one("#stat-finished", Static).update(str(finished_count))
        self.query_one("#stat-failed", Static).update(str(failed_count))

        active_table = self.query_one("#active-table", DataTable)
        active_table.clear()
        if running:
            for item in running:
                active_table.add_row(
                    self._display_id(item["id"]),
                    self._source_label(item),
                    self._dest_label(item),
                    "[green]\u25cf RUNNING[/]",
                    self._elapsed(item),
                    key=item["id"],
                )
            active_table.display = True
            self.query_one("#active-empty").display = False
        else:
            active_table.display = False
            self.query_one("#active-empty").display = True

        recent_table = self.query_one("#recent-table", DataTable)
        recent_table.clear()
        if recent:
            for item in recent[:8]:
                state = item["state"]
                if state == "Succeeded":
                    state_display = "[green]\u25cf SUCCEEDED[/]"
                elif state == "Failed":
                    state_display = "[red]\u25cf FAILED[/]"
                elif state == "Cancelled":
                    state_display = "[dim]\u25cf CANCELLED[/]"
                else:
                    state_display = f"\u25cf {state}"
                recent_table.add_row(
                    self._display_id(item["id"]),
                    self._source_label(item),
                    self._dest_label(item),
                    state_display,
                    self._elapsed(item),
                    key=item["id"],
                )
            recent_table.display = True
            self.query_one("#recent-empty").display = False
        else:
            recent_table.display = False
            self.query_one("#recent-empty").display = True

        focused = self.focused
        if not active_table.display and recent_table.display and focused is active_table:
            recent_table.focus()
        elif active_table.display and not recent_table.display and focused is recent_table:
            active_table.focus()

    @staticmethod
    def _display_id(job_id: str) -> str:
        """Show timestamp + token suffix to distinguish same-day jobs."""
        if len(job_id) > 20:
            return job_id[9:]
        return job_id

    def _source_label(self, item: dict) -> str:
        src = item.get("source", {})
        if src.get("table_name"):
            return src["table_name"][:25]
        if src.get("sql_path_at_launch"):
            return Path(src["sql_path_at_launch"]).name[:25]
        return src.get("type", "")[:25]

    def _dest_label(self, item: dict) -> str:
        dest = item.get("destination", {})
        schema = dest.get("schema", "")
        table = dest.get("table_name", "")
        if schema and table:
            return f"{schema}.{table}"[:30]
        return dest.get("type", "")[:30]

    def _selected_job_id(self) -> str | None:
        for table_id in ("#active-table", "#recent-table"):
            table_widget = self.query_one(table_id, DataTable)
            candidate = self._job_id_from_table(table_widget)
            if candidate and table_widget.has_focus:
                self._selected_job_id_cache = candidate
                return candidate

        if self._selected_job_id_cache:
            all_job_ids = {job["id"] for job in jobs.active_jobs()}
            if self._selected_job_id_cache in all_job_ids:
                return self._selected_job_id_cache
            self._selected_job_id_cache = None

        return None

    def _job_id_from_table(self, table_widget: DataTable) -> str | None:
        try:
            row_key = table_widget.get_row_at(table_widget.cursor_row)
        except Exception:
            return None
        candidate = str(row_key[0])
        if not candidate or candidate.startswith("No "):
            return None
        all_jobs = jobs.active_jobs()
        for job in all_jobs:
            if job["id"].startswith(candidate):
                return job["id"]
        return None

    def _dispatch_app(self) -> "DispatchApp":
        return cast("DispatchApp", self.app)

    def action_new_job(self) -> None:
        self._dispatch_app().open_top_level("new_job")

    def action_view_logs(self) -> None:
        job_id = self._selected_job_id()
        if job_id:
            self._dispatch_app().open_job_detail(job_id)

    def action_cancel(self) -> None:
        job_id = self._selected_job_id()
        if job_id:
            self._dispatch_app().open_job_detail(job_id, cancel_on_mount=True)

    def action_history(self) -> None:
        self._dispatch_app().open_top_level("history")

    def action_browser(self) -> None:
        self._dispatch_app().open_top_level("browse")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-job":
            self.action_new_job()
        elif event.button.id == "view-logs":
            self.action_view_logs()
        elif event.button.id == "cancel":
            self.action_cancel()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_key = str(event.row_key.value) if event.row_key else ""
        if row_key and row_key != "__empty__":
            self._selected_job_id_cache = row_key
            self._dispatch_app().open_job_detail(row_key)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        row_key = str(event.row_key.value) if event.row_key else ""
        self._selected_job_id_cache = row_key if row_key and row_key != "__empty__" else None
