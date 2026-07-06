#!/usr/bin/env python3
"""Capture a before/after demo video for PR #4 (Browse table search clarity).

Renders the pre-PR and post-PR Browse query row via Textual's pilot API,
captures PNG frames, and stitches them into ``docs/videos/pr4-browse-table-search-clarity.mp4``.

Run from the repo root (after ``source mocks/dev-env.sh``):

    /workspace/.venv/bin/python demos/pr4-browse-table-search-clarity/capture_demo.py

Outputs:
  - docs/videos/pr4-browse-table-search-clarity.mp4
  - docs/videos/pr4-browse-table-search-clarity.gif  (short loop for PR embed)
  - demos/pr4-browse-table-search-clarity/frames/*.png
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

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from textual.app import ComposeResult  # noqa: E402
from textual.containers import Horizontal, Vertical  # noqa: E402
from textual.screen import Screen  # noqa: E402
from textual.widgets import Button, DataTable, Footer, Header, Input, Static  # noqa: E402

from dispatch import impala  # noqa: E402
from dispatch.app import DispatchApp  # noqa: E402
from dispatch.screens.browser import BrowserScreen  # noqa: E402
from dispatch.screens.sidebar import Sidebar  # noqa: E402

DEMO_DIR = Path(__file__).resolve().parent
FRAMES_DIR = DEMO_DIR / "frames"
VIDEO_DIR = REPO_ROOT / "docs" / "videos"
MP4_OUT = VIDEO_DIR / "pr4-browse-table-search-clarity.mp4"
GIF_OUT = VIDEO_DIR / "pr4-browse-table-search-clarity.gif"
TERMINAL_SIZE = (120, 40)


class BeforeBrowseDemoScreen(Screen[None]):
    """Pre-PR Browse query row: shared caption, no Table name label or hint."""

    CSS = """
    #browser-query-row Input {
        width: 1fr;
        margin: 0 1 0 0;
    }

    #browser-query-row Button {
        min-width: 16;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        sidebar = Sidebar()
        sidebar.active_screen = "browse"
        yield sidebar
        with Vertical(id="main-content"):
            with Vertical(id="browser-content"):
                yield Static("[bold]Browse Impala Metadata[/]", classes="section-title")
                with Horizontal(id="browser-split"):
                    with Vertical(id="browser-left"):
                        yield Static(
                            "[dim]Schema \u00b7 table filter[/]",
                            classes="input-caption",
                        )
                        with Horizontal(id="browser-query-row"):
                            yield Input(value="aa_enc", placeholder="Schema", id="schema")
                            yield Input(
                                value="*",
                                placeholder="Filter (e.g. dispatch_*)",
                                id="filter",
                            )
                            yield Button("Load Tables [S]", id="show", variant="default")
                        yield DataTable(id="browser-table")
                        with Horizontal(id="browser-status"):
                            yield Static("", id="browser-count")
                    with Vertical(id="browser-right"):
                        yield Static("[dim]No table selected[/]", id="file-preview-title")
                        yield Static(
                            "[dim]Select a table and press Enter to view its schema.[/]",
                            id="describe-body",
                        )
            with Horizontal(classes="action-bar"):
                yield Button("Back [B]", id="back", variant="default")
                yield Button("Describe [Enter]", id="describe", variant="primary", disabled=True)
                yield Button("Drop [D]", id="drop", variant="error", disabled=True)
        yield Footer()

    async def on_mount(self) -> None:
        table = self.query_one("#browser-table", DataTable)
        table.add_columns("Name", "Type")
        table.cursor_type = "row"
        table.add_row("(load tables to browse)", "")


def _bootstrap_capture_env() -> None:
    mocks_bin = REPO_ROOT / "mocks" / "bin"
    root = Path(tempfile.mkdtemp(prefix="dispatch-pr4-demo-"))
    data_root = root / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    dispatch_home = data_root / ".dispatch"
    dispatch_home.mkdir(parents=True, exist_ok=True)
    (dispatch_home / "config.json").write_text(
        json.dumps({"to_email": "demo@example.com"}),
        encoding="utf-8",
    )

    os.environ["PATH"] = str(mocks_bin) + os.pathsep + os.environ.get("PATH", "")
    os.environ["DISPATCH_DATA_ROOT"] = str(data_root)
    os.environ["DISPATCH_EMAIL"] = "demo@example.com"
    os.environ.setdefault("DISPATCH_MOCK_SCENARIO", "happy_path")
    os.environ.setdefault("USER", "demo")


async def _capture_screen_png(app: DispatchApp, path: Path) -> None:
    # Textual only exports SVG; rasterise it to a genuine PNG so the committed
    # ``frames/*.png`` are real PNGs (not SVG payloads with a .png extension)
    # and can be decoded by ffmpeg when building the video.
    import cairosvg

    path.parent.mkdir(parents=True, exist_ok=True)
    svg_markup = app.export_screenshot()
    cairosvg.svg2png(
        bytestring=svg_markup.encode("utf-8"),
        write_to=str(path),
        output_width=1600,
        background_color="#1e1e2e",
    )


async def capture_before_frame() -> Path:
    out = FRAMES_DIR / "01_before_browser.png"
    app = DispatchApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.push_screen(BeforeBrowseDemoScreen())
        await pilot.pause(0.6)
        await _capture_screen_png(app, out)
    return out


async def capture_after_frames() -> list[Path]:
    async def fake_show_tables(schema: str, pattern: str = "*") -> list[str]:
        return ["dispatch_result", "dispatch_archive", "dispatch_staging"]

    async def fake_describe_table(full_table: str) -> str:
        return "name|type|comment\nid|string|primary key"

    impala.show_tables = fake_show_tables
    impala.describe_table = fake_describe_table

    paths: list[Path] = []
    app = DispatchApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        screen = BrowserScreen(auto_load=False)
        app.push_screen(screen)
        await pilot.pause(0.6)
        initial = FRAMES_DIR / "02_after_labels.png"
        await _capture_screen_png(app, initial)
        paths.append(initial)

        filter_input = screen.query_one("#filter", Input)
        filter_input.value = "dispatch*"
        filter_input.focus()
        await pilot.pause(0.4)
        typed = FRAMES_DIR / "03_after_filter_typed.png"
        await _capture_screen_png(app, typed)
        paths.append(typed)

        await screen.action_show_tables()
        await pilot.pause(0.6)
        loaded = FRAMES_DIR / "04_after_tables_loaded.png"
        await _capture_screen_png(app, loaded)
        paths.append(loaded)

    return paths


def _make_title_card(text: str, path: Path, *, duration_sec: float = 2.0) -> None:
    """Render a simple title card with ffmpeg drawtext."""
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_text = text.replace(":", r"\:").replace("'", r"\'")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=#1e1e2e:s=1920x1080:d={duration_sec}",
            "-vf",
            (
                f"drawtext=text='{safe_text}':fontsize=72:fontcolor=white:"
                "x=(w-text_w)/2:y=(h-text_h)/2:font=DejaVu Sans"
            ),
            "-frames:v",
            "1",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def _image_to_clip(image: Path, clip: Path, *, duration_sec: float) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image),
            "-t",
            str(duration_sec),
            "-vf",
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#1e1e2e",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            str(clip),
        ],
        check=True,
        capture_output=True,
    )


def _concat_clips(clips: list[Path], output: Path) -> None:
    list_file = output.with_suffix(".concat.txt")
    list_file.write_text("".join(f"file '{clip}'\n" for clip in clips), encoding="utf-8")
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
            "-c",
            "copy",
            str(output),
        ],
        check=True,
        capture_output=True,
    )
    list_file.unlink(missing_ok=True)


def build_video() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required to build the demo video")

    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    clips_dir = DEMO_DIR / "clips"
    if clips_dir.exists():
        shutil.rmtree(clips_dir)
    clips_dir.mkdir(parents=True)

    title_before = clips_dir / "00_title_before.png"
    title_after = clips_dir / "00_title_after.png"
    _make_title_card("Before — Schema · table filter", title_before)
    _make_title_card("After — Table name + hint", title_after)

    segments: list[tuple[Path, float]] = [
        (title_before, 1.5),
        (FRAMES_DIR / "01_before_browser.png", 3.0),
        (title_after, 1.5),
        (FRAMES_DIR / "02_after_labels.png", 3.0),
        (FRAMES_DIR / "03_after_filter_typed.png", 2.0),
        (FRAMES_DIR / "04_after_tables_loaded.png", 3.5),
    ]

    clip_paths: list[Path] = []
    for index, (image, duration) in enumerate(segments):
        clip = clips_dir / f"seg_{index:02d}.mp4"
        _image_to_clip(image, clip, duration_sec=duration)
        clip_paths.append(clip)

    _concat_clips(clip_paths, MP4_OUT)

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(MP4_OUT),
            "-vf",
            "fps=10,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            str(GIF_OUT),
        ],
        check=True,
        capture_output=True,
    )


async def main() -> None:
    _bootstrap_capture_env()
    print("Capturing before frame…")
    await capture_before_frame()
    print("Capturing after frames…")
    await capture_after_frames()
    print("Building video…")
    build_video()
    print(f"Wrote {MP4_OUT}")
    print(f"Wrote {GIF_OUT}")


if __name__ == "__main__":
    asyncio.run(main())
