#!/usr/bin/env python3
"""Generate PR #11 demo video: SqlTemplate label renamed to MonthlyJob.

Captures Textual SVG screenshots of the New Job flow (before vs after) and
stitches them into an MP4 with ffmpeg. Does not modify application source.

Run from repo root:
    /workspace/.venv/bin/python demos/pr11-monthlyjob-label/generate_demo.py

Output:
    demos/pr11-monthlyjob-label/monthlyjob-label-pr11-demo.mp4
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = Path(__file__).resolve().parent
FRAMES_DIR = OUT_DIR / "frames"
VIDEO_PATH = OUT_DIR / "monthlyjob-label-pr11-demo.mp4"
TERMINAL_SIZE = (140, 50)
HEALTHY_TTL_SECONDS = 8 * 3600

TEMPLATE_SQL = (
    "SELECT region, SUM(amount) AS total\n"
    "FROM sales\n"
    "WHERE sale_date BETWEEN '{date_inicio}' AND '{date_fim}'\n"
    "GROUP BY region\n"
)


def _bootstrap_environment(launch_cwd: Path) -> None:
    data_root = launch_cwd.parent / "data"
    dispatch_home = data_root / ".dispatch"
    dispatch_home.mkdir(parents=True, exist_ok=True)
    (dispatch_home / "config.json").write_text(
        '{"to_email": "analyst@example.com"}', encoding="utf-8"
    )
    launch_cwd.mkdir(parents=True, exist_ok=True)
    (launch_cwd / "monthly_revenue.sql").write_text(TEMPLATE_SQL, encoding="utf-8")
    (launch_cwd / "plain_query.sql").write_text("SELECT 1\n", encoding="utf-8")

    os.environ["DISPATCH_DATA_ROOT"] = str(data_root)
    os.environ["DISPATCH_EMAIL"] = "analyst@example.com"
    os.environ.setdefault("USER", "analyst")
    os.environ.setdefault("DISPATCH_MOCK_SCENARIO", "happy_path")

    import dispatch.kerberos as kerberos
    from dispatch import config
    from dispatch.version import __version__

    async def _fake_ttl() -> int:
        return HEALTHY_TTL_SECONDS

    kerberos.ticket_ttl_seconds = _fake_ttl  # type: ignore[assignment]
    config.installed_version_path().write_text(__version__, encoding="utf-8")


def _apply_label_mode(mode: str) -> None:
    """Simulate before (SqlTemplate) or after (MonthlyJob) display labels."""
    from dispatch import manifest

    if mode == "before":
        manifest.SOURCE_DISPLAY_LABELS["SqlTemplate"] = "SqlTemplate"
    else:
        manifest.SOURCE_DISPLAY_LABELS["SqlTemplate"] = "MonthlyJob"


async def _capture_new_job(name: str, *, select_template: bool, expand_matrix: bool) -> Path:
    from textual.widgets import RadioButton

    from dispatch.app import DispatchApp
    from dispatch.screens.new_job import NewJobScreen

    out_path = FRAMES_DIR / f"{name}.svg"
    launch_cwd = Path(tempfile.mkdtemp(prefix=f"dispatch-demo-{name}-")) / "sql"
    _bootstrap_environment(launch_cwd)

    app = DispatchApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        screen = NewJobScreen(launch_cwd)
        app.push_screen(screen)
        await pilot.pause(1.0)

        if expand_matrix:
            await pilot.press("m")
            await pilot.pause(0.4)

        if select_template:
            screen.query_one("#src-sqltemplate", RadioButton).value = True
            await pilot.pause(0.5)
            # Ensure picker highlights the template file.
            picker = screen.query_one("#sql-file-picker")
            if picker.display and picker.row_count > 1:
                picker.focus()
                await pilot.press("down")
                await pilot.pause(0.5)

        app.save_screenshot(filename=str(out_path))

    if not out_path.exists():
        raise RuntimeError(f"Screenshot not written: {out_path}")
    return out_path


async def _capture_preview(name: str) -> Path:
    from textual.widgets import RadioButton

    from dispatch.app import DispatchApp
    from dispatch.screens.new_job import NewJobScreen

    out_path = FRAMES_DIR / f"{name}.svg"
    launch_cwd = Path(tempfile.mkdtemp(prefix=f"dispatch-demo-{name}-")) / "sql"
    _bootstrap_environment(launch_cwd)

    app = DispatchApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        screen = NewJobScreen(launch_cwd)
        app.push_screen(screen)
        await pilot.pause(1.0)
        screen.query_one("#src-sqltemplate", RadioButton).value = True
        await pilot.pause(0.4)
        await pilot.press("p")
        await pilot.pause(0.6)
        app.save_screenshot(filename=str(out_path))

    if not out_path.exists():
        raise RuntimeError(f"Screenshot not written: {out_path}")
    return out_path


def _svg_to_png(svg_path: Path, png_path: Path, width: int = 1280, height: int = 720) -> None:
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x1e1e1e"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(svg_path),
            "-vf",
            vf,
            "-frames:v",
            "1",
            "-update",
            "1",
            str(png_path),
        ],
        check=True,
        capture_output=True,
    )


def _title_card(text: str, png_path: Path, *, subtitle: str = "") -> None:
    safe = text.replace(":", "\\:").replace("'", "\\'")
    sub = subtitle.replace(":", "\\:").replace("'", "\\'")
    draw = f"drawtext=text='{safe}':fontsize=42:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-30"
    if subtitle:
        draw += (
            f",drawtext=text='{sub}':fontsize=24:fontcolor=0xaaaaaa:"
            "x=(w-text_w)/2:y=(h-text_h)/2+30"
        )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x1e1e1e:s=1280x720",
            "-vf",
            draw,
            "-frames:v",
            "1",
            "-update",
            "1",
            str(png_path),
        ],
        check=True,
        capture_output=True,
    )


def _build_video(frame_specs: list[tuple[Path, float]], output: Path) -> None:
    """Concatenate still frames with per-frame duration into H.264 MP4."""
    concat_lines: list[str] = []
    for png_path, seconds in frame_specs:
        concat_lines.append(f"file '{png_path}'")
        concat_lines.append(f"duration {seconds}")

    # Repeat last frame so ffmpeg concat demuxer keeps final duration.
    concat_lines.append(f"file '{frame_specs[-1][0]}'")

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
        handle.write("\n".join(concat_lines))
        concat_path = handle.name

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                concat_path,
                "-vf",
                "fps=30,format=yuv420p",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output),
            ],
            check=True,
            capture_output=True,
        )
    finally:
        Path(concat_path).unlink(missing_ok=True)


async def _generate_screenshots() -> list[tuple[str, Path]]:
    captures: list[tuple[str, Path]] = []

    _apply_label_mode("before")
    captures.append(
        (
            "01_before_matrix",
            await _capture_new_job("01_before_matrix", select_template=False, expand_matrix=True),
        )
    )
    captures.append(
        (
            "02_before_selected",
            await _capture_new_job("02_before_selected", select_template=True, expand_matrix=False),
        )
    )
    captures.append(
        ("03_before_preview", await _capture_preview("03_before_preview")),
    )

    _apply_label_mode("after")
    captures.append(
        (
            "04_after_matrix",
            await _capture_new_job("04_after_matrix", select_template=False, expand_matrix=True),
        )
    )
    captures.append(
        (
            "05_after_selected",
            await _capture_new_job("05_after_selected", select_template=True, expand_matrix=False),
        )
    )
    captures.append(
        ("06_after_preview", await _capture_preview("06_after_preview")),
    )

    return captures


def _verify_capture(svg_path: Path, required: list[str], forbidden: list[str]) -> None:
    sys.path.insert(0, str(REPO_ROOT / "tools" / "dev"))
    from svg_text import svg_to_text  # noqa: E402

    text = svg_to_text(svg_path.read_text(encoding="utf-8"))
    for needle in required:
        if needle not in text:
            raise AssertionError(f"{svg_path.name}: missing {needle!r} in capture")
    for needle in forbidden:
        if needle in text:
            raise AssertionError(f"{svg_path.name}: unexpected {needle!r} in capture")


def main() -> int:
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    captures = asyncio.run(_generate_screenshots())

    _verify_capture(captures[0][1], ["SqlTemplate"], ["MonthlyJob"])
    _verify_capture(captures[1][1], ["SqlTemplate supports Table only"], ["MonthlyJob"])
    _verify_capture(captures[2][1], ["SqlTemplate", "SQL Preview"], ["MonthlyJob"])
    _verify_capture(captures[3][1], ["MonthlyJob"], ["SqlTemplate"])
    _verify_capture(captures[4][1], ["MonthlyJob supports Table only"], ["SqlTemplate"])
    _verify_capture(captures[5][1], ["MonthlyJob", "SQL Preview"], ["SqlTemplate"])

    png_specs: list[tuple[Path, float]] = []

    title_before = FRAMES_DIR / "title_before.png"
    title_after = FRAMES_DIR / "title_after.png"
    _title_card(
        "Before PR #11",
        title_before,
        subtitle="New Job source option: SqlTemplate",
    )
    _title_card(
        "After PR #11",
        title_after,
        subtitle="New Job source option: MonthlyJob",
    )
    png_specs.append((title_before, 2.5))

    for name, svg_path in captures[:3]:
        png_path = FRAMES_DIR / f"{name}.png"
        _svg_to_png(svg_path, png_path)
        png_specs.append((png_path, 3.5))

    png_specs.append((title_after, 2.5))

    for name, svg_path in captures[3:]:
        png_path = FRAMES_DIR / f"{name}.png"
        _svg_to_png(svg_path, png_path)
        png_specs.append((png_path, 3.5))

    _build_video(png_specs, VIDEO_PATH)
    print(f"Wrote demo video: {VIDEO_PATH}")
    print(f"Frame assets: {FRAMES_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
