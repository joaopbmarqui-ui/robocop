#!/usr/bin/env python3
"""Generate an end-to-end demo video for PR #10 (Jupyter Kerberos login gate).

Captures Textual SVG screenshots at key moments, converts them to PNG frames,
and assembles an MP4 with short on-screen labels. Run from the repo root:

    /workspace/.venv/bin/python demos/generate_jupyter_kerberos_login_demo.py

Output:
    docs/videos/pr-10-jupyter-kerberos-login-demo.mp4
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_VIDEO = REPO_ROOT / "docs" / "videos" / "pr-10-jupyter-kerberos-login-demo.mp4"
FRAME_SIZE = (1280, 800)  # padded render target for the MP4


def _bootstrap_mock_env(base: Path) -> None:
    mocks_bin = REPO_ROOT / "mocks" / "bin"
    state_dir = base / "mock_state"
    data_root = base / "data"
    state_dir.mkdir(parents=True, exist_ok=True)
    data_root.mkdir(parents=True, exist_ok=True)
    dispatch_home = data_root / ".dispatch"
    dispatch_home.mkdir(parents=True, exist_ok=True)
    (dispatch_home / "config.json").write_text('{"to_email": "demo@example.com"}', encoding="utf-8")
    from dispatch.version import __version__

    (dispatch_home / "installed_version").write_text(f"{__version__}\n", encoding="utf-8")

    default_path = os.pathsep.join(("/usr/bin", "/bin"))
    os.environ["PATH"] = f"{mocks_bin}{os.pathsep}{os.environ.get('PATH', default_path)}"
    os.environ["DISPATCH_DATA_ROOT"] = str(data_root)
    os.environ["DISPATCH_MOCK_STATE_DIR"] = str(state_dir)
    os.environ["DISPATCH_MOCK_SCENARIO"] = "happy_path"
    os.environ["DISPATCH_SCR_DIR"] = str(REPO_ROOT / "scr")
    os.environ["MAILHOST"] = "127.0.0.1:9"
    os.environ.pop("DISPATCH_JUPYTER_MODE", None)


def _svg_to_png(svg_path: Path, png_path: Path) -> None:
    import cairosvg

    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=FRAME_SIZE[0],
        output_height=FRAME_SIZE[1],
    )


def _label_png(src: Path, dst: Path, title: str, subtitle: str = "") -> None:
    """Add a title banner above the screenshot using ffmpeg drawtext."""
    text = title.replace(":", "\\:").replace("'", "\\'")
    sub = subtitle.replace(":", "\\:").replace("'", "\\'")
    filters = [
        "drawbox=x=0:y=0:w=iw:h=72:color=black@0.75:t=fill",
        f"drawtext=text='{text}':x=(w-text_w)/2:y=20:fontsize=28:fontcolor=white",
    ]
    if subtitle:
        filters.append(f"drawtext=text='{sub}':x=(w-text_w)/2:y=48:fontsize=18:fontcolor=0xCCCCCC")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vf",
        ",".join(filters),
        str(dst),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


async def _capture_before_dashboard(frames_dir: Path) -> None:
    """Non-Jupyter startup with no Kerberos ticket — dashboard opens directly."""
    from dispatch.app import DispatchApp

    os.environ["DISPATCH_JUPYTER_MODE"] = "0"
    os.environ["DISPATCH_MOCK_KLIST_TTL"] = "0"
    ticket_file = Path(os.environ["DISPATCH_MOCK_STATE_DIR"]) / "klist_ttl"
    ticket_file.unlink(missing_ok=True)

    app = DispatchApp()
    svg_path = frames_dir / "01-before-dashboard.svg"
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(delay=0.6)
        app.save_screenshot(filename=str(svg_path))
        await pilot.pause(delay=0.2)


async def _capture_jupyter_login_flow(frames_dir: Path) -> None:
    """Jupyter startup with no ticket — login modal, then dashboard after kinit."""
    from textual.widgets import Input

    from dispatch.app import DispatchApp
    from dispatch.screens.dashboard import DashboardScreen
    from dispatch.screens.kerberos_login import KerberosLoginScreen

    os.environ["DISPATCH_JUPYTER_MODE"] = "1"
    os.environ["DISPATCH_MOCK_KLIST_TTL"] = "0"
    ticket_file = Path(os.environ["DISPATCH_MOCK_STATE_DIR"]) / "klist_ttl"
    ticket_file.unlink(missing_ok=True)

    app = DispatchApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(delay=0.6)
        assert isinstance(app.screen, KerberosLoginScreen)
        app.save_screenshot(filename=str(frames_dir / "02-after-login-modal.svg"))

        app.screen.query_one("#kerberos-login-eid", Input).value = "jdoe"
        await pilot.pause(delay=0.3)
        app.save_screenshot(filename=str(frames_dir / "03-after-eid-filled.svg"))

        app.screen.query_one("#kerberos-login-password", Input).value = "demo-password"
        await pilot.pause(delay=0.3)
        app.save_screenshot(filename=str(frames_dir / "04-after-password-filled.svg"))

        app.screen.action_submit()
        await pilot.pause(delay=0.2)
        app.save_screenshot(filename=str(frames_dir / "05-signing-in.svg"))
        await pilot.pause(delay=0.6)
        assert isinstance(app.screen, DashboardScreen)
        app.save_screenshot(filename=str(frames_dir / "06-after-success-dashboard.svg"))


def _build_video(frames_dir: Path, out_path: Path) -> None:
    labeled_dir = frames_dir / "labeled"
    labeled_dir.mkdir(exist_ok=True)
    sequence = [
        (
            "01-before-dashboard.svg",
            "Before (terminal / non-Jupyter)",
            "No ticket → dashboard opens with Kerberos missing",
        ),
        (
            "02-after-login-modal.svg",
            "After (Jupyter Notebook)",
            "No ticket → Kerberos sign-in modal blocks startup",
        ),
        ("03-after-eid-filled.svg", "Jupyter login", "EID field"),
        ("04-after-password-filled.svg", "Jupyter login", "Windows password (masked)"),
        (
            "05-signing-in.svg",
            "Running kinit in background",
            "Password sent on stdin only — never logged",
        ),
        (
            "06-after-success-dashboard.svg",
            "Authenticated",
            "Dashboard loads with active Kerberos ticket",
        ),
    ]
    durations = [3.5, 3.5, 2.0, 2.0, 2.0, 3.5]

    concat_lines: list[str] = []
    for index, (svg_name, title, subtitle) in enumerate(sequence):
        raw_png = labeled_dir / f"frame-{index:02d}-raw.png"
        labeled_png = labeled_dir / f"frame-{index:02d}.png"
        _svg_to_png(frames_dir / svg_name, raw_png)
        _label_png(raw_png, labeled_png, title, subtitle)
        concat_lines.append(f"file '{labeled_png}'")
        concat_lines.append(f"duration {durations[index]}")

    concat_lines.append(f"file '{labeled_dir / f'frame-{len(sequence) - 1:02d}.png'}'")
    concat_file = labeled_dir / "concat.txt"
    concat_file.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-vf",
            "fps=30,format=yuv420p",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(out_path),
        ],
        check=True,
        capture_output=True,
    )


def main() -> int:
    if shutil.which("ffmpeg") is None:
        print("ffmpeg is required to build the demo video", file=sys.stderr)
        return 1
    try:
        import cairosvg  # noqa: F401
    except ImportError:
        print("Install cairosvg in the project venv: pip install cairosvg", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="dispatch-jupyter-demo-") as tmp:
        base = Path(tmp)
        _bootstrap_mock_env(base)
        frames_dir = base / "frames"
        frames_dir.mkdir()
        asyncio.run(_capture_before_dashboard(frames_dir))
        asyncio.run(_capture_jupyter_login_flow(frames_dir))
        _build_video(frames_dir, OUT_VIDEO)

    print(f"Wrote demo video to {OUT_VIDEO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
