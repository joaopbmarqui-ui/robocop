"""Sidebar navigation widget shared across all screens."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class NavItem(Static):
    """A single clickable navigation item."""

    class Selected(Message):
        def __init__(self, item_id: str) -> None:
            super().__init__()
            self.item_id = item_id

    active = reactive(False)

    def __init__(self, label: str, item_id: str, icon: str = "") -> None:
        self._label = label
        self._icon = icon
        super().__init__(self._display_text(label, icon, collapsed=False))
        self.item_id = item_id

    @staticmethod
    def _display_text(label: str, icon: str, collapsed: bool) -> str:
        if collapsed:
            return icon or label[:1]
        return f"{icon} {label}" if icon else label

    def set_collapsed(self, collapsed: bool) -> None:
        self.update(self._display_text(self._label, self._icon, collapsed))

    def on_click(self) -> None:
        self.post_message(self.Selected(self.item_id))

    def watch_active(self, value: bool) -> None:
        self.set_class(value, "nav-active")


# BMP Unicode symbols (SSH-safe, no multi-byte emoji)
NAV_ITEMS = [
    ("Overview", "overview", "\u2302"),
    ("New Job", "new_job", "\u229e"),
    ("View Logs", "view_logs", "\u25b8"),
    ("History", "history", "\u25f7"),
    ("Browse", "browse", "\u2630"),
]


class Sidebar(Widget):
    """Left-side navigation panel."""

    active_screen = reactive("overview")
    collapsed = reactive(False)

    def compose(self) -> ComposeResult:
        with Vertical(id="sidebar-inner"):
            yield Static("robocop / [bold cyan]Dispatch[/]", id="sidebar-brand")
            with Vertical(id="sidebar-nav"):
                for label, item_id, icon in NAV_ITEMS:
                    yield NavItem(label, item_id, icon)
            with Vertical(id="sidebar-footer"):
                yield Static("[dim]? Help[/]", id="sidebar-help")

    def on_mount(self) -> None:
        self._sync_collapse_from_app()
        self.watch(self.app, "size", self._on_app_resize, init=False)

    def _on_app_resize(self) -> None:
        self._sync_collapse_from_app()

    def _sync_collapse_from_app(self) -> None:
        if self.app is None:
            return
        auto_collapsed = self.app.size.width < 100
        if auto_collapsed != self.collapsed:
            self.collapsed = auto_collapsed

    def toggle_collapsed(self) -> None:
        self.collapsed = not self.collapsed

    def watch_collapsed(self, value: bool) -> None:
        self.set_class(value, "sidebar-collapsed")
        brand = self.query_one("#sidebar-brand", Static)
        if value:
            brand.update("[bold cyan]D[/]")
        else:
            brand.update("robocop / [bold cyan]Dispatch[/]")
        help_line = self.query_one("#sidebar-help", Static)
        help_line.update("[dim]?[/]" if value else "[dim]? Help[/]")
        for child in self.query(NavItem):
            child.set_collapsed(value)

    def watch_active_screen(self, value: str) -> None:
        for child in self.query(NavItem):
            child.active = child.item_id == value
