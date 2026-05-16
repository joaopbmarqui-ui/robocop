"""New Job wizard screen."""

from __future__ import annotations

import calendar
import os
from datetime import date
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, RadioButton, RadioSet, Static

from .. import config, jobs, kerberos, manifest, process, sql
from .preview import PreviewScreen
from .sidebar import NavItem, Sidebar

_SOURCE_IDS = {"src-sqlfile": "SqlFile", "src-sqltemplate": "SqlTemplate", "src-existingtable": "ExistingTable"}
_DEST_IDS = {"dst-table": "Table", "dst-csv": "Csv", "dst-table-csv": "Table+Csv"}


class NewJobScreen(Screen[None]):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("b", "app.pop_screen", "Back"),
        ("e", "edit_sql", "Edit SQL"),
        ("k", "kinit", "kinit"),
        ("l", "launch", "Launch"),
        ("p", "preview", "Preview SQL"),
    ]

    def __init__(self, launch_cwd: Path) -> None:
        super().__init__()
        self.launch_cwd = launch_cwd
        self.kerberos_ttl: int | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        sidebar = Sidebar()
        sidebar.active_screen = "new_job"
        yield sidebar
        with Vertical(id="main-content"):
            yield Static("", id="kerberos-status")
            with Vertical(id="new-job-content"):
                yield Static("New Job", classes="section-title")

                with Vertical(id="matrix-panel"):
                    yield Static("Source \u00d7 Destination legal cells", classes="section-title")
                    yield DataTable(id="matrix-table")

                with Vertical(id="info-panel"):
                    yield Static(
                        "[bold cyan]\u24d8[/] Auto-detected source type: [cyan]SqlFile \u2192 Table[/]",
                        id="info-detected",
                    )
                    yield Static(
                        "[yellow]\u26a0[/] Ensure the combination above matches your "
                        "source and destination selection.",
                        classes="warn-text",
                    )

                with Vertical(id="radio-panel"):
                    with Horizontal(id="radio-row"):
                        with Vertical(classes="radio-group"):
                            yield Static("Source", classes="field-label")
                            with RadioSet(id="source"):
                                yield RadioButton("SqlFile", value=True, id="src-sqlfile")
                                yield RadioButton("SqlTemplate", id="src-sqltemplate")
                                yield RadioButton("ExistingTable", id="src-existingtable")
                        with Vertical(classes="radio-group"):
                            yield Static("Destination", classes="field-label")
                            with RadioSet(id="destination"):
                                yield RadioButton("Table", id="dst-table")
                                yield RadioButton("Csv", value=True, id="dst-csv")
                                yield RadioButton("Table+Csv", id="dst-table-csv")

                with Vertical(id="form-grid"):
                    yield Static("SQL File", classes="field-label", id="lbl-sql-file")
                    yield Input(value=self._default_sql_file(), placeholder="SQL File", id="sql-file")

                    yield Static("Existing Table", classes="field-label", id="lbl-existing-table")
                    yield Input(value="", placeholder="e.g. analytics.events_existing", id="existing-table")

                    yield Static("Schema", classes="field-label", id="lbl-schema")
                    yield Input(value="dw_settle", placeholder="Schema", id="schema")

                    yield Static("Table Name", classes="field-label", id="lbl-table-name")
                    yield Input(value="dispatch_result", placeholder="Table name", id="table-name")

                    yield Static("Start Date (YYYY-MM-DD)", classes="field-label", id="lbl-start-date")
                    yield Input(value=self._default_start_date(), placeholder="YYYY-MM-DD", id="start-date")

                    yield Static("End Date (YYYY-MM-DD)", classes="field-label", id="lbl-end-date")
                    yield Input(value=self._default_end_date(), placeholder="YYYY-MM-DD", id="end-date")

                    yield Static("Email (notifications)", classes="field-label", id="lbl-email")
                    yield Input(value="", placeholder="dataops@company.com", id="email")

                    yield Static("Subject (email)", classes="field-label", id="lbl-subject")
                    yield Input(value="Dispatch Job", placeholder="Subject line", id="subject")

                yield Static("", id="warning-text")

                with Horizontal(classes="button-row"):
                    yield Button("Preview SQL [P]", id="preview", variant="primary")
                    yield Button("Launch [L]", id="launch", variant="success")

                yield Static(
                    "[dim]\u24d8 Use Preview SQL to validate the generated statement before launching.\n"
                    "  Job will be submitted to Impala over SSH.[/]",
                    id="launch-info",
                )
        yield Footer()

    async def on_mount(self) -> None:
        matrix = self.query_one("#matrix-table", DataTable)
        matrix.add_columns("SOURCE \\ DEST", "TABLE", "CSV", "TABLE+CSV")
        matrix.add_row("SqlFile", "[green]\u2713[/]", "[green]\u2713[/]", "[green]\u2713[/]")
        matrix.add_row("SqlTemplate", "[green]\u2713[/]", "[dim]\u2014[/]", "[dim]\u2014[/]")
        matrix.add_row("ExistingTable", "[dim]\u2014[/]", "[green]\u2713[/]", "[dim]\u2014[/]")
        matrix.show_cursor = False

        self.kerberos_ttl = await kerberos.ticket_ttl_seconds()
        self._refresh_kerberos()
        self._detect_sql()
        self._update_field_visibility()

    @staticmethod
    def _default_start_date() -> str:
        today = date.today()
        return today.replace(day=1).isoformat()

    @staticmethod
    def _default_end_date() -> str:
        today = date.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        return today.replace(day=last_day).isoformat()

    def _default_sql_file(self) -> str:
        matches = sorted(self.launch_cwd.glob("*.sql"))
        return str(matches[0]) if matches else str(self.launch_cwd / "query.sql")

    def _input_value(self, widget_id: str) -> str:
        return self.query_one(f"#{widget_id}", Input).value.strip()

    def _selected_source(self) -> str:
        radio_set = self.query_one("#source", RadioSet)
        if radio_set.pressed_button is not None:
            return _SOURCE_IDS.get(radio_set.pressed_button.id or "", "SqlFile")
        return "SqlFile"

    def _selected_destination(self) -> str:
        radio_set = self.query_one("#destination", RadioSet)
        if radio_set.pressed_button is not None:
            return _DEST_IDS.get(radio_set.pressed_button.id or "", "Csv")
        return "Csv"

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self._update_field_visibility()

    def _update_field_visibility(self) -> None:
        source = self._selected_source()
        destination = self._selected_destination()

        dest_radio_set = self.query_one("#destination", RadioSet)
        for btn in dest_radio_set.query(RadioButton):
            dest_type = _DEST_IDS.get(btn.id or "", "")
            btn.disabled = (source, dest_type) not in manifest.LEGAL_CELLS

        is_sql = source in ("SqlFile", "SqlTemplate")
        is_existing = source == "ExistingTable"
        is_template = source == "SqlTemplate"
        needs_table = destination in ("Table", "Table+Csv") or is_template

        self.query_one("#lbl-sql-file", Static).display = is_sql
        self.query_one("#sql-file", Input).display = is_sql

        self.query_one("#lbl-existing-table", Static).display = is_existing
        self.query_one("#existing-table", Input).display = is_existing

        self.query_one("#lbl-schema", Static).display = needs_table
        self.query_one("#schema", Input).display = needs_table

        self.query_one("#lbl-table-name", Static).display = needs_table
        self.query_one("#table-name", Input).display = needs_table

        self.query_one("#lbl-start-date", Static).display = is_template
        self.query_one("#start-date", Input).display = is_template

        self.query_one("#lbl-end-date", Static).display = is_template
        self.query_one("#end-date", Input).display = is_template

    def _refresh_kerberos(self) -> None:
        label = self.query_one("#kerberos-status", Static)
        if self.kerberos_ttl is None:
            label.update("[yellow]Kerberos ticket missing \u2014 press K to kinit[/]")
        else:
            minutes = self.kerberos_ttl // 60
            label.update(f"[dim]Kerberos: {minutes}m remaining[/]")

    def _read_sql(self) -> str | None:
        sql_path = Path(self._input_value("sql-file"))
        try:
            return sql_path.read_text(encoding="utf-8")
        except OSError as exc:
            self._show_message(f"Cannot read SQL file: {sql_path}\n{exc}", "error")
            return None

    def _show_message(self, text: str, severity: str = "info") -> None:
        widget = self.query_one("#warning-text", Static)
        markup_map = {
            "error": "red",
            "warning": "yellow",
            "success": "green",
            "info": "dim",
        }
        color = markup_map.get(severity, "dim")
        widget.update(f"[{color}]{text}[/]")

    def _detect_sql(self) -> None:
        content = self._read_sql()
        if content is None:
            return
        detected = sql.detect_source(content)
        info = self.query_one("#info-detected", Static)
        info.update(f"[bold cyan]\u24d8[/] Auto-detected source type: [cyan]{detected}[/]")
        if detected == "SqlTemplate":
            self.query_one("#src-sqltemplate", RadioButton).value = True
        elif detected == "ExistingTable":
            self.query_one("#src-existingtable", RadioButton).value = True

    def _validate(self) -> str | None:
        source_type = self._selected_source()
        destination_type = self._selected_destination()
        if (source_type, destination_type) not in manifest.LEGAL_CELLS:
            return f"Illegal Source/Destination cell: {source_type}/{destination_type}"
        if not jobs.can_launch():
            return f"Already at the {jobs.RUNNING_CAP}-Job concurrency cap; wait for one to finish"
        if self.kerberos_ttl is None:
            return "Kerberos ticket missing"
        if self.kerberos_ttl < 300:
            return "Kerberos ticket TTL is under 5 minutes"
        if source_type == "ExistingTable":
            if not self._input_value("existing-table"):
                return "Existing table name is required"
            return None
        sql_text = self._read_sql()
        if sql_text is None:
            return "SQL file is unreadable"
        if sql.is_malformed_template(sql_text):
            return "SQL contains only one of {date_inicio}/{date_fim} \u2014 likely a typo"
        if source_type == "SqlTemplate" and not sql.template_is_complete(sql_text):
            return "SqlTemplate requires both {date_inicio} and {date_fim}"
        return None

    def _source_destination(self) -> tuple[manifest.Source, manifest.Destination]:
        source_type = self._selected_source()
        destination_type = self._selected_destination()
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
        if self._selected_source() == "SqlTemplate":
            params["start_date"] = sql.to_orchestrator_date(self._input_value("start-date"))
            params["end_date"] = sql.to_orchestrator_date(self._input_value("end-date"))
        return params

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "launch":
            await self.action_launch()
        elif event.button.id == "preview":
            self.action_preview()

    def action_preview(self) -> None:
        source_type = self._selected_source()
        schema = self._input_value("schema")
        table = self._input_value("table-name")
        if source_type == "ExistingTable":
            self._show_message("Preview is not available for ExistingTable source.", "warning")
            return
        sql_text = self._read_sql()
        if sql_text is None:
            return
        if source_type == "SqlTemplate":
            preview = sql.monthly_preview(
                sql_text, schema, table,
                self._input_value("start-date"),
                self._input_value("end-date"),
            )
        else:
            preview = sql.table_wrapper(sql_text, schema, table, config.current_user())
        self.app.push_screen(
            PreviewScreen("SQL Preview", preview, schema=schema, table=table)
        )

    async def action_launch(self) -> None:
        error = self._validate()
        if error:
            self._show_message(error, "error")
            return
        source_type = self._selected_source()
        if source_type == "ExistingTable":
            sql_text = ""
        else:
            sql_text = self._read_sql()
            if sql_text is None:
                return
        source, destination = self._source_destination()
        job_dir, _job_manifest = manifest.create_job(
            source=source,
            destination=destination,
            params=self._params(),
            launch_cwd=self.launch_cwd,
            sql_text=sql_text,
        )
        await process.launch_runner(job_dir)
        self._show_message(f"\u2713 Launched Job {job_dir.name}", "success")

    def action_edit_sql(self) -> None:
        editor = os.environ.get("EDITOR", "vi")
        with self.app.suspend():
            process.run_interactive(editor, self._input_value("sql-file"))
        self._detect_sql()

    async def action_kinit(self) -> None:
        with self.app.suspend():
            process.run_interactive("kinit")
        self.kerberos_ttl = await kerberos.ticket_ttl_seconds()
        self._refresh_kerberos()
        await self.app._refresh_kerberos_indicator()

    def on_nav_item_selected(self, event: NavItem.Selected) -> None:
        if event.item_id == "overview":
            self.app.pop_screen()
        elif event.item_id != "new_job":
            self.dismiss()
