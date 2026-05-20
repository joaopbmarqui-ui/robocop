"""Textual application shell for Dispatch."""

from __future__ import annotations

import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Header, Static

from . import config, kerberos, setup_logging
from .screens.browser import BrowserScreen
from .version import __version__
from .screens.dashboard import DashboardScreen
from .screens.help import HelpScreen
from .screens.history import HistoryScreen
from .screens.job_detail import JobDetailScreen
from .screens.new_job import NewJobScreen
from .screens.sidebar import NavItem

logger = logging.getLogger("dispatch.app")

APP_CSS = """
/* ── Global ── */
Screen {
    layout: horizontal;
    background: $surface;
}

/* ── Sidebar ── */
Sidebar {
    width: 28;
    dock: left;
    background: #111111;
    border-right: vkey $primary-background-darken-2;
}

#sidebar-inner {
    height: 1fr;
}

#sidebar-brand {
    padding: 1 2;
    text-style: bold;
    color: $text;
    background: #0d0d0d;
}

#sidebar-nav {
    padding: 1 0;
    height: auto;
}

NavItem {
    padding: 0 2;
    height: 3;
    content-align-vertical: middle;
    color: $text-muted;
}

NavItem:hover {
    background: $primary 15%;
    color: $text;
}

NavItem.nav-active {
    background: $primary 30%;
    color: $text;
    text-style: bold;
}

#sidebar-footer {
    dock: bottom;
    height: auto;
    padding: 1 2;
}

/* ── Main content area ── */
#main-content {
    width: 1fr;
}

/* ── Stats row ── */
#stats-row {
    layout: horizontal;
    height: auto;
    padding: 1 0;
}

.stat-card {
    width: 1fr;
    height: auto;
    border: round $primary-background-darken-1;
    padding: 0 1;
    margin: 0 1;
    content-align: center middle;
}

.stat-card .stat-label {
    color: $accent;
    text-style: bold;
    text-align: center;
}

.stat-card .stat-value {
    text-align: center;
    text-style: bold;
}

.stat-card .stat-sub {
    color: $text-muted;
    text-align: center;
}

.stat-green {
    color: $success;
}

.stat-red {
    color: $error;
}

.stat-yellow {
    color: $warning;
}

/* ── Section headers ── */
.section-title {
    color: $accent;
    text-style: bold;
    padding: 1 1 0 1;
}

/* ── Tables ── */
DataTable {
    height: auto;
    max-height: 16;
    margin: 0 1;
    scrollbar-size: 1 1;
}

DataTable > .datatable--header {
    text-style: bold;
    color: $accent;
}

/* ── Job ID input section ── */
#job-id-section {
    height: auto;
    padding: 0 1;
    margin: 1 0 0 0;
}

#job-id-section Static {
    color: $accent;
}

/* ── Button rows ── */
.button-row {
    layout: horizontal;
    height: auto;
    padding: 1 1;
    align-horizontal: center;
}

.button-row Button {
    margin: 0 1;
}

.button-spacer {
    width: 4;
    height: auto;
}

/* ── Show-more link ── */
.show-more {
    text-align: right;
    padding: 0 2;
    color: $text-muted;
}

/* ── Dashboard ── */
#dashboard-content {
    height: 1fr;
    overflow-y: auto;
    padding: 0;
}

/* ── Empty state panels ── */
.empty-state {
    height: auto;
    padding: 2 4;
    margin: 1 2;
    content-align: center middle;
    text-align: center;
    color: $text-muted;
    border: dashed $primary-background-darken-2;
}

.empty-state .empty-icon {
    text-align: center;
    color: $primary-background-darken-1;
}

.empty-state .empty-hint {
    color: $text-muted;
    text-align: center;
}

/* ── New Job screen ── */
#new-job-content {
    height: 1fr;
    overflow-y: auto;
    padding: 0 1;
}

#matrix-panel {
    height: auto;
    padding: 1;
    margin: 1;
    border: round $primary-background-darken-1;
}

#matrix-panel .section-title {
    padding: 0 0 1 0;
}

#matrix-table {
    height: auto;
    max-height: 6;
    margin: 0;
}

#radio-panel {
    height: auto;
    margin: 0 1 1 1;
}

#radio-row {
    height: auto;
}

.radio-group {
    width: 1fr;
    height: auto;
    padding: 0 1;
}

.radio-group .field-label {
    color: $accent;
    text-style: bold;
    height: 1;
    margin: 0 0 1 0;
}

.path-hint {
    color: $text-muted;
    padding: 0 0 0 22;
    height: 1;
    overflow: hidden;
}

Button:disabled {
    opacity: 0.4;
}

#describe-table {
    height: 1fr;
    margin: 0;
}

#info-panel {
    height: auto;
    padding: 1;
    margin: 0 1;
    border: round $accent 30%;
}

#info-panel Static {
    height: auto;
}

.info-text {
    color: $text-muted;
}

.warn-text {
    color: $warning;
}

#form-grid {
    height: auto;
    padding: 1;
}

.form-row {
    height: auto;
    margin: 0 0 1 0;
    align-vertical: middle;
}

.form-row .field-label {
    width: 22;
    color: $accent;
    height: 3;
    content-align-vertical: middle;
}

.form-row Input {
    width: 1fr;
    height: 3;
}

#kerberos-status {
    color: $text-muted;
    padding: 0 1;
    text-align: right;
    dock: top;
    height: 1;
}

#warning-text {
    height: auto;
    padding: 0 1;
    color: $warning;
}

#launch-info {
    color: $text-muted;
    padding: 0 2;
    height: auto;
}

/* ── Preview screen ── */
#preview-content {
    height: 1fr;
    padding: 0;
}

#preview-header {
    height: auto;
    padding: 1 2;
    layout: horizontal;
    background: $surface-darken-1;
}

#preview-header Static {
    width: 1fr;
}

#preview-meta {
    text-align: right;
    color: $accent;
}

#sql-display {
    height: 1fr;
    min-height: 6;
    margin: 0 1;
    border: round $primary-background-darken-1;
    overflow-y: auto;
}

#sql-display RichLog {
    height: 1fr;
    padding: 0 1;
}

#sql-display Static {
    padding: 0 1;
}

#preview-footer-info {
    height: auto;
    layout: horizontal;
    padding: 1;
    background: $surface-darken-1;
    margin: 0 1;
}

#preview-footer-info Static {
    width: 1fr;
    padding: 0 1;
    color: $text-muted;
}

/* ── Job Detail screen ── */
#job-detail-content {
    height: 1fr;
    padding: 0;
}

#job-summary-panel {
    height: auto;
    max-height: 14;
    padding: 1;
    margin: 1;
    border: round $primary-background-darken-1;
    overflow-y: auto;
}

#job-summary-panel .section-title {
    padding: 0 0 1 0;
}

#summary-grid {
    layout: horizontal;
    height: auto;
}

#summary-grid Vertical {
    width: 1fr;
}

#summary-grid Static {
    height: auto;
}

.summary-label {
    color: $text-muted;
}

.summary-value {
    color: $text;
}

#log-header {
    layout: horizontal;
    height: auto;
    padding: 0 1;
}

#log-header Static {
    width: 1fr;
}

#log-streaming {
    text-align: right;
    color: $success;
}

#log-panel {
    height: 1fr;
    margin: 0 1;
    border: round $primary-background-darken-1;
    overflow-y: auto;
    padding: 0 1;
    min-height: 8;
}

#log-panel RichLog {
    height: 1fr;
}

#job-status-line {
    height: auto;
    padding: 0 2;
}

/* ── History screen ── */
#history-content {
    height: 1fr;
    padding: 0;
}

#search-row {
    layout: horizontal;
    height: auto;
    padding: 1;
}

#search-row Input {
    width: 1fr;
    margin: 0 1;
}

#search-label {
    width: auto;
    height: 3;
    content-align-vertical: middle;
    padding: 0 1;
    color: $text-muted;
}

#history-table {
    height: 1fr;
    margin: 0 1;
}

#pagination {
    layout: horizontal;
    height: auto;
    padding: 0 2;
}

#page-info {
    width: 1fr;
    color: $text-muted;
}

#page-controls {
    width: 1fr;
    text-align: right;
    color: $text-muted;
}

/* ── Browser screen ── */
#browser-content {
    height: 1fr;
    padding: 0;
}

#browser-split {
    layout: horizontal;
    height: 1fr;
}

#browser-left {
    width: 3fr;
    margin: 0 1;
}

#browser-right {
    width: 2fr;
    margin: 0 1;
    border-left: vkey $primary-background-darken-2;
    padding: 0 1;
}

#browser-left DataTable {
    height: 1fr;
}

#file-preview-title {
    color: $accent;
    text-style: bold;
    padding: 1 0 0 0;
}

#file-preview-path {
    color: $text-muted;
    padding: 0;
}

#file-meta {
    height: auto;
    padding: 1 0;
}

#file-meta Static {
    height: auto;
    color: $text-muted;
}

#file-preview-code {
    height: 1fr;
    border: round $primary-background-darken-1;
    overflow-y: auto;
    padding: 0 1;
}

#browser-status {
    layout: horizontal;
    height: auto;
    padding: 0 1;
}

#browser-status Static {
    width: 1fr;
}

#browser-count {
    text-align: right;
    color: $text-muted;
}

#browser-help {
    color: $text-muted;
    padding: 0 1;
}

/* ── Startup splash ── */
#startup {
    width: 80;
    border: round $primary;
    padding: 1 2;
}

/* ── Version-mismatch banner ── */
#version-warning {
    background: $warning 80%;
    color: $text;
    padding: 0 2;
    height: auto;
    text-align: center;
    text-style: bold;
}

/* ── Kerberos indicator ── */
KerberosIndicator {
    dock: right;
    width: auto;
    padding: 0 2;
    color: $text-muted;
}

KerberosIndicator.krb-missing {
    color: $error;
    text-style: bold;
}

KerberosIndicator.krb-low {
    color: $warning;
}

.muted {
    color: $text-muted;
}

/* ── Confirmation modal ── */
ConfirmScreen {
    align: center middle;
}

#confirm-dialog {
    width: 60;
    height: auto;
    border: double $primary;
    padding: 1 2;
    background: $surface;
}

#confirm-dialog.danger {
    border: double $error;
}

#confirm-title {
    height: auto;
    padding: 0 0 1 0;
}

#confirm-body {
    height: auto;
    padding: 0 0 1 0;
}

#confirm-help {
    height: auto;
    color: $text-muted;
    padding: 0 0 1 0;
}

#confirm-buttons {
    height: auto;
    align: center middle;
    padding: 1 0 0 0;
}

#confirm-buttons Button {
    margin: 0 1;
}

/* ── Help modal ── */
HelpScreen {
    align: center middle;
}

#help-dialog {
    width: 60;
    height: auto;
    max-height: 80%;
    border: double $primary;
    padding: 1 2;
    background: $surface;
    overflow-y: auto;
}

#help-body {
    height: auto;
}

#help-quick {
    height: auto;
    padding: 0 0 1 0;
    margin: 0 0 1 0;
    border-bottom: solid $primary-background-darken-2;
    color: $text-muted;
}
"""


class KerberosIndicator(Static):
    """Persistent header widget showing current Kerberos TTL."""

    ttl_seconds: reactive[int | None] = reactive(None)

    def render(self) -> str:
        if self.ttl_seconds is None:
            return "Kerberos: MISSING"
        hours, remainder = divmod(self.ttl_seconds, 3600)
        minutes = remainder // 60
        return f"Kerberos: {hours}h {minutes:02d}m"

    def watch_ttl_seconds(self, value: int | None) -> None:
        self.remove_class("krb-missing", "krb-low")
        if value is None:
            self.add_class("krb-missing")
        elif value < 3600:
            self.add_class("krb-low")


class DispatchApp(App[None]):
    """Server-side TUI for Impala Job launch and supervision."""

    CSS = APP_CSS

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("question_mark", "help", "Help"),
    ]

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def __init__(self) -> None:
        super().__init__()
        setup_logging()
        self.launch_cwd = Path.cwd()
        logger.info(
            "Dispatch %s starting, cwd=%s, data_root=%s",
            __version__, self.launch_cwd, config.data_root(),
        )

    def compose(self) -> ComposeResult:
        yield Static("", id="version-warning", markup=True)
        yield KerberosIndicator(id="krb-indicator")

    async def on_mount(self) -> None:
        version_warning = self._build_version_warning()
        w = self.query_one("#version-warning", Static)
        if version_warning:
            w.update(version_warning)
        else:
            w.display = False

        if not config.dispatch_home().exists():
            logger.error("Dispatch home %s does not exist", config.dispatch_home())
            self.notify(
                "Dispatch is not installed for this user. "
                "Run install.sh to set up.",
                severity="error",
                timeout=0,
            )

        if self.size.width < 80 or self.size.height < 24:
            self.notify(
                f"Terminal too small ({self.size.width}\u00d7{self.size.height}). "
                "Minimum: 80\u00d724. Some layouts may break.",
                severity="warning",
                timeout=0,
            )

        self.push_screen(DashboardScreen(self.launch_cwd))
        await self._refresh_kerberos_indicator()
        self.set_interval(60.0, self._refresh_kerberos_indicator)

    def on_resize(self) -> None:
        if self.size.width < 80 or self.size.height < 24:
            self.notify(
                f"Terminal too small ({self.size.width}\u00d7{self.size.height}). "
                "Minimum: 80\u00d724.",
                severity="warning",
            )

    async def _refresh_kerberos_indicator(self) -> None:
        ttl = await kerberos.ticket_ttl_seconds()
        self.query_one(KerberosIndicator).ttl_seconds = ttl

    def _build_version_warning(self) -> str:
        try:
            installed = config.installed_version_path().read_text(encoding="utf-8").strip()
        except OSError:
            return f"\u26a0 Install incomplete: version file missing. Run install.sh. (running {__version__})"
        if installed != __version__:
            return f"\u26a0 Version mismatch: installed {installed}, running {__version__}. Run install.sh."
        return ""

    def on_nav_item_selected(self, event: NavItem.Selected) -> None:
        item_id = event.item_id
        current = self.screen

        # If we are selecting the item we are already on, do nothing
        if item_id == "overview" and isinstance(current, DashboardScreen):
            return
        if item_id == "new_job" and isinstance(current, NewJobScreen):
            return
        if item_id == "history" and isinstance(current, HistoryScreen):
            return
        if item_id == "browse" and isinstance(current, BrowserScreen):
            return
        if item_id == "view_logs" and isinstance(current, JobDetailScreen):
            return

        if item_id == "view_logs":
            job_id = self._sidebar_selected_job_id(current)
            if job_id and job_id != "__empty__":
                self.call_after_refresh(self._navigate_from_sidebar, "view_logs", job_id)
            else:
                self.notify(
                    "Please select a job from the Overview or History table first.",
                    severity="warning",
                )
            return

        self.call_after_refresh(self._navigate_from_sidebar, item_id, None)

    def _navigate_from_sidebar(self, item_id: str, job_id: str | None) -> None:
        self._pop_to_dashboard()

        if item_id == "overview":
            return
        if item_id == "new_job":
            self.push_screen(NewJobScreen(self.launch_cwd))
        elif item_id == "history":
            self.push_screen(HistoryScreen())
        elif item_id == "browse":
            self.push_screen(BrowserScreen())
        elif item_id == "view_logs" and job_id:
            self.push_screen(JobDetailScreen(job_id))

    def _pop_to_dashboard(self) -> None:
        while len(self.screen_stack) > 2:
            self.pop_screen()

    @staticmethod
    def _sidebar_selected_job_id(current: object) -> str | None:
        if isinstance(current, DashboardScreen):
            return current._selected_job_id()
        if isinstance(current, HistoryScreen):
            return current._selected_job_id()
        return None
