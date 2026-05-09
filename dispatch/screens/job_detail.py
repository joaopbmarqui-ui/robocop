"""Job detail and live-tail screen."""

from __future__ import annotations

from collections import deque

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from .. import config, manifest, process


class JobDetailScreen(Screen[None]):
    BINDINGS = [
        ("b", "app.pop_screen", "Back"),
        ("c", "cancel", "Cancel"),
    ]

    def __init__(self, job_id: str, cancel_on_mount: bool = False) -> None:
        super().__init__()
        self.job_id = job_id
        self.cancel_on_mount = cancel_on_mount

    @property
    def job_dir(self):
        return config.jobs_dir() / self.job_id

    def compose(self) -> ComposeResult:
        with Vertical(id="job-detail"):
            yield Static(f"Job {self.job_id}", id="summary")
            yield Static("", id="log")
            yield Button("Cancel Job", id="cancel", variant="error")
            yield Button("Back", id="back")

    def on_mount(self) -> None:
        if self.cancel_on_mount:
            self.action_cancel()
        self.refresh_detail()
        self.set_interval(1.0, self.refresh_detail)

    def refresh_detail(self) -> None:
        try:
            item = manifest.load(self.job_dir / "manifest.json")
        except Exception as exc:
            self.query_one("#summary", Static).update(f"Job {self.job_id}: {exc}")
            return
        destination = item["destination"]
        summary = [
            f"Source: {item['source']['type']}    Destination: {destination['type']}",
            f"State: {item['state']}    Started: {item['started_at']}",
        ]
        if "schema" in destination:
            summary.append(f"Table: {destination.get('schema')}.{destination.get('table_name')}")
        if destination.get("csv_path"):
            summary.append(f"CSV: {destination['csv_path']}")
        self.query_one("#summary", Static).update("\n".join(summary))
        self.query_one("#log", Static).update(self._tail())

    def _tail(self) -> str:
        path = self.job_dir / "run.log"
        if not path.exists():
            return "run.log not created yet"
        lines: deque[str] = deque(maxlen=80)
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                lines.append(line.rstrip())
        return "\n".join(lines)

    def action_cancel(self) -> None:
        item = manifest.load(self.job_dir / "manifest.json")
        pid = item.get("pid")
        if item["state"] == "Running" and pid:
            process.cancel_process_group(pid)
            self.query_one("#log", Static).update("Cancellation requested")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.action_cancel()
        elif event.button.id == "back":
            self.app.pop_screen()
