#!/usr/bin/env python3
"""Record a focused demo of Browse-tab auto-refresh after DROP.

Generates SVG frames with Textual's pilot API, converts them to PNG, and
stitches an MP4 plus GIF under ``docs/videos/``.

Usage:
    source mocks/dev-env.sh
    /workspace/.venv/bin/python tools/demo_browser_drop_refresh.py

Outputs:
    docs/videos/browse-drop-refresh-pr9.mp4
    docs/videos/browse-drop-refresh-pr9.gif
    docs/videos/browse-drop-refresh-pr9/   (frame assets)
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from textual.widgets import DataTable, Input  # noqa: E402

from dispatch.app import DispatchApp  # noqa: E402
from dispatch.screens.browser import BrowserScreen  # noqa: E402

MOCKS_BIN = WORKSPACE / "mocks" / "bin"
OUT_DIR = WORKSPACE / "docs" / "videos" / "browse-drop-refresh-pr9"
VIDEO_MP4 = WORKSPACE / "docs" / "videos" / "browse-drop-refresh-pr9.mp4"
VIDEO_GIF = WORKSPACE / "docs" / "videos" / "browse-drop-refresh-pr9.gif"
FRAME_SECONDS = 2.5


def _prepare_env(root: Path) -> None:
    state_dir = root / "mock_state"
    data_root = root / "data"
    state_dir.mkdir(parents=True, exist_ok=True)
    data_root.mkdir(parents=True, exist_ok=True)

    os.environ["PATH"] = str(MOCKS_BIN) + os.pathsep + os.environ.get("PATH", "")
    os.environ["DISPATCH_MOCK_STATE_DIR"] = str(state_dir)
    os.environ["DISPATCH_DATA_ROOT"] = str(data_root)
    os.environ["DISPATCH_MOCK_SCENARIO"] = "happy_path"
    os.environ["DISPATCH_MOCK_DELAY"] = "0"
    os.environ["MAILHOST"] = "127.0.0.1:9"

    dispatch_home = data_root / ".dispatch"
    dispatch_home.mkdir(parents=True, exist_ok=True)
    (dispatch_home / "config.json").write_text(
        json.dumps({"to_email": "demo@example.com"}),
        encoding="utf-8",
    )


def _title_svg(title: str, subtitle: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1040" viewBox="0 0 1800 1040">
  <rect width="1800" height="1040" fill="#101418"/>
  <text x="900" y="470" fill="#d7e3f4" font-size="54" font-family="monospace" text-anchor="middle">{title}</text>
  <text x="900" y="560" fill="#8aa0bf" font-size="30" font-family="monospace" text-anchor="middle">{subtitle}</text>
</svg>
"""


async def _capture_frames(out_dir: Path) -> list[Path]:
    frames: list[Path] = []

    def save_title(name: str, title: str, subtitle: str) -> None:
        path = out_dir / f"{name}.svg"
        path.write_text(_title_svg(title, subtitle), encoding="utf-8")
        frames.append(path)

    async def save_app(app: DispatchApp, name: str) -> None:
        path = out_dir / f"{name}.svg"
        app.save_screenshot(filename=str(path))
        frames.append(path)

    save_title(
        "00_intro",
        "Browse DROP auto-refresh",
        "PR #9 — dropped tables disappear without manual reload",
    )

    with tempfile.TemporaryDirectory(prefix="dispatch-drop-demo-") as tmp:
        _prepare_env(Path(tmp))

        app = DispatchApp()
        async with app.run_test(size=(180, 52)) as pilot:
            screen = BrowserScreen()
            app.push_screen(screen)
            await pilot.pause(0.8)
            await save_app(app, "01_before_drop_loaded")

            table = screen.query_one("#browser-table", DataTable)
            dropped_name = str(table.get_row_at(0)[0])
            full_name = f"aa_enc.{dropped_name}"
            table.cursor_coordinate = (0, 0)

            worker = screen.action_drop()
            await pilot.pause(0.5)
            await save_app(app, "02_drop_confirmation")

            confirm_input = app.screen.query_one("#confirm-input", Input)
            confirm_input.value = full_name
            await pilot.press("enter")
            await worker.wait()
            await pilot.pause(0.6)
            await save_app(app, "03_after_drop_auto_refreshed")

            remaining = [table.get_row_at(i)[0] for i in range(table.row_count)]
            assert dropped_name not in remaining, (
                f"Expected dropped table {dropped_name!r} to be gone; still have {remaining}"
            )

    save_title(
        "04_outro",
        "No Load Tables [S] pressed",
        "List refreshed automatically after successful DROP",
    )
    return frames


def _svg_to_png(svg_path: Path, png_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(svg_path),
            "-frames:v",
            "1",
            "-update",
            "1",
            str(png_path),
        ],
        check=True,
        capture_output=True,
    )


def _build_video(frames: list[Path], mp4_path: Path, gif_path: Path) -> None:
    work = mp4_path.parent / f".{mp4_path.stem}_build"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    png_paths: list[Path] = []
    for index, svg_path in enumerate(frames):
        png_path = work / f"frame_{index:02d}.png"
        _svg_to_png(svg_path, png_path)
        png_paths.append(png_path)

    concat_file = work / "concat.txt"
    concat_lines: list[str] = []
    for path in png_paths:
        concat_lines.append(f"file '{path}'")
        concat_lines.append(f"duration {FRAME_SECONDS}")
    concat_lines.append(f"file '{png_paths[-1]}'")
    concat_file.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

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
            "fps=2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(mp4_path),
        ],
        check=True,
        capture_output=True,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(mp4_path),
            "-vf",
            "fps=8,scale=900:-1:flags=lanczos",
            "-loop",
            "0",
            str(gif_path),
        ],
        check=True,
        capture_output=True,
    )

    shutil.rmtree(work)


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = await _capture_frames(OUT_DIR)
    _build_video(frames, VIDEO_MP4, VIDEO_GIF)
    print(f"Wrote demo frames to {OUT_DIR}")
    print(f"Wrote demo video to {VIDEO_MP4}")
    print(f"Wrote demo gif to {VIDEO_GIF}")


if __name__ == "__main__":
    asyncio.run(main())
