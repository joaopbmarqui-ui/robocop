"""Textual application shell for Dispatch."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Static

from . import config
from .version import __version__
from .screens.dashboard import DashboardScreen


class DispatchApp(App[None]):
    """Server-side TUI for Impala Job launch and supervision."""

    CSS = """
    Screen {
        align: center middle;
    }

    #startup {
        width: 80;
        border: round $primary;
        padding: 1 2;
    }

    .muted {
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.launch_cwd = Path.cwd()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="startup"):
            yield Static(f"Dispatch v{__version__}", id="title")
            yield Static("Server-side Impala Job launcher")
            yield Static(f"Launch-time CWD: {self.launch_cwd}", classes="muted")
            yield Static(self._version_banner(), id="version-banner")
        yield Footer()

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen(self.launch_cwd))

    def _version_banner(self) -> str:
        try:
            installed = config.installed_version_path().read_text(encoding="utf-8").strip()
        except OSError:
            return "Install state: missing config/version; run install.sh"
        if installed != __version__:
            return f"Warning: installed version {installed}, deployed version {__version__}"
        return "Install state: current"
