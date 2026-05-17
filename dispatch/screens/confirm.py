"""Reusable confirmation modal for safety-sensitive actions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmScreen(ModalScreen[bool]):
    """Modal confirmation that returns ``True`` for confirm, ``False`` otherwise."""

    BINDINGS = [
        ("enter", "confirm", "Confirm"),
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        title: str,
        body: str,
        *,
        danger: bool = False,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
    ) -> None:
        super().__init__()
        self.title = title
        self.body = body
        self.danger = danger
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        classes = "danger" if self.danger else ""
        with Vertical(id="confirm-dialog", classes=classes):
            title_markup = (
                f"[bold red]{self.title}[/]"
                if self.danger
                else f"[bold]{self.title}[/]"
            )
            yield Static(title_markup, id="confirm-title")
            yield Static(self.body, id="confirm-body")
            yield Static(
                "Press [bold]Enter[/] or [bold]Y[/] to confirm; "
                "[bold]N[/] or [bold]Esc[/] to cancel.",
                id="confirm-help",
            )
            with Horizontal(id="confirm-buttons"):
                variant = "error" if self.danger else "primary"
                yield Button(f"{self.confirm_label} [Y]", id="confirm-yes", variant=variant)
                yield Button(f"{self.cancel_label} [N]", id="confirm-no", variant="default")

    def on_mount(self) -> None:
        self.query_one("#confirm-yes", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-yes")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
