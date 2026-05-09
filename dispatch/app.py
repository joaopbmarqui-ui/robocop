"""Textual application shell for Dispatch."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Static

from .version import __version__
from .screens.new_job import NewJobScreen


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
        ("n", "new_job", "New Job"),
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
            yield Static("[N]ew Job  [Q]uit")
        yield Footer()

    def action_new_job(self) -> None:
        self.push_screen(NewJobScreen(self.launch_cwd))
