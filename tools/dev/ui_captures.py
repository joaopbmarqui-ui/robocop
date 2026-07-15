"""Generate SVG captures of Dispatch TUI states for UI user-story evidence.

This drives the real :class:`dispatch.app.DispatchApp` through Textual's
``run_test`` pilot at fixed terminal sizes and writes one SVG per UI state into
``tools/prod_tui/reports/ui-captures/``. Each capture carries required/forbidden
substring assertions so the run doubles as a self-verifying check of the
UI-rendering user stories that cannot be exercised by the Edge harness:

- APP-002  global help map + command-palette destinations + F2 sidebar toggle
- APP-003  below-minimum (80x24) terminal warning, and a usable 80x24 layout
- SIDE-002 sidebar auto-collapse under width 100, plus manual F2 collapse
- PREV-002 SQL preview action bar (Copy SQL / Back, never Launch) + copy result

The environment is mocked so the captures are clean: a temp data root with
config, a healthy Kerberos TTL, and a launch directory that contains a SQL
file so New Job/Preview render real content.

Run:  py tools/dev/ui_captures.py
Exit code is non-zero if any capture fails its content assertions.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from svg_text import svg_to_text  # noqa: E402

OUT_DIR = REPO_ROOT / "tools" / "prod_tui" / "reports" / "ui-captures"
HEALTHY_TTL_SECONDS = 8 * 3600


def _bootstrap_environment() -> Path:
    """Create a clean temp data root + launch dir and point Dispatch at them.

    Returns the launch directory (containing a SQL file) that the app should
    treat as the current working directory.
    """
    base = Path(tempfile.mkdtemp(prefix="dispatch-ui-captures-"))
    data_root = base / "data"
    dispatch_home = data_root / ".dispatch"
    dispatch_home.mkdir(parents=True, exist_ok=True)
    (dispatch_home / "config.json").write_text(
        '{"to_email": "analyst@example.com"}', encoding="utf-8"
    )

    launch_cwd = base / "sql"
    launch_cwd.mkdir(parents=True, exist_ok=True)
    (launch_cwd / "monthly_revenue.sql").write_text(
        "SELECT region, SUM(amount) AS total\nFROM sales\nGROUP BY region\n",
        encoding="utf-8",
    )

    os.environ["DISPATCH_DATA_ROOT"] = str(data_root)
    os.environ["DISPATCH_EMAIL"] = "analyst@example.com"
    os.environ.setdefault("USER", "analyst")
    return launch_cwd


def _install_healthy_kerberos() -> None:
    """Override the klist-backed TTL probe with a healthy fixed value."""
    import dispatch.kerberos as kerberos

    async def _fake_ttl() -> int:
        return HEALTHY_TTL_SECONDS

    kerberos.ticket_ttl_seconds = _fake_ttl  # type: ignore[assignment]


@dataclass
class Capture:
    name: str
    size: tuple[int, int]
    description: str
    requires: list[str] = field(default_factory=list)
    forbids: list[str] = field(default_factory=list)
    # actions(pilot) -> awaitable; performed after initial mount settle.
    actions: object = None
    # optional second size to resize to after mount (for resize captures).
    resize_to: tuple[int, int] | None = None


def _active_notifications(app) -> str:
    """Join active notification messages.

    Textual paints toast notifications on a layer that the offline
    ``save_screenshot`` compositor does not render, so notification-driven
    behavior (the too-small warning, the copy-result toast) is asserted from the
    app's live notification state instead of the SVG pixels.
    """
    try:
        return " ".join(getattr(note, "message", "") for note in app._notifications)
    except Exception:  # pragma: no cover - defensive
        return ""


async def _run_capture(cap: Capture) -> tuple[bool, str]:
    from dispatch.app import DispatchApp

    out_path = OUT_DIR / f"{cap.name}.svg"
    app = DispatchApp()
    notifications = ""
    async with app.run_test(size=cap.size) as pilot:
        await pilot.pause(0.6)
        if cap.resize_to is not None:
            await pilot.resize_terminal(*cap.resize_to)
            await pilot.pause(0.5)
        if cap.actions is not None:
            await cap.actions(pilot, app)
            await pilot.pause(0.4)
        notifications = _active_notifications(app)
        app.save_screenshot(filename=str(out_path))

    if not out_path.exists():
        return False, f"{cap.name}: screenshot not written"
    raw = out_path.read_text(encoding="utf-8")
    if not raw.startswith("<svg"):
        return False, f"{cap.name}: not a valid SVG"

    # Assert on decoded, whitespace-normalized text (SVG encodes spaces as
    # &#160;) plus any active toast notifications.
    text = svg_to_text(raw) + " " + notifications

    problems: list[str] = []
    for needle in cap.requires:
        if needle not in text:
            problems.append(f"missing required text {needle!r}")
    for needle in cap.forbids:
        if needle in text:
            problems.append(f"contains forbidden text {needle!r}")
    if problems:
        return False, f"{cap.name}: " + "; ".join(problems)
    return True, f"{cap.name}: OK -> {out_path.relative_to(REPO_ROOT)}"


async def _press(pilot, *keys: str) -> None:
    for key in keys:
        await pilot.press(key)
        await pilot.pause(0.25)


def _build_captures() -> list[Capture]:
    async def help_modal(pilot, app):
        await _press(pilot, "question_mark")

    async def command_palette(pilot, app):
        await _press(pilot, "ctrl+p")

    async def f2_collapse(pilot, app):
        await _press(pilot, "f2")

    async def open_preview(pilot, app):
        await _press(pilot, "n")
        await pilot.pause(0.6)
        await _press(pilot, "p")
        await pilot.pause(0.4)

    async def preview_then_copy(pilot, app):
        await _press(pilot, "n")
        await pilot.pause(0.6)
        await _press(pilot, "p")
        await pilot.pause(0.4)
        await _press(pilot, "y")

    return [
        Capture(
            name="app002-help",
            size=(120, 40),
            description="APP-002 global help map (?)",
            requires=["Command palette", "Collapse / expand the sidebar", "Quick Reference"],
            actions=help_modal,
        ),
        Capture(
            name="app002-command-palette",
            size=(120, 40),
            description="APP-002 command palette destinations (Ctrl+P)",
            requires=[
                "Overview",
                "New Job",
                "History",
                "Browse metadata",
                "Refresh Kerberos (kinit)",
            ],
            actions=command_palette,
        ),
        Capture(
            name="app003-too-small",
            size=(70, 20),
            description="APP-003 below-minimum (70x20) terminal warning",
            requires=["Terminal too small", "Minimum"],
        ),
        Capture(
            name="app003-min-80x24",
            size=(80, 24),
            description="APP-003 usable layout at the 80x24 minimum",
            requires=["RUNNING", "KERBEROS"],
        ),
        Capture(
            name="side002-expanded",
            size=(120, 40),
            description="SIDE-002 expanded sidebar baseline (width 120)",
            requires=["Overview", "KRB"],
        ),
        Capture(
            name="side002-auto-collapsed",
            size=(120, 40),
            description="SIDE-002 sidebar auto-collapses under width 100 (resized to 90)",
            requires=["RUNNING"],
            forbids=["Overview", "KRB"],
            resize_to=(90, 30),
        ),
        Capture(
            name="side002-f2-collapsed",
            size=(120, 40),
            description="SIDE-002 manual F2 collapse at full width",
            requires=["RUNNING"],
            forbids=["Overview", "KRB"],
            actions=f2_collapse,
        ),
        Capture(
            name="prev002-preview",
            size=(120, 40),
            description="PREV-002 SQL preview action bar omits Launch",
            requires=["Copy SQL", "Back", "review before launching"],
            forbids=["Launch"],
            actions=open_preview,
        ),
        Capture(
            name="prev002-copy-result",
            size=(120, 40),
            description="PREV-002 copy result notification",
            requires=["clipboard"],
            actions=preview_then_copy,
        ),
    ]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    launch_cwd = _bootstrap_environment()
    _install_healthy_kerberos()
    os.chdir(launch_cwd)

    captures = _build_captures()
    results: list[tuple[bool, str]] = []
    palette_labels: list[str] = []

    for cap in captures:
        ok, message = asyncio.run(_run_capture(cap))
        results.append((ok, message))
        print(("PASS " if ok else "FAIL ") + message)

    # Direct (non-SVG) assertion of the command-palette destinations for APP-002.
    palette_labels = asyncio.run(_collect_palette_labels())
    expected = ["Overview", "New Job", "History", "Browse metadata", "Refresh Kerberos (kinit)"]
    missing = [label for label in expected if label not in palette_labels]
    if missing:
        results.append((False, f"command-palette destinations missing: {missing}"))
        print(f"FAIL command-palette destinations missing: {missing}")
    else:
        results.append((True, "command-palette destinations: " + ", ".join(expected)))
        print("PASS command-palette destinations: " + ", ".join(expected))

    failures = [message for ok, message in results if not ok]
    print("\n" + ("ALL CAPTURES PASSED" if not failures else f"{len(failures)} CHECK(S) FAILED"))
    return 0 if not failures else 1


async def _collect_palette_labels() -> list[str]:
    from dispatch.app import DispatchApp

    app = DispatchApp()
    labels: list[str] = []
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.4)
        for command in app.get_system_commands(app.screen):
            labels.append(getattr(command, "title", ""))
    return labels


if __name__ == "__main__":
    sys.exit(main())
