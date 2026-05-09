"""New Job wizard screen."""

from __future__ import annotations

import os
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from .. import config, kerberos, manifest, process, sql


class NewJobScreen(Screen[None]):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("e", "edit_sql", "Edit"),
        ("k", "kinit", "kinit"),
        ("l", "launch", "Launch"),
        ("p", "preview", "Preview"),
    ]

    def __init__(self, launch_cwd: Path) -> None:
        super().__init__()
        self.launch_cwd = launch_cwd
        self.source_type = "SqlFile"
        self.destination_type = "Csv"
        self.kerberos_ttl: int | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="new-job"):
            yield Static("New Job")
            yield Static(self._matrix_text(), id="matrix")
            yield Input(value=self._default_sql_file(), placeholder="SQL File", id="sql-file")
            yield Input(value=self.source_type, placeholder="Source", id="source")
            yield Input(value=self.destination_type, placeholder="Destination", id="destination")
            yield Input(value="dw_settle", placeholder="Schema", id="schema")
            yield Input(value="dispatch_result", placeholder="Table name", id="table-name")
            yield Input(value="", placeholder="Existing table as schema.table", id="existing-table")
            yield Input(value="", placeholder="Email", id="email")
            yield Input(value="Dispatch Job", placeholder="Subject", id="subject")
            yield Input(value="2026-01-01", placeholder="Start date YYYY-MM-DD", id="start-date")
            yield Input(value="2026-01-31", placeholder="End date YYYY-MM-DD", id="end-date")
            yield Static("Kerberos: checking", id="kerberos")
            yield Static("", id="warning")
            yield Button("Preview SQL", id="preview", variant="primary")
            yield Button("Launch", id="launch", variant="success")

    async def on_mount(self) -> None:
        self.kerberos_ttl = await kerberos.ticket_ttl_seconds()
        self._refresh_kerberos()
        self._detect_sql()

    def _default_sql_file(self) -> str:
        matches = sorted(self.launch_cwd.glob("*.sql"))
        return str(matches[0]) if matches else str(self.launch_cwd / "query.sql")

    def _matrix_text(self) -> str:
        return (
            "Source x Destination legal cells:\n"
            "SqlFile: Table | Csv | Table+Csv\n"
            "SqlTemplate: Table\n"
            "ExistingTable: Csv"
        )

    def _input_value(self, widget_id: str) -> str:
        return self.query_one(f"#{widget_id}", Input).value.strip()

    def _refresh_kerberos(self) -> None:
        label = self.query_one("#kerberos", Static)
        if self.kerberos_ttl is None:
            label.update("Kerberos ticket missing - press K to kinit")
        else:
            minutes = self.kerberos_ttl // 60
            label.update(f"Kerberos: {minutes}m remaining")

    def _read_sql(self) -> str:
        sql_path = Path(self._input_value("sql-file"))
        return sql_path.read_text(encoding="utf-8")

    def _detect_sql(self) -> None:
        try:
            detected = sql.detect_source(self._read_sql())
        except OSError:
            return
        self.query_one("#warning", Static).update(f"Auto-detected: {detected}")
        self.query_one("#source", Input).value = detected

    def _validate(self) -> str | None:
        source_type = self._input_value("source")
        destination_type = self._input_value("destination")
        if (source_type, destination_type) not in manifest.LEGAL_CELLS:
            return f"Illegal Source/Destination cell: {source_type}/{destination_type}"
        if self.kerberos_ttl is None:
            return "Kerberos ticket missing"
        if self.kerberos_ttl < 300:
            return "Kerberos ticket TTL is under 5 minutes"
        if source_type == "SqlTemplate" and not sql.template_is_complete(self._read_sql()):
            return "SqlTemplate requires both {date_inicio} and {date_fim}"
        return None

    def _source_destination(self) -> tuple[manifest.Source, manifest.Destination]:
        source_type = self._input_value("source")
        destination_type = self._input_value("destination")
        schema = self._input_value("schema")
        table = self._input_value("table-name")
        if source_type == "ExistingTable":
            existing = self._input_value("existing-table") or f"{schema}.{table}"
            source: manifest.Source = {"type": "ExistingTable", "table_name": existing}
            if "." in existing:
                schema, table = existing.split(".", 1)
        else:
            source = {"type": source_type, "sql_path_at_launch": self._input_value("sql-file")}
        csv_path = str(self.launch_cwd / f"{table}.csv")
        destination: manifest.Destination = {
            "type": destination_type,
            "schema": schema,
            "table_name": table,
            "csv_path": csv_path,
        }
        return source, destination

    def _params(self) -> dict[str, str]:
        params = {"to_email": self._input_value("email"), "subject": self._input_value("subject")}
        if self._input_value("source") == "SqlTemplate":
            params["start_date"] = sql.to_orchestrator_date(self._input_value("start-date"))
            params["end_date"] = sql.to_orchestrator_date(self._input_value("end-date"))
        return params

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "launch":
            await self.action_launch()
        elif event.button.id == "preview":
            self.action_preview()

    def action_preview(self) -> None:
        source_type = self._input_value("source")
        schema = self._input_value("schema")
        table = self._input_value("table-name")
        sql_text = self._read_sql()
        if source_type == "SqlTemplate":
            preview = sql.monthly_preview(
                sql_text,
                schema,
                table,
                self._input_value("start-date"),
                self._input_value("end-date"),
            )
        else:
            preview = sql.table_wrapper(sql_text, schema, table, config.current_user())
        self.query_one("#warning", Static).update(preview[:1500])

    async def action_launch(self) -> None:
        error = self._validate()
        if error:
            self.query_one("#warning", Static).update(error)
            return
        source, destination = self._source_destination()
        job_dir, _job_manifest = manifest.create_job(
            source=source,
            destination=destination,
            params=self._params(),
            launch_cwd=self.launch_cwd,
            sql_text=self._read_sql(),
        )
        await process.launch_runner(job_dir)
        self.query_one("#warning", Static).update(f"Launched Job {job_dir.name}")

    def action_edit_sql(self) -> None:
        editor = os.environ.get("EDITOR", "vi")
        with self.app.suspend():
            process.run_interactive(editor, self._input_value("sql-file"))
        self._detect_sql()

    def action_kinit(self) -> None:
        with self.app.suspend():
            process.run_interactive("kinit")
