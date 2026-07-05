#!/usr/bin/env python3
"""Record a short demo video for PR #7: EID-prefixed table names in New Job.

Captures representative Textual screenshots via the pilot API, converts them to
PNG, and assembles an MP4 with a brief synthetic "before" slide for contrast.

Usage (from repo root):
    /workspace/.venv/bin/python docs/videos/record_eid_table_name_prefix_demo.py

Output:
    docs/videos/pr7-eid-table-name-prefix-demo.mp4
    docs/videos/frames-pr7-eid-table-name-prefix/*.png
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "docs" / "videos"
FRAMES_DIR = OUT_DIR / "frames-pr7-eid-table-name-prefix"
VIDEO_PATH = OUT_DIR / "pr7-eid-table-name-prefix-demo.mp4"
MOCKS_BIN = REPO_ROOT / "mocks" / "bin"
SCR_DIR = REPO_ROOT / "scr"

WIDTH, HEIGHT = 180, 52
FRAME_SECONDS = 3.5
TITLE_SECONDS = 4.0


def _annotate_frame(src: Path, dst: Path, caption: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    with Image.open(src) as image:
        rgb = image.convert("RGB")
        draw = ImageDraw.Draw(rgb)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        except OSError:
            font = ImageFont.load_default()
        bar_h = 56
        draw.rectangle((0, rgb.height - bar_h, rgb.width, rgb.height), fill=(20, 24, 32))
        draw.text((24, rgb.height - bar_h + 14), caption, fill=(210, 230, 255), font=font)
        rgb.save(dst)


def _ensure_deps() -> None:
    try:
        import cairosvg  # noqa: F401
        from PIL import Image, ImageDraw, ImageFont  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "Demo recorder needs cairosvg and pillow:\n"
            "  /workspace/.venv/bin/python -m pip install cairosvg pillow"
        ) from exc


def _setup_env(launch_dir: Path, data_root: Path, state_dir: Path) -> None:
    launch_dir.mkdir(parents=True, exist_ok=True)
    data_root.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    os.environ["PATH"] = str(MOCKS_BIN) + os.pathsep + os.environ.get("PATH", "")
    os.environ["DISPATCH_MOCK_STATE_DIR"] = str(state_dir)
    os.environ["DISPATCH_DATA_ROOT"] = str(data_root)
    os.environ["DISPATCH_SCR_DIR"] = str(SCR_DIR)
    os.environ["DISPATCH_MOCK_SCENARIO"] = "happy_path"
    os.environ["DISPATCH_MOCK_DELAY"] = "0"
    os.environ["MAILHOST"] = "127.0.0.1:9"
    os.environ["DISPATCH_EMAIL"] = "demo@example.com"

    dispatch_home = data_root / ".dispatch"
    dispatch_home.mkdir(parents=True, exist_ok=True)
    (dispatch_home / "config.json").write_text(
        json.dumps({"to_email": "demo@example.com"}),
        encoding="utf-8",
    )

    sql_path = launch_dir / "query.sql"
    if not sql_path.exists():
        sql_path.write_text(
            "SELECT id, amount\n"
            "FROM payments\n"
            "WHERE ds BETWEEN '2026-05-01' AND '2026-05-31';\n",
            encoding="utf-8",
        )


def _render_before_slide(path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (1280, 720), color=(18, 18, 24))
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        mono_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 24)
    except OSError:
        title_font = body_font = mono_font = ImageFont.load_default()

    draw.text((70, 70), "Before PR #7", fill=(255, 140, 90), font=title_font)
    draw.text(
        (70, 150),
        "New Job › Table Name was one fully editable field.",
        fill=(230, 230, 230),
        font=body_font,
    )
    draw.text(
        (70, 210),
        "Users could type any identifier with no EID ownership guard.",
        fill=(180, 180, 180),
        font=body_font,
    )

    box_x, box_y, box_w, box_h = 70, 300, 1140, 90
    draw.rounded_rectangle((box_x, box_y, box_x + box_w, box_y + box_h), radius=12, outline=(90, 90, 110), width=2)
    draw.text((box_x + 24, box_y + 16), "Table Name", fill=(150, 150, 170), font=body_font)
    draw.text((box_x + 260, box_y + 28), "dispatch_result", fill=(255, 255, 255), font=mono_font)

    draw.text(
        (70, 430),
        "After PR #7: fixed EID_ prefix + editable suffix only.",
        fill=(120, 220, 160),
        font=body_font,
    )
    draw.text(
        (70, 490),
        "Final launched name format: EID_suffix (example: ubuntu_monthly_export)",
        fill=(150, 200, 170),
        font=body_font,
    )

    img.save(path)


def _svg_to_png(svg_path: Path, png_path: Path) -> None:
    import cairosvg

    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1280)


def _fit_png(src: Path, dst: Path) -> None:
    from PIL import Image

    with Image.open(src) as image:
        image.convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS).save(dst)


async def _capture_frames(frames: list[tuple[str, str]]) -> None:
    from dispatch import config
    from dispatch.app import DispatchApp
    from dispatch.screens.new_job import NewJobScreen

    eid = config.current_user()
    root = Path(tempfile.mkdtemp(prefix="dispatch-pr7-demo-"))
    launch_dir = root / "launch"
    data_root = root / "data"
    state_dir = root / "state"
    _setup_env(launch_dir, data_root, state_dir)
    os.chdir(launch_dir)

    async def save_step(app: DispatchApp, name: str) -> None:
        svg_path = FRAMES_DIR / f"{name}.svg"
        app.save_screenshot(filename=svg_path.name, path=str(FRAMES_DIR))
        raw_png = FRAMES_DIR / f"{name}.raw.png"
        _svg_to_png(svg_path, raw_png)
        _fit_png(raw_png, FRAMES_DIR / f"{name}.png")
        raw_png.unlink(missing_ok=True)

    app = DispatchApp()
    async with app.run_test(size=(WIDTH, HEIGHT)) as pilot:
        screen = NewJobScreen(launch_dir)
        app.push_screen(screen)
        await pilot.pause(1.0)

        # Csv-only: table name row hidden (not a table-creation flow).
        screen._force_radio("#destination", "dst-csv")
        await pilot.pause(0.8)
        await save_step(app, "01_csv_only_hidden_table_name")

        # Table destination: fixed EID prefix with default suffix.
        screen._force_radio("#destination", "dst-table")
        await pilot.pause(0.8)
        await save_step(app, "02_table_destination_eid_prefix")

        # User edits only the suffix; full name becomes EID_suffix.
        screen.query_one("#table-name-suffix").value = "monthly_export"
        await pilot.pause(0.8)
        await save_step(app, "03_suffix_edited")

        # Pasting a full EID_suffix strips the fixed prefix back to suffix only.
        screen.query_one("#table-name-suffix").value = f"{eid}_cloned_job"
        await pilot.pause(0.8)
        await save_step(app, "04_paste_strips_prefix")

        # Validation summary reflects the enforced full table name.
        screen._update_validation_summary()
        await pilot.pause(0.5)
        await save_step(app, "05_ready_to_launch")

        frame_specs = [
            ("00_before_single_editable_field", "BEFORE: single editable Table Name field"),
            (
                "01_csv_only_hidden_table_name",
                "Csv-only: Table Name row hidden (not table creation)",
            ),
            (
                "02_table_destination_eid_prefix",
                f"Table: fixed {eid}_ prefix + editable suffix (default dispatch_result)",
            ),
            (
                "03_suffix_edited",
                f"User edits suffix only → full name {eid}_monthly_export",
            ),
            (
                "04_paste_strips_prefix",
                f"Paste {eid}_cloned_job → suffix normalizes to cloned_job",
            ),
            (
                "05_ready_to_launch",
                f"Validation uses enforced {eid}_cloned_job before launch",
            ),
        ]
        for stem, caption in frame_specs:
            src = FRAMES_DIR / f"{stem}.png"
            dst = FRAMES_DIR / f"{stem}_captioned.png"
            _annotate_frame(src, dst, caption)
            frames.append((dst.name, caption))


def _assemble_video(frame_files: list[Path], durations: list[float]) -> None:
    concat_lines: list[str] = []
    for frame, seconds in zip(frame_files, durations, strict=True):
        concat_lines.append(f"file '{frame}'")
        concat_lines.append(f"duration {seconds}")

    # Repeat last frame so ffmpeg concat demuxer keeps final scene visible.
    concat_lines.append(f"file '{frame_files[-1]}'")

    list_path = FRAMES_DIR / "ffmpeg_concat.txt"
    list_path.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-vf",
            "fps=30,format=yuv420p",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(VIDEO_PATH),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    _ensure_deps()
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    before_png = FRAMES_DIR / "00_before_single_editable_field.png"
    _render_before_slide(before_png)

    captured: list[tuple[str, str]] = []
    asyncio.run(_capture_frames(captured))

    frame_paths = [FRAMES_DIR / name for name, _label in captured]
    durations = [TITLE_SECONDS] + [FRAME_SECONDS] * (len(frame_paths) - 1)

    _assemble_video(frame_paths, durations)
    print(f"Wrote demo video: {VIDEO_PATH}")
    print(f"Frame PNGs: {FRAMES_DIR}")


if __name__ == "__main__":
    main()
