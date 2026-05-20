"""Job detail and live-tail screen."""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RichLog, Static

from .. import config, manifest, process
from .confirm import ConfirmScreen
from .sidebar import Sidebar


class JobDetailScreen(Screen[None]):
    BINDINGS = [
        ("b", "app.pop_screen", "Back"),
        ("c", "cancel", "Cancel Job"),
        ("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, job_id: str, cancel_on_mount: bool = False) -> None:
        super().__init__()
        self.job_id = job_id
        self.cancel_on_mount = cancel_on_mount
        self._tail_offset = 0
        self._last_line_count = 0
        self._tail_lines: deque[str] = deque(maxlen=200)

    @property
    def job_dir(self):
        return config.jobs_dir() / self.job_id

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        sidebar = Sidebar()
        sidebar.active_screen = "view_logs"
        yield sidebar
        with Vertical(id="main-content"):
            with Vertical(id="job-detail-content"):
                yield Static(
                    f"[dim]\u2039[/] Job [bold cyan]{self.job_id}[/]",
                    classes="section-title",
                )

                with Vertical(id="job-summary-panel"):
                    yield Static("Job Summary", classes="section-title")
                    with Horizontal(id="summary-grid"):
                        with Vertical():
                            yield Static("[dim]Source:[/]", classes="summary-label")
                            yield Static("--", id="sum-source", classes="summary-value")
                            yield Static("[dim]Destination:[/]", classes="summary-label")
                            yield Static("--", id="sum-dest", classes="summary-value")
                            yield Static("[dim]State:[/]", classes="summary-label")
                            yield Static("--", id="sum-state", classes="summary-value")
                        with Vertical():
                            yield Static("[dim]Started:[/]", classes="summary-label")
                            yield Static("--", id="sum-started", classes="summary-value")
                            yield Static("[dim]Elapsed:[/]", classes="summary-label")
                            yield Static("--", id="sum-elapsed", classes="summary-value")
                            yield Static("[dim]Target Table:[/]", classes="summary-label")
                            yield Static("--", id="sum-table", classes="summary-value")
                            yield Static("[dim]CSV Path:[/]", classes="summary-label")
                            yield Static("--", id="sum-csv", classes="summary-value")

                with Horizontal(id="log-header"):
                    yield Static(
                        "[bold cyan]Live Logs[/]",
                        classes="section-title",
                    )
                    yield Static(
                        "",
                        id="log-streaming",
                    )

                with Vertical(id="log-panel"):
                    yield RichLog(id="log-display", highlight=True, markup=True)

                yield Static("", id="job-status-line")

                with Horizontal(classes="button-row"): 
                    yield Button("Back [B]", id="back", variant="default")
                    yield Static("    ", classes="button-spacer")
                    yield Button("Cancel Job [C]", id="cancel", variant="error")
        yield Footer()

    async def on_mount(self) -> None:
        if self.cancel_on_mount:
            await self.action_cancel()
        self.refresh_detail()
        self.set_interval(1.0, self.refresh_detail)

    def refresh_detail(self) -> None:
        try:
            item = manifest.load(self.job_dir / "manifest.json")
        except Exception as exc:
            self.query_one("#sum-source", Static).update(f"Error: {exc}")
            return

        dest = item["destination"]
        source = item["source"]
        state = item["state"]

        self.query_one("#sum-source", Static).update(
            source.get("table_name") or source.get("sql_path_at_launch") or source.get("type", "--")
        )
        schema = dest.get("schema", "")
        table = dest.get("table_name", "")
        full_table = f"{schema}.{table}" if schema and table else dest.get("type", "--")
        self.query_one("#sum-dest", Static).update(full_table)

        if state == "Running":
            self.query_one("#sum-state", Static).update("[green]\u25cf RUNNING[/]")
            self.query_one("#log-streaming", Static).update(
                "[green]Streaming logs\u2026 (auto-scroll) \u25cf[/]"
            )
        elif state == "Succeeded":
            self.query_one("#sum-state", Static).update("[green]\u25cf SUCCEEDED[/]")
            self.query_one("#log-streaming", Static).update("[dim]Complete[/]")
        elif state == "Failed":
            self.query_one("#sum-state", Static).update("[red]\u25cf FAILED[/]")
            self.query_one("#log-streaming", Static).update("[red]Failed[/]")
        elif state == "Cancelled":
            self.query_one("#sum-state", Static).update("[dim]\u25cf CANCELLED[/]")
            self.query_one("#log-streaming", Static).update("[dim]Cancelled[/]")
        else:
            self.query_one("#sum-state", Static).update(state)
            self.query_one("#log-streaming", Static).update("")

        self.query_one("#sum-started", Static).update(item.get("started_at") or "--")
        self.query_one("#sum-elapsed", Static).update(self._format_elapsed(item))
        self.query_one("#sum-table", Static).update(full_table)
        csv_path = dest.get("csv_path") or ""
        if dest.get("type") in ("Csv", "Table+Csv") and csv_path:
            self.query_one("#sum-csv", Static).update(csv_path)
        else:
            self.query_one("#sum-csv", Static).update("[dim]N/A (table-only)[/]")

        self._update_log()

        status_parts = []
        if state == "Running":
            status_parts.append("[green]Job is RUNNING[/]")
        elif state == "Succeeded":
            status_parts.append("[green]Job SUCCEEDED[/]")
        elif state == "Failed":
            status_parts.append(f"[red]Job FAILED (exit {item.get('exit_code', '?')})[/]")
        elif state == "Cancelled":
            status_parts.append("[dim]Job CANCELLED[/]")
        if item.get("finished_at"):
            status_parts.append(f"Finished: {item['finished_at']}")
        self.query_one("#job-status-line", Static).update("  ".join(status_parts))

    @staticmethod
    def _format_elapsed(item: dict) -> str:
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
        total = int(delta.total_seconds())
        if total < 60:
            return f"{total}s"
        minutes = total // 60
        if minutes < 60:
            return f"{minutes}m {total % 60}s"
        hours = minutes // 60
        return f"{hours}h {minutes % 60}m"

    def _update_log(self) -> None:
        path = self.job_dir / "run.log"
        if not path.exists():
            return
        try:
            size = path.stat().st_size
        except OSError:
            return
        if size < self._tail_offset:
            self._tail_offset = 0
            self._tail_lines.clear()
            self._last_line_count = 0
        if size > self._tail_offset:
            log_widget = self.query_one("#log-display", RichLog)
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                handle.seek(self._tail_offset)
                for line in handle:
                    stripped = line.rstrip()
                    self._tail_lines.append(stripped)
                    styled = self._style_log_line(stripped)
                    log_widget.write(styled)
                self._tail_offset = handle.tell()

    @staticmethod
    def _style_log_line(line: str) -> str:
        """Dim timestamp prefixes in log lines for visual separation."""
        if line.startswith("[") and "]" in line:
            idx = line.index("]") + 1
            return f"[dim]{line[:idx]}[/]{line[idx:]}"
        return line

    async def action_cancel(self) -> None:
        try:
            item = manifest.load(self.job_dir / "manifest.json")
        except Exception:
            return
        pid = item.get("pid")
        if item["state"] == "Running" and pid:
            confirmed = await self._confirm_cancel(item["id"], pid)
            if not confirmed:
                return
            process.cancel_process_group(pid)
            self.notify(f"Cancellation requested for Job {item['id']}", severity="warning")
            self.query_one("#job-status-line", Static).update(
                "[yellow]Cancellation requested\u2026[/]"
            )

    async def _confirm_cancel(self, job_id: str, pid: int) -> bool:
        loop_future: asyncio.Future[bool] = asyncio.get_running_loop().create_future()

        def on_result(result: bool | None) -> None:
            if not loop_future.done():
                loop_future.set_result(bool(result))

        self.app.push_screen(
            ConfirmScreen(
                "Cancel Job",
                (
                    f"Cancel Job [cyan]{job_id}[/]?\n\n"
                    f"This sends SIGTERM to process group PID [bold]{pid}[/]."
                ),
                danger=True,
                confirm_label="Cancel Job",
                cancel_label="Keep Running",
            ),
            callback=on_result,
        )
        return await loop_future

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            await self.action_cancel()
        elif event.button.id == "back":
            self.app.pop_screen()
