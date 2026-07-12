"""Advisor launch-gate modal — error findings only, explicit proceed/cancel."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from dispatch.advisor.models import Finding, finding_markup


class AdvisorLaunchGate(ModalScreen[bool]):
    """Enforcement ceiling: errors pause here; proceed launches SQL as written."""

    BINDINGS = [
        ("y", "proceed", "Launch anyway"),
        ("n", "cancel", "Cancel"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, errors: tuple[Finding, ...] | list[Finding]) -> None:
        super().__init__()
        self.errors = tuple(errors)

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog", classes="danger"):
            yield Static("[bold red]Advisor found error findings[/]", id="confirm-title")
            body = "\n\n".join(finding_markup(f) for f in self.errors)
            yield Static(
                body
                + "\n\n[dim]The SQL launches exactly as written — Dispatch never rewrites it.[/]",
                id="confirm-body",
            )
            yield Static(
                "[bold]Y[/] launches anyway; [bold]N[/] or [bold]Esc[/] cancels.",
                id="confirm-help",
            )
            with Horizontal(id="confirm-buttons"):
                yield Button("Launch anyway", id="confirm-yes", variant="error")
                yield Button("Cancel", id="confirm-no", variant="default")

    def on_mount(self) -> None:
        self.query_one("#confirm-yes", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-yes")

    def action_proceed(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
