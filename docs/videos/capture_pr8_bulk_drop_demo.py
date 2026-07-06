#!/usr/bin/env python3
"""Capture an end-to-end demo of Browse bulk table deletion (PR #8).

Generates SVG/PNG frames via Textual's pilot API, then stitches them into
``bulk-table-deletion-demo.mp4`` and ``bulk-table-deletion-demo.gif``.

Usage (from repo root, after ``source mocks/dev-env.sh`` is optional — the
script sets up its own mock environment):

    /workspace/.venv/bin/python docs/videos/capture_pr8_bulk_drop_demo.py
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

import cairosvg  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from textual.widgets import Input  # noqa: E402

from dispatch import impala  # noqa: E402
from dispatch.app import DispatchApp  # noqa: E402
from dispatch.screens.browser import BrowserScreen  # noqa: E402

MOCKS_BIN = WORKSPACE / "mocks" / "bin"
SCR_DIR = WORKSPACE / "scr"
OUT_DIR = WORKSPACE / "docs" / "videos" / "pr8-bulk-table-deletion"
FRAMES_DIR = OUT_DIR / "frames"
DEMO_TABLES = ["dispatch_alpha", "dispatch_beta", "dispatch_gamma"]


class DemoContext:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="dispatch-bulk-drop-demo-"))
        self.state_dir = self.root / "mock_state"
        self.data_root = self.root / "data"

    def prepare(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.data_root.mkdir(parents=True, exist_ok=True)
        FRAMES_DIR.mkdir(parents=True, exist_ok=True)
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        os.environ["PATH"] = str(MOCKS_BIN) + os.pathsep + os.environ.get("PATH", "")
        os.environ["DISPATCH_MOCK_STATE_DIR"] = str(self.state_dir)
        os.environ["DISPATCH_DATA_ROOT"] = str(self.data_root)
        os.environ["DISPATCH_SCR_DIR"] = str(SCR_DIR)
        os.environ["DISPATCH_MOCK_SCENARIO"] = "happy_path"
        os.environ["DISPATCH_MOCK_DELAY"] = "0"
        os.environ["MAILHOST"] = "127.0.0.1:9"

        dispatch_home = self.data_root / ".dispatch"
        dispatch_home.mkdir(parents=True, exist_ok=True)
        (dispatch_home / "config.json").write_text(
            json.dumps({"to_email": "demo@example.com"}),
            encoding="utf-8",
        )


def svg_to_png(svg_path: Path, png_path: Path, *, width: int = 1440) -> None:
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=width)


def add_caption(png_path: Path, caption: str) -> None:
    image = Image.open(png_path).convert("RGBA")
    bar_height = 56
    canvas = Image.new("RGBA", (image.width, image.height + bar_height), (18, 18, 18, 255))
    canvas.paste(image, (0, bar_height))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    draw.text((24, 16), caption, fill=(240, 240, 240, 255), font=font)
    canvas.convert("RGB").save(png_path)


def save_frame(app: DispatchApp, index: int, slug: str, caption: str) -> Path:
    stem = f"{index:02d}_{slug}"
    svg_path = FRAMES_DIR / f"{stem}.svg"
    png_path = FRAMES_DIR / f"{stem}.png"
    app.save_screenshot(filename=svg_path.name, path=str(FRAMES_DIR))
    svg_to_png(svg_path, png_path)
    add_caption(png_path, caption)
    return png_path


async def capture_demo() -> list[Path]:
    dropped: list[str] = []

    async def fake_show_tables(schema: str, pattern: str = "*") -> list[str]:
        return list(DEMO_TABLES)

    async def fake_describe_table(full_table: str) -> str:
        return "name|type|comment\nid|string|primary key\namount|decimal(18,2)|value"

    async def fake_drop_table(full_table: str) -> str:
        dropped.append(full_table)
        return f"Dropped {full_table}"

    impala.show_tables = fake_show_tables  # type: ignore[assignment]
    impala.describe_table = fake_describe_table  # type: ignore[assignment]
    impala.drop_table = fake_drop_table  # type: ignore[assignment]

    frames: list[Path] = []
    app = DispatchApp()
    async with app.run_test(size=(180, 52)) as pilot:
        screen = BrowserScreen(auto_load=False)
        app.push_screen(screen)
        await pilot.pause(0.4)

        await screen.action_show_tables(describe_selection=False)
        await pilot.pause(0.4)
        frames.append(
            save_frame(
                app,
                1,
                "before_drop_disabled",
                "Before: tables loaded — Drop stays disabled until you check rows",
            )
        )

        screen.action_toggle_check()
        await pilot.pause(0.4)
        frames.append(
            save_frame(
                app,
                2,
                "one_table_checked",
                "Space toggles selection — one table checked, Drop enabled",
            )
        )

        screen.action_select_all()
        await pilot.pause(0.4)
        frames.append(
            save_frame(
                app,
                3,
                "select_all_checked",
                "Select All [A] checks every loaded table",
            )
        )

        worker = screen.action_drop()
        await pilot.pause(0.5)
        frames.append(
            save_frame(
                app,
                4,
                "confirm_modal_list",
                "Drop lists checked tables — confirm button disabled until phrases match",
            )
        )

        confirm = app.screen
        confirm.query_one("#confirm-input", Input).value = "I AM SURE"
        confirm._update_confirm_enabled()
        await pilot.pause(0.3)
        frames.append(
            save_frame(
                app,
                5,
                "typed_i_am_sure",
                'Step 1: type exactly "I AM SURE"',
            )
        )

        confirm.query_one("#confirm-input-secondary", Input).value = "DROP"
        confirm._update_confirm_enabled()
        await pilot.pause(0.3)
        frames.append(
            save_frame(
                app,
                6,
                "typed_drop_enabled",
                'Step 2: type exactly "DROP" — Drop button enables',
            )
        )

        confirm.action_confirm()
        await worker.wait()
        await pilot.pause(0.5)
        frames.append(
            save_frame(
                app,
                7,
                "after_bulk_drop",
                f"After: dropped {len(dropped)} tables — only checked rows were removed",
            )
        )

    assert dropped == [
        "aa_enc.dispatch_alpha",
        "aa_enc.dispatch_beta",
        "aa_enc.dispatch_gamma",
    ], dropped
    return frames


def build_video(frames: list[Path]) -> None:
    list_file = FRAMES_DIR / "ffmpeg_list.txt"
    lines = []
    for frame in frames:
        lines.append(f"file '{frame.name}'")
        lines.append("duration 2.5")
    lines.append(f"file '{frames[-1].name}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    mp4_path = OUT_DIR / "bulk-table-deletion-demo.mp4"
    gif_path = OUT_DIR / "bulk-table-deletion-demo.gif"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-vf",
            "fps=24,format=yuv420p",
            str(mp4_path),
        ],
        check=True,
        cwd=str(FRAMES_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    palette_path = FRAMES_DIR / "palette.png"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-vf",
            "fps=8,scale=960:-1:flags=lanczos,palettegen",
            str(palette_path),
        ],
        check=True,
        cwd=str(FRAMES_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-i",
            str(palette_path),
            "-lavfi",
            "fps=8,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse",
            str(gif_path),
        ],
        check=True,
        cwd=str(FRAMES_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    ctx = DemoContext()
    ctx.prepare()
    frames = asyncio.run(capture_demo())
    build_video(frames)
    print(f"Wrote {len(frames)} frames to {FRAMES_DIR}")
    print(f"Video: {OUT_DIR / 'bulk-table-deletion-demo.mp4'}")
    print(f"GIF:   {OUT_DIR / 'bulk-table-deletion-demo.gif'}")


if __name__ == "__main__":
    main()
