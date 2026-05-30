"""Help screen listing keyboard shortcuts organized by screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

QUICK_HELP = """\
[bold cyan]Quick Reference[/]  [dim]N[/] New Job  [dim]V[/] View Logs  [dim]H[/] History  [dim]B[/] Browser  [dim]?[/] Help  [dim]Q[/] Quit\
"""

HELP_TEXT = """\
[bold $accent]Dispatch Keyboard Shortcuts[/]

[bold $accent]Global[/]
  [cyan]Q[/]       Quit Dispatch
  [cyan]?[/]       Toggle this help screen

───────────────

[bold $accent]Dashboard[/]
  [cyan]N[/]       New Job wizard
  [cyan]V[/]       View logs for selected job
  [cyan]J/K[/]     Move selection in tables
  [cyan]C[/]       Cancel selected job
  [cyan]H[/]       Open History
  [cyan]B[/]       Open Impala Browser
  [cyan]\u2191 \u2193[/]     Navigate job rows
  [cyan]Enter[/]   Open detail for selected row

───────────────

[bold $accent]New Job[/]
  [cyan]L[/]       Launch job (requires Kerberos)
  [cyan]P[/]       Preview generated SQL
  [cyan]E[/]       Edit SQL file in $EDITOR
  [cyan]K[/]       Refresh Kerberos (kinit)
  [cyan]B / Esc[/] Back to Dashboard

[bold $accent]SQL Preview[/]
  [cyan]Enter[/]   Back to form
  [cyan]Y[/]       Copy SQL
  [cyan]B / Esc[/] Back

[bold $accent]Job Detail[/]
  [cyan]Space/F[/] Toggle log follow mode
  [cyan]G/g[/]     Jump to bottom / top of log
  [cyan]/[/]       Search log
  [cyan]Y[/]       Copy job ID
  [cyan]R[/]       Clone job to New Job
  [cyan]C[/]       Cancel job (with confirmation)
  [cyan]B / Esc[/] Back

[bold $accent]History[/]
  [cyan]S[/]       Cycle sort order
  [cyan]Enter[/]   View logs for selected row
  [cyan][ / ][/]   Previous / Next page
  [cyan]B / Esc[/] Back

[bold $accent]Browser[/]
  [cyan]Enter[/]   Describe selected table
  [cyan]D[/]       Drop selected table (with typed confirmation)
  [cyan]B / Esc[/] Back

[dim]Press Esc or ? to close.[/]\
"""


class HelpScreen(ModalScreen[None]):
    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("question_mark", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Static(QUICK_HELP, id="help-quick")
            yield Static(HELP_TEXT, id="help-body")
