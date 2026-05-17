"""Textual application shell for Dispatch."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

from . import config, kerberos
from .version import __version__
from .screens.dashboard import DashboardScreen

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
    max-height: 8;
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
    layout: grid;
    grid-size: 2 6;
    grid-gutter: 1;
    height: auto;
    padding: 1;
    grid-columns: 1fr 1fr;
}

#form-grid .field-label {
    color: $accent;
    height: 1;
    padding: 0;
}

#form-grid Input {
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
    margin: 0 1;
    border: round $primary-background-darken-1;
    overflow-y: auto;
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
    padding: 1;
    margin: 1;
    border: round $primary-background-darken-1;
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
    ]

    def __init__(self) -> None:
        super().__init__()
        self.launch_cwd = Path.cwd()

    def compose(self) -> ComposeResult:
        yield Static("", id="version-warning", markup=True)
        yield Header(show_clock=True)
        yield KerberosIndicator(id="krb-indicator")
        yield Footer()

    async def on_mount(self) -> None:
        version_warning = self._build_version_warning()
        w = self.query_one("#version-warning", Static)
        if version_warning:
            w.update(version_warning)
        else:
            w.display = False
        self.push_screen(DashboardScreen(self.launch_cwd))
        await self._refresh_kerberos_indicator()
        self.set_interval(60.0, self._refresh_kerberos_indicator)

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
