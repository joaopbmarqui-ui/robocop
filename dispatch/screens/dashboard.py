"""Overview screen: a supervision cockpit for Dispatch Jobs.

Wireframe rationale: Dispatch's dominant loop is launch -> watch -> diagnose.
Instead of a page-stack dashboard (stat cards + two tables + navigation to see
logs), the Overview is a persistent workspace: a dense status strip, one
unified Jobs table (running jobs pinned first), and a live detail pane that
tails the highlighted job's log. Full Job Detail remains one keypress away for
deep inspection.
"""

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
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from .. import config, errors, jobs, kerberos
from ..formatting import (
    format_elapsed,
    format_job_id,
    format_kerberos_ttl,
    format_state,
    style_log_line,
)
from .sidebar import Sidebar

if TYPE_CHECKING:
    from ..app import DispatchApp

JOBS_ROW_LIMIT = 100
DETAIL_TAIL_BYTES = 4096
DETAIL_TAIL_LINES = 8
# Below this height the detail pane is hidden so the jobs table stays usable.
DETAIL_MIN_HEIGHT = 30


class DashboardScreen(Screen[None]):
    BINDINGS = [
        ("n", "new_job", "New Job"),
        ("v", "view_logs", "View Logs"),
        ("c", "cancel", "Cancel"),
        ("h", "history", "History"),
        ("b", "browser", "Browse"),
        ("slash", "filter_jobs", "Filter"),
        Binding("escape", "clear_filter", "Clear Filter", show=False),
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
        self._table_signature: tuple | None = None
        self._filter_needle = ""
        self._detail_job_id: str | None = None
        self._detail_visible = True

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        sidebar = Sidebar()
        sidebar.active_screen = "overview"
        yield sidebar
        with Vertical(id="main-content"):
            with Vertical(id="dashboard-content"):
                yield Static("", id="status-strip")
                yield Static(
                    "[bold]Jobs[/] [dim]\u00b7 running first \u00b7 last 7 days[/]",
                    classes="section-title",
                    id="jobs-title",
                )
                yield Input(placeholder="Filter: id, file, table, or state\u2026", id="jobs-filter")
                yield DataTable(id="jobs-table")
                with Vertical(id="jobs-empty", classes="empty-state"):
                    yield Static("[dim]No jobs in the last 7 days \u2014 press [/][bold]N[/][dim] to launch one[/]")
                with Vertical(id="detail-pane"):
                    yield Static("[dim]Select a job to preview its log[/]", id="detail-title")
                    yield Static("", id="detail-log")
            with Horizontal(classes="action-bar", id="dashboard-action-bar"):
                yield Static("", id="event-trail", classes="action-status")
                yield Button("New Job [N]", id="new-job", variant="primary")
                yield Button("View Logs [V]", id="view-logs", variant="default")
                yield Button("Cancel [C]", id="cancel", variant="error")
        yield Footer()

    async def on_mount(self) -> None:
        table = self.query_one("#jobs-table", DataTable)
        table.add_columns("ID", "Source", "Destination", "State", "Elapsed")
        table.cursor_type = "row"
        self.query_one("#jobs-empty").display = False
        self.query_one("#jobs-filter").display = False
        self._add_event("dispatch started")
        self._update_layout_mode()
        await self._refresh_jobs_async()
        self.set_interval(2.0, self._refresh_jobs_async)
        self.kerberos_ttl = await kerberos.ticket_ttl_seconds()
        table.focus()

    def on_resize(self) -> None:
        self._update_layout_mode()

    def _update_layout_mode(self) -> None:
        visible = self.app.size.height >= DETAIL_MIN_HEIGHT
        if visible == self._detail_visible:
            return
        self._detail_visible = visible
        self.query_one("#detail-pane").display = visible

    def _add_event(self, text: str, severity: str = "info") -> None:
        now_str = datetime.now().strftime("%H:%M")
        color_map = {"error": "red", "warning": "yellow", "success": "green", "info": "dim"}
        color = color_map.get(severity, "dim")
        self._events.append(f"[{color}][{now_str}] {text}[/]")
        trail = self.query_one("#event-trail", Static)
        trail.update(self._events[-1])

    # ── Data refresh ────────────────────────────────────────────────────

    async def _refresh_jobs_async(self) -> None:
        try:
            detail_target = self._detail_job_id
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
            if detail_target is None and active:
                running_item = next(
                    (item for item in active if item["state"] == "Running"), None
                )
                detail_target = (running_item or active[0])["id"]
                self._detail_job_id = detail_target
            tail = (
                await asyncio.to_thread(self._read_log_tail, detail_target)
                if detail_target and self._detail_visible
                else None
            )
            self._apply_jobs_snapshot(
                {
                    "active": active,
                    "kerberos_ttl": kerberos_ttl,
                    "error_cache": error_cache,
                    "detail_target": detail_target,
                    "detail_tail": tail,
                }
            )
        except Exception as exc:
            self.notify(f"Job refresh failed: {exc}", severity="error")

    @staticmethod
    def _read_log_tail(job_id: str) -> list[str]:
        log_path = config.jobs_dir() / job_id / "run.log"
        try:
            size = log_path.stat().st_size
            with log_path.open("r", encoding="utf-8", errors="replace") as handle:
                if size > DETAIL_TAIL_BYTES:
                    handle.seek(size - DETAIL_TAIL_BYTES)
                    handle.readline()  # drop the partial first line
                lines = [line.rstrip() for line in handle if line.strip()]
        except OSError:
            return []
        return lines[-DETAIL_TAIL_LINES:]

    def _apply_jobs_snapshot(self, snapshot: dict) -> None:
        active = snapshot["active"]
        self.kerberos_ttl = snapshot["kerberos_ttl"]
        self._error_cache.update(snapshot["error_cache"])

        running = [j for j in active if j["state"] == "Running"]
        finished_count = sum(1 for j in active if j["state"] == "Succeeded")
        failed_count = sum(1 for j in active if j["state"] == "Failed")

        self._detect_state_transitions(active)
        self._update_status_strip(len(running), finished_count, failed_count)

        merged = running + [j for j in active if j["state"] != "Running"]
        merged = self._apply_filter(merged)[:JOBS_ROW_LIMIT]
        self._populate_table(merged)
        self._update_detail_pane(
            snapshot["detail_target"], snapshot["detail_tail"], active
        )

    def _update_status_strip(self, running: int, finished: int, failed: int) -> None:
        krb_ttl = self.kerberos_ttl
        if krb_ttl is None:
            krb_text = "[red]MISSING[/]"
        elif krb_ttl < 3600:
            krb_text = f"[yellow]{format_kerberos_ttl(krb_ttl)}[/]"
        else:
            krb_text = f"[green]{format_kerberos_ttl(krb_ttl)}[/]"
        finished_text = f"[green]{finished}[/]" if finished else "[dim]0[/]"
        failed_text = f"[red]{failed}[/]" if failed else "[dim]0[/]"
        self.query_one("#status-strip", Static).update(
            f"[dim]RUNNING[/] {running} / {jobs.RUNNING_CAP}    "
            f"[dim]FINISHED 7D[/] {finished_text}    "
            f"[dim]FAILED 7D[/] {failed_text}    "
            f"[dim]KERBEROS[/] {krb_text}"
        )

    def _apply_filter(self, items: list[dict]) -> list[dict]:
        needle = self._filter_needle.lower().strip()
        if not needle:
            return items
        matched = []
        for item in items:
            haystack = " ".join(
                (
                    item["id"],
                    self._source_label(item),
                    self._dest_label(item),
                    item["state"],
                )
            ).lower()
            if needle in haystack:
                matched.append(item)
        return matched

    def _populate_table(self, items: list[dict]) -> None:
        """Rebuild the jobs table only when content changed, preserving the cursor."""
        table = self.query_one("#jobs-table", DataTable)
        signature = tuple(
            (item["id"], item["state"], format_elapsed(item)) for item in items
        )
        if self._table_signature == signature:
            return
        self._table_signature = signature

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
        self.query_one("#jobs-empty").display = not has_rows

    def _update_detail_pane(
        self,
        job_id: str | None,
        tail: list[str] | None,
        active: list[dict],
    ) -> None:
        if not self._detail_visible:
            return
        title = self.query_one("#detail-title", Static)
        log_widget = self.query_one("#detail-log", Static)
        if job_id is None:
            title.update("[dim]Select a job to preview its log[/]")
            log_widget.update("")
            return
        item = next((j for j in active if j["id"] == job_id), None)
        if item is None:
            title.update("[dim]Select a job to preview its log[/]")
            log_widget.update("")
            return
        state_markup = format_state(item["state"], self._error_cache.get(job_id))
        suffix = "[dim] \u00b7 V for full logs[/]"
        title.update(
            f"[bold]{format_job_id(job_id)}[/]  {state_markup}  "
            f"[dim]{format_elapsed(item)}[/]{suffix}"
        )
        if tail:
            log_widget.update("\n".join(style_log_line(line) for line in tail))
        else:
            log_widget.update("[dim]No log output yet.[/]")

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

    @staticmethod
    def _cursor_row_key(table: DataTable) -> str | None:
        try:
            cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            return str(cell_key.row_key.value)
        except Exception:
            return None

    # ── Filter ──────────────────────────────────────────────────────────

    def action_filter_jobs(self) -> None:
        filter_input = self.query_one("#jobs-filter", Input)
        filter_input.display = True
        filter_input.focus()

    def action_clear_filter(self) -> None:
        filter_input = self.query_one("#jobs-filter", Input)
        if not filter_input.display:
            return
        filter_input.value = ""
        filter_input.display = False
        self._filter_needle = ""
        self._table_signature = None
        self.query_one("#jobs-table", DataTable).focus()
        self.call_after_refresh(self._refresh_jobs_async)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "jobs-filter":
            self._filter_needle = event.value
            self._table_signature = None
            self.call_after_refresh(self._refresh_jobs_async)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "jobs-filter":
            self.query_one("#jobs-table", DataTable).focus()

    # ── Selection / actions ─────────────────────────────────────────────

    def action_cursor_down(self) -> None:
        table = self.query_one("#jobs-table", DataTable)
        if table.has_focus:
            table.action_cursor_down()

    def action_cursor_up(self) -> None:
        table = self.query_one("#jobs-table", DataTable)
        if table.has_focus:
            table.action_cursor_up()

    def _selected_job_id(self) -> str | None:
        table = self.query_one("#jobs-table", DataTable)
        if table.display:
            candidate = self._cursor_row_key(table)
            if candidate:
                self._selected_job_id_cache = candidate
                return candidate

        if self._selected_job_id_cache:
            all_job_ids = {job["id"] for job in jobs.active_jobs()}
            if self._selected_job_id_cache in all_job_ids:
                return self._selected_job_id_cache
            self._selected_job_id_cache = None

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
        if row_key and row_key != "__empty__":
            self._selected_job_id_cache = row_key
            if row_key != self._detail_job_id:
                self._detail_job_id = row_key
                self.run_worker(
                    self._refresh_detail_only(row_key),
                    name="detail-tail",
                    group="detail",
                    exclusive=True,
                )
        else:
            self._selected_job_id_cache = None

    async def _refresh_detail_only(self, job_id: str) -> None:
        """Fast path: update only the detail pane when the highlight moves."""
        if not self._detail_visible:
            return
        tail = await asyncio.to_thread(self._read_log_tail, job_id)
        active = await asyncio.to_thread(jobs.active_jobs)
        if self._detail_job_id == job_id:
            self._update_detail_pane(job_id, tail, active)
