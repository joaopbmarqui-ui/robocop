"""Dashboard screen for active and recently finished Jobs."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

logger = logging.getLogger("dispatch.dashboard")

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static

from .. import config, errors, jobs, kerberos
from ..formatting import format_elapsed, format_job_id, format_kerberos_ttl, format_state
from .sidebar import Sidebar

if TYPE_CHECKING:
    from ..app import DispatchApp

RECENT_ROW_LIMIT = 50


class DashboardScreen(Screen[None]):
    BINDINGS = [
        ("n", "new_job", "New Job"),
        ("v", "view_logs", "View Logs"),
        ("c", "cancel", "Cancel"),
        ("h", "history", "History"),
        ("b", "browser", "Browse"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("q", "app.quit", "Quit", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.kerberos_ttl: int | None = None
        self._events: deque[str] = deque(maxlen=3)
        self._selected_job_id_cache: str | None = None
        self._error_cache: dict[str, str | None] = {}
        self._last_states: dict[str, str] = {}
        self._compact_stats = False
        self._table_signatures: dict[str, tuple] = {}

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
                        yield Static("0 / 2", id="stat-running", classes="stat-value")
                        yield Static("slots in use", classes="stat-sub")
                    with Vertical(classes="stat-card"):
                        yield Static("FINISHED", classes="stat-label")
                        yield Static("0", id="stat-finished", classes="stat-value")
                        yield Static("last 7 days", classes="stat-sub")
                    with Vertical(classes="stat-card"):
                        yield Static("FAILED", classes="stat-label")
                        yield Static("0", id="stat-failed", classes="stat-value")
                        yield Static("last 7 days", classes="stat-sub")
                    with Vertical(classes="stat-card"):
                        yield Static("KERBEROS", classes="stat-label")
                        yield Static("--", id="stat-kerberos", classes="stat-value")
                        yield Static("ticket remaining", classes="stat-sub")
                yield Static("", id="stats-compact", classes="stats-compact-line")
                yield Static(
                    "[bold]Active Jobs[/] [dim]\u00b7 newest first[/]",
                    classes="section-title",
                    id="active-title",
                )
                yield DataTable(id="active-table")
                with Vertical(id="active-empty", classes="empty-state"):
                    yield Static("[dim]No active jobs \u2014 press [/][bold]N[/][dim] to launch one[/]")
                with Vertical(id="recent-section"):
                    yield Static(
                        "[bold]Recently Finished[/] [dim]\u00b7 last 7 days \u00b7 newest first[/]",
                        classes="section-title",
                        id="recent-title",
                    )
                    yield DataTable(id="recent-table")
                    with Vertical(id="recent-empty", classes="empty-state"):
                        yield Static("[dim]No recently finished jobs \u2014 completed jobs appear here for 7 days[/]")
            with Horizontal(classes="action-bar", id="dashboard-action-bar"):
                yield Static("", id="event-trail", classes="action-status")
                yield Button("New Job [N]", id="new-job", variant="primary")
                yield Button("View Logs [V]", id="view-logs", variant="default")
                yield Button("Cancel [C]", id="cancel", variant="error")
        yield Footer()

    async def on_mount(self) -> None:
        active_table = self.query_one("#active-table", DataTable)
        active_table.add_columns("ID", "Source", "Destination", "State", "Elapsed")
        active_table.cursor_type = "row"
        recent_table = self.query_one("#recent-table", DataTable)
        recent_table.add_columns("ID", "Source", "Destination", "State", "Elapsed")
        recent_table.cursor_type = "row"
        self.query_one("#active-empty").display = False
        self.query_one("#recent-empty").display = False
        self.query_one("#stats-compact").display = False
        self._add_event("dispatch started")
        self._update_layout_mode()
        await self._refresh_jobs_async()
        self.set_interval(2.0, self._refresh_jobs_async)
        self.kerberos_ttl = await kerberos.ticket_ttl_seconds()
        self._refresh_kerberos()

    def on_resize(self) -> None:
        self._update_layout_mode()

    def _update_layout_mode(self) -> None:
        compact = self.app.size.width < 100
        if compact == self._compact_stats:
            return
        self._compact_stats = compact
        self.set_class(compact, "dashboard-compact")
        self.query_one("#stats-row").display = not compact
        self.query_one("#stats-compact").display = compact

    def _add_event(self, text: str, severity: str = "info") -> None:
        now_str = datetime.now().strftime("%H:%M")
        color_map = {"error": "red", "warning": "yellow", "success": "green", "info": "dim"}
        color = color_map.get(severity, "dim")
        self._events.append(f"[{color}][{now_str}] {text}[/]")
        trail = self.query_one("#event-trail", Static)
        trail.update(self._events[-1])

    def _refresh_kerberos(self) -> None:
        label = self.query_one("#stat-kerberos", Static)
        if self.kerberos_ttl is None:
            label.update("[red]MISSING[/]")
        elif self.kerberos_ttl < 3600:
            label.update(f"[yellow]{format_kerberos_ttl(self.kerberos_ttl)}[/]")
        else:
            label.update(f"[green]{format_kerberos_ttl(self.kerberos_ttl)}[/]")

    async def _refresh_jobs_async(self) -> None:
        try:
            active = await asyncio.to_thread(jobs.active_jobs)
            kerberos_ttl = await kerberos.ticket_ttl_seconds()
            error_cache: dict[str, str | None] = {}
            for item in active:
                if item["state"] != "Failed":
                    continue
                job_id = item["id"]
                if job_id in self._error_cache:
                    error_cache[job_id] = self._error_cache[job_id]
                else:
                    log_path = config.jobs_dir() / job_id / "run.log"
                    error_cache[job_id] = await asyncio.to_thread(errors.classify, log_path)
            self._apply_jobs_snapshot(
                {"active": active, "kerberos_ttl": kerberos_ttl, "error_cache": error_cache}
            )
        except Exception as exc:
            self.notify(f"Job refresh failed: {exc}", severity="error")

    def _apply_jobs_snapshot(self, snapshot: dict) -> None:
        active = snapshot["active"]
        self.kerberos_ttl = snapshot["kerberos_ttl"]
        self._error_cache.update(snapshot["error_cache"])

        running = [j for j in active if j["state"] == "Running"]
        recent = [j for j in active if j["state"] != "Running"]
        finished_count = sum(1 for j in active if j["state"] == "Succeeded")
        failed_count = sum(1 for j in active if j["state"] == "Failed")

        self._detect_state_transitions(active)
        self._refresh_kerberos()

        if self._compact_stats:
            krb_text = format_kerberos_ttl(self.kerberos_ttl)
            compact = self.query_one("#stats-compact", Static)
            compact.update(
                f"\u25cf Running {len(running)}/2  "
                f"\u2713 Finished {finished_count}  "
                f"\u2717 Failed {failed_count}  "
                f"KRB {krb_text}"
            )

        self.query_one("#stat-running", Static).update(f"{len(running)} / 2")
        self.query_one("#stat-finished", Static).update(
            f"[green]{finished_count}[/]" if finished_count else "[dim]0[/]"
        )
        self.query_one("#stat-failed", Static).update(
            f"[red]{failed_count}[/]" if failed_count else "[dim]0[/]"
        )

        self._populate_table("#active-table", "#active-empty", running)
        self._populate_table("#recent-table", "#recent-empty", recent[:RECENT_ROW_LIMIT])

        active_table = self.query_one("#active-table", DataTable)
        recent_table = self.query_one("#recent-table", DataTable)
        focused = self.focused
        if not active_table.display and recent_table.display and focused is active_table:
            recent_table.focus()
        elif active_table.display and not recent_table.display and focused is recent_table:
            active_table.focus()

    def _populate_table(self, table_id: str, empty_id: str, items: list[dict]) -> None:
        """Rebuild a job table only when its content changed, preserving the cursor."""
        table = self.query_one(table_id, DataTable)
        signature = tuple(
            (item["id"], item["state"], format_elapsed(item)) for item in items
        )
        if self._table_signatures.get(table_id) == signature:
            return
        self._table_signatures[table_id] = signature

        cursor_key = self._cursor_row_key(table)
        table.clear()
        for item in items:
            table.add_row(
                format_job_id(item["id"]),
                self._source_label(item),
                self._dest_label(item),
                format_state(item["state"], self._error_cache.get(item["id"])),
                Text(format_elapsed(item), justify="right"),
                key=item["id"],
            )
        if cursor_key is not None:
            try:
                table.move_cursor(row=table.get_row_index(cursor_key))
            except Exception:
                pass

        has_rows = bool(items)
        table.display = has_rows
        self.query_one(empty_id).display = not has_rows

    @staticmethod
    def _cursor_row_key(table: DataTable) -> str | None:
        try:
            cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            return str(cell_key.row_key.value)
        except Exception:
            return None

    def _detect_state_transitions(self, active: list[dict]) -> None:
        current: dict[str, str] = {item["id"]: item["state"] for item in active}
        for job_id, state in current.items():
            prev = self._last_states.get(job_id)
            if prev == "Running" and state in ("Succeeded", "Failed", "Cancelled"):
                severity = {"Succeeded": "success", "Failed": "error"}.get(state, "warning")
                self._add_event(f"Job {format_job_id(job_id)} {state.lower()}", severity)
                self.app.notify(
                    f"Job {format_job_id(job_id)} {state.lower()}",
                    severity="information" if state == "Succeeded" else "warning",
                )
        self._last_states = current

    def _source_label(self, item: dict) -> str:
        src = item.get("source", {})
        if src.get("table_name"):
            return src["table_name"][:22]
        if src.get("sql_path_at_launch"):
            return Path(src["sql_path_at_launch"]).name[:22]
        return src.get("type", "")[:22]

    def _dest_label(self, item: dict) -> str:
        dest = item.get("destination", {})
        schema = dest.get("schema", "")
        table = dest.get("table_name", "")
        if schema and table:
            return f"{schema}.{table}"[:26]
        return dest.get("type", "")[:26]

    def _focused_table(self) -> DataTable | None:
        for table_id in ("#active-table", "#recent-table"):
            table = self.query_one(table_id, DataTable)
            if table.has_focus and table.display:
                return table
        return None

    def action_cursor_down(self) -> None:
        table = self._focused_table()
        if table is not None:
            table.action_cursor_down()

    def action_cursor_up(self) -> None:
        table = self._focused_table()
        if table is not None:
            table.action_cursor_up()

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
        for job in jobs.active_jobs():
            if job["id"].startswith(candidate) or format_job_id(job["id"]) == candidate:
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
