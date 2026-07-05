"""Reusable confirmation modal for safety-sensitive actions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


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
        required_confirmation_text: str | None = None,
        secondary_confirmation_text: str | None = None,
    ) -> None:
        super().__init__()
        self.title = title
        self.body = body
        self.danger = danger
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.required_confirmation_text = required_confirmation_text
        self.secondary_confirmation_text = secondary_confirmation_text

    def compose(self) -> ComposeResult:
        classes = "danger" if self.danger else ""
        with Vertical(id="confirm-dialog", classes=classes):
            title_markup = f"[bold red]{self.title}[/]" if self.danger else f"[bold]{self.title}[/]"
            yield Static(title_markup, id="confirm-title")
            yield Static(self.body, id="confirm-body")
            if self.required_confirmation_text:
                yield Input(
                    placeholder=f"Type {self.required_confirmation_text} to confirm",
                    id="confirm-input",
                )
            if self.secondary_confirmation_text:
                yield Input(
                    placeholder=f"Type {self.secondary_confirmation_text} to confirm",
                    id="confirm-input-secondary",
                )
            help_text = self._help_text()
            yield Static(help_text, id="confirm-help")
            with Horizontal(id="confirm-buttons"):
                variant = "error" if self.danger else "primary"
                yield Button(self.confirm_label, id="confirm-yes", variant=variant)
                yield Button(self.cancel_label, id="confirm-no", variant="default")

    def _help_text(self) -> str:
        if self.required_confirmation_text and self.secondary_confirmation_text:
            return (
                f"Type [bold]{self.required_confirmation_text}[/], then "
                f"[bold]{self.secondary_confirmation_text}[/] exactly; "
                "[bold]Enter[/] confirms when both match; "
                "[bold]N[/] or [bold]Esc[/] cancels."
            )
        if self.required_confirmation_text:
            return (
                f"Type [bold]{self.required_confirmation_text}[/] exactly, then "
                "[bold]Y[/] or [bold]Enter[/] to confirm; "
                "[bold]N[/] or [bold]Esc[/] cancels."
            )
        return "[bold]Y[/] or [bold]Enter[/] to confirm; [bold]N[/] or [bold]Esc[/] to cancel."

    def on_mount(self) -> None:
        if self.required_confirmation_text:
            self.query_one("#confirm-input", Input).focus()
        else:
            self.query_one("#confirm-yes", Button).focus()
        self._update_confirm_enabled()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id in {"confirm-input", "confirm-input-secondary"}:
            self._update_confirm_enabled()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-yes":
            self.action_confirm()
        else:
            self.action_cancel()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in {"confirm-input", "confirm-input-secondary"}:
            self.action_confirm()

    def _confirmation_matches(self) -> bool:
        if self.required_confirmation_text:
            value = self.query_one("#confirm-input", Input).value.strip()
            if value != self.required_confirmation_text:
                return False
        if self.secondary_confirmation_text:
            value = self.query_one("#confirm-input-secondary", Input).value.strip()
            if value != self.secondary_confirmation_text:
                return False
        return True

    def _update_confirm_enabled(self) -> None:
        needs_typed_confirmation = bool(
            self.required_confirmation_text or self.secondary_confirmation_text
        )
        if not needs_typed_confirmation:
            return
        self.query_one("#confirm-yes", Button).disabled = not self._confirmation_matches()

    def action_confirm(self) -> None:
        if self.required_confirmation_text or self.secondary_confirmation_text:
            if not self._confirmation_matches():
                self.query_one("#confirm-help", Static).update(
                    "[red]Type the exact confirmation text(s) to proceed.[/]"
                )
                self._update_confirm_enabled()
                return
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
