"""Advisor launch-gate modal — error findings only, explicit proceed/cancel."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from dispatch.advisor.models import Finding

from .findings import FindingBlock


class AdvisorLaunchGate(ModalScreen[bool]):
    """Enforcement ceiling: errors pause here; proceed launches SQL as written."""

    BINDINGS = [
        ("y", "proceed", "Launch anyway"),
        ("n", "cancel", "Cancel"),
        ("escape", "cancel", "Cancel"),
        ("down", "scroll_findings(1)", "Scroll"),
        ("up", "scroll_findings(-1)", "Scroll"),
        ("pagedown", "scroll_findings(8)", "Scroll"),
        ("pageup", "scroll_findings(-8)", "Scroll"),
    ]

    def __init__(
        self,
        errors: tuple[Finding, ...] | list[Finding],
        *,
        job_summary: str = "",
    ) -> None:
        super().__init__()
        self.errors = tuple(errors)
        self.job_summary = job_summary

    def compose(self) -> ComposeResult:
        count = len(self.errors)
        noun = "finding" if count == 1 else "findings"
        with Vertical(id="confirm-dialog", classes="danger"):
            yield Static(
                f"[bold red]Launch Job — {count} Advisor error {noun}[/]",
                id="confirm-title",
            )
            if self.job_summary:
                yield Static(self.job_summary, id="confirm-body")
            with VerticalScroll(id="confirm-body-scroll"):
                for finding in self.errors:
                    yield FindingBlock(finding)
            yield Static(
                "[dim]The SQL launches exactly as written — Dispatch never rewrites it.[/]",
                id="confirm-note",
            )
            yield Static(
                "[bold]Y[/] launches anyway · [bold]N[/]/[bold]Esc[/] cancels"
                " · [bold]↑↓ PgUp PgDn[/] scroll findings",
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

    def action_scroll_findings(self, lines: int) -> None:
        scroll = self.query_one("#confirm-body-scroll", VerticalScroll)
        scroll.scroll_relative(y=lines, animate=False)
