#!/usr/bin/env python3
"""Record an end-to-end demo of the Browse tab table-size column (PR #1).

Drives the real Dispatch Textual app through mocked Impala metadata, captures
SVG frames for a synthetic "before" layout and the new Size-column behavior
(including size sorting), then assembles an MP4 under ``docs/videos/``.

Usage:
    source mocks/dev-env.sh
    python3 demos/browse-table-size-pr1-demo.py

Outputs:
    docs/videos/browse-table-size-pr1-demo.mp4
    docs/videos/browse-table-size-pr1-demo.gif   (short animated preview)
    demos/frames/browse-table-size-pr1-*.png     (intermediate frames)
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FRAMES_DIR = REPO_ROOT / "demos" / "frames"
VIDEO_MP4 = REPO_ROOT / "docs" / "videos" / "browse-table-size-pr1-demo.mp4"
VIDEO_GIF = REPO_ROOT / "docs" / "videos" / "browse-table-size-pr1-demo.gif"

DEMO_TABLES = ("dispatch_alpha", "dispatch_zulu")
DEMO_SIZES = {
    "dispatch_alpha": (13_212_057, "12.6 MB"),
    "dispatch_zulu": (1_342_177_280, "1.2 GB"),
}


def _bootstrap_environment() -> Path:
    """Point Dispatch at a clean mocked data root and launch directory."""
    base = Path(tempfile.mkdtemp(prefix="dispatch-browse-size-demo-"))
    data_root = base / "data"
    dispatch_home = data_root / ".dispatch"
    dispatch_home.mkdir(parents=True, exist_ok=True)
    (dispatch_home / "config.json").write_text(
        json.dumps({"to_email": "demo@example.com"}),
        encoding="utf-8",
    )

    launch_cwd = base / "sql"
    launch_cwd.mkdir(parents=True, exist_ok=True)
    (launch_cwd / "query.sql").write_text("SELECT 1;\n", encoding="utf-8")

    mocks_bin = REPO_ROOT / "mocks" / "bin"
    os.environ["PATH"] = str(mocks_bin) + os.pathsep + os.environ.get("PATH", "")
    os.environ["DISPATCH_DATA_ROOT"] = str(data_root)
    os.environ["DISPATCH_EMAIL"] = "demo@example.com"
    os.environ["DISPATCH_MOCK_SCENARIO"] = "happy_path"
    os.environ["DISPATCH_MOCK_DELAY"] = "0"
    os.environ.setdefault("USER", "demo")
    return launch_cwd


def _install_healthy_kerberos() -> None:
    import dispatch.kerberos as kerberos

    async def _fake_ttl() -> int:
        return 8 * 3600

    kerberos.ticket_ttl_seconds = _fake_ttl  # type: ignore[assignment]


def _install_demo_impala() -> None:
    """Deterministic metadata so name sort and size sort produce different orders."""
    from dispatch import impala

    async def fake_show_tables(schema: str, pattern: str = "*") -> list[str]:
        return list(DEMO_TABLES)

    async def fake_describe_table(full_table: str) -> str:
        return "name|type|comment\nid|string|primary key"

    async def fake_table_sizes(schema: str, table_names: list[str]) -> dict[str, impala.TableStats]:
        return {
            name: impala.TableStats(
                size_bytes=DEMO_SIZES[name][0],
                size_display=DEMO_SIZES[name][1],
            )
            for name in table_names
        }

    impala.show_tables = fake_show_tables  # type: ignore[assignment]
    impala.describe_table = fake_describe_table  # type: ignore[assignment]
    impala.table_sizes = fake_table_sizes  # type: ignore[assignment]


def _svg_to_png(svg_path: Path, png_path: Path, *, width: int = 1440) -> None:
    import cairosvg

    png_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=width,
    )


def _annotate_png(png_path: Path, caption: str) -> None:
    """Burn a short caption onto the frame with ffmpeg."""
    tmp = png_path.with_suffix(".tmp.png")
    filter_expr = (
        "drawbox=x=0:y=0:w=iw:h=56:color=black@0.55:t=fill,"
        f"drawtext=text='{caption}':fontcolor=white:fontsize=28:x=24:y=16"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(png_path),
            "-vf",
            filter_expr,
            str(tmp),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    tmp.replace(png_path)


async def _capture_before_frame(svg_path: Path) -> None:
    """Synthetic pre-PR layout: Name + Type only (no Size column or sort indicator)."""
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import DataTable, Footer, Header, Input, Static

    class BeforeBrowserDemo(App):
        CSS_PATH = REPO_ROOT / "dispatch" / "app.tcss"

        def compose(self) -> ComposeResult:
            yield Header(show_clock=False)
            with Vertical(id="main-content"):
                with Vertical(id="browser-content"):
                    yield Static("[bold]Browse Impala Metadata[/]", classes="section-title")
                    with Horizontal(id="browser-split"):
                        with Vertical(id="browser-left"):
                            yield Static("[dim]Schema · table filter[/]", classes="input-caption")
                            with Horizontal(id="browser-query-row"):
                                yield Input(value="aa_enc", placeholder="Schema", id="schema")
                                yield Input(value="*", placeholder="Filter", id="filter")
                            table = DataTable(id="browser-table")
                            yield table
                            yield Static("[dim]2 tables[/]", id="browser-count")
                        with Vertical(id="browser-right"):
                            yield Static("[dim]No table selected[/]", id="file-preview-title")
                            yield Static(
                                "Select a table and press Enter to view its schema.",
                                id="describe-body",
                            )
            yield Footer()

        async def on_mount(self) -> None:
            table = self.query_one("#browser-table", DataTable)
            table.add_columns("Name", "Type")
            table.cursor_type = "row"
            for name in DEMO_TABLES:
                table.add_row(name, "table")

    app = BeforeBrowserDemo()
    async with app.run_test(size=(140, 44)) as pilot:
        await pilot.pause(0.6)
        app.save_screenshot(filename=str(svg_path))


async def _capture_after_frames(frame_paths: list[tuple[Path, str]]) -> None:
    """Capture the new Browse behavior: sizes loaded, then sorted by size."""
    from dispatch.app import DispatchApp
    from dispatch.screens.browser import BrowserScreen

    app = DispatchApp()
    async with app.run_test(size=(140, 44)) as pilot:
        screen = BrowserScreen(auto_load=False)
        app.push_screen(screen)
        await pilot.pause(0.5)

        svg_loaded = FRAMES_DIR / "_after_loaded.svg"
        await screen.action_show_tables(describe_selection=False)
        await pilot.pause(0.6)
        app.save_screenshot(filename=str(svg_loaded))
        frame_paths.append((svg_loaded, "AFTER: Size column populated (sorted by name)"))

        svg_size_sort = FRAMES_DIR / "_after_size_sort.svg"
        screen.action_cycle_sort()
        await pilot.pause(0.6)
        app.save_screenshot(filename=str(svg_size_sort))
        frame_paths.append((svg_size_sort, "AFTER: Press O — sorted by size (largest first)"))


def _assemble_video(png_paths: list[Path], mp4_path: Path, gif_path: Path) -> None:
    mp4_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = FRAMES_DIR / "concat.txt"
    # Hold each frame for 3.5s so viewers can read the table.
    with list_file.open("w", encoding="utf-8") as handle:
        for png in png_paths:
            handle.write(f"file '{png}'\n")
            handle.write("duration 3.5\n")
        handle.write(f"file '{png_paths[-1]}'\n")

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
            "scale=1280:-2:flags=lanczos,format=yuv420p",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(mp4_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(mp4_path),
            "-vf",
            "fps=2,scale=960:-2:flags=lanczos",
            "-loop",
            "0",
            str(gif_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


async def main() -> int:
    try:
        import cairosvg  # noqa: F401
    except ImportError as exc:
        print("Missing dependency cairosvg. Install with: python3 -m pip install cairosvg")
        raise SystemExit(1) from exc

    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    launch_cwd = _bootstrap_environment()
    _install_healthy_kerberos()
    _install_demo_impala()
    os.chdir(launch_cwd)

    from dispatch import config
    from dispatch.version import __version__

    config.installed_version_path().write_text(__version__, encoding="utf-8")

    captures: list[tuple[Path, str]] = []

    before_svg = FRAMES_DIR / "_before.svg"
    await _capture_before_frame(before_svg)
    captures.append((before_svg, "BEFORE: Name + Type only (no Size column)"))

    await _capture_after_frames(captures)

    png_paths: list[Path] = []
    for index, (svg_path, caption) in enumerate(captures, start=1):
        png_path = FRAMES_DIR / f"browse-table-size-pr1-{index:02d}.png"
        _svg_to_png(svg_path, png_path)
        _annotate_png(png_path, caption)
        png_paths.append(png_path)
        svg_path.unlink(missing_ok=True)
        print(f"frame {index}: {png_path.relative_to(REPO_ROOT)}")

    _assemble_video(png_paths, VIDEO_MP4, VIDEO_GIF)
    print(f"video: {VIDEO_MP4.relative_to(REPO_ROOT)}")
    print(f"gif:   {VIDEO_GIF.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
