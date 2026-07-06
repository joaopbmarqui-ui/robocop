"""Kerberos login modal for Jupyter Notebook sessions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from .. import kerberos


class KerberosLoginScreen(ModalScreen[bool]):
    """Collect EID credentials and run ``kinit`` before Dispatch continues."""

    BINDINGS = [
        ("escape", "cancel", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="kerberos-login-dialog"):
            yield Static("[bold]Kerberos sign-in[/]", id="kerberos-login-title")
            yield Static(
                "Dispatch needs an active Kerberos ticket before you can continue.",
                id="kerberos-login-body",
            )
            yield Input(placeholder="EID", id="kerberos-login-eid")
            yield Input(
                placeholder="Windows password",
                id="kerberos-login-password",
                password=True,
            )
            yield Static("", id="kerberos-login-error")
            with Horizontal(id="kerberos-login-buttons"):
                yield Button("Sign in", id="kerberos-login-submit", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#kerberos-login-eid", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "kerberos-login-submit":
            self.action_submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "kerberos-login-eid":
            self.query_one("#kerberos-login-password", Input).focus()
            return
        if event.input.id == "kerberos-login-password":
            self.action_submit()

    def action_submit(self) -> None:
        self.run_worker(self._submit(), name="kerberos-login", exclusive=True)

    async def _submit(self) -> None:
        eid_input = self.query_one("#kerberos-login-eid", Input)
        password_input = self.query_one("#kerberos-login-password", Input)
        error_widget = self.query_one("#kerberos-login-error", Static)
        submit_button = self.query_one("#kerberos-login-submit", Button)

        eid = eid_input.value.strip()
        password = password_input.value
        error_widget.update("[dim]Signing in...[/]")
        eid_input.disabled = True
        password_input.disabled = True
        submit_button.disabled = True

        try:
            ok, message = await kerberos.kinit_with_password(eid, password)
        finally:
            password_input.value = ""
            eid_input.disabled = False
            password_input.disabled = False
            submit_button.disabled = False

        if ok:
            if hasattr(self.app, "refresh_kerberos"):
                await self.app.refresh_kerberos()
            self.dismiss(True)
            return

        error_widget.update(f"[red]{message}[/]")
        password_input.focus()

    def action_cancel(self) -> None:
        self.dismiss(False)
