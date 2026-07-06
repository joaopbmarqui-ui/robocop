#!/usr/bin/env python3
"""Generate a before/after demo video for the New Job email placeholder change.

Captures Textual SVG screenshots of the email field (empty value, no
DISPATCH_EMAIL) and assembles them into an MP4 under demos/.

Usage (from repo root, with mocks/dev-env sourced optional):

    /workspace/.venv/bin/python demos/record_email_placeholder_demo.py

Output:

    demos/email-placeholder-new-job-demo.mp4
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dispatch import config
from dispatch.app import DispatchApp
from dispatch.screens.new_job import NewJobScreen

OLD_PLACEHOLDER = "user@example.com"
NEW_PLACEHOLDER = "name.surname@mastercard.com,name2.surname2@mastercard.com"
OUTPUT_MP4 = REPO_ROOT / "demos" / "email-placeholder-new-job-demo.mp4"
FRAME_SECONDS = 3.5


def _require_deps() -> None:
    try:
        import cairosvg  # noqa: F401
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:  # pragma: no cover - demo helper
        raise SystemExit(
            "Demo requires cairosvg and pillow:\n"
            "  /workspace/.venv/bin/pip install cairosvg pillow"
        ) from exc
    globals()["Image"] = Image
    globals()["ImageDraw"] = ImageDraw
    globals()["ImageFont"] = ImageFont


def _title_slide(title: str, subtitle: str, accent: str) -> Path:
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1280, 720
    img = Image.new("RGB", (width, height), "#121212")
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        mono_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuMono.ttf", 24)
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = title_font
        mono_font = title_font

    draw.text((64, 120), title, fill=accent, font=title_font)
    draw.text((64, 220), subtitle, fill="#e0e0e0", font=sub_font)
    draw.text((64, 320), "Dispatch · New Job · Email (notifications)", fill="#9e9e9e", font=mono_font)
    draw.text((64, 380), "PR: email placeholder update", fill="#656565", font=mono_font)

    out = Path(tempfile.mkstemp(suffix=".png")[1])
    img.save(out)
    return out


def _svg_to_png(svg_path: Path, png_path: Path) -> None:
    import cairosvg

    cairosvg.svg2png(url=svg_path.as_uri(), write_to=str(png_path), output_width=1280)


async def _capture_email_field_screenshot(
    *,
    placeholder: str,
    source_button: str | None = None,
    destination_button: str | None = None,
) -> Path:
    os.environ.pop("DISPATCH_EMAIL", None)
    config.save_form_defaults({})

    demo_cwd = Path(tempfile.mkdtemp(prefix="dispatch-email-demo-"))
    (demo_cwd / "query.sql").write_text("select 1 as id\n", encoding="utf-8")

    svg_path = Path(tempfile.mkstemp(suffix=".svg")[1])
    app = DispatchApp()

    async with app.run_test(size=(165, 58)) as pilot:
        app.push_screen(NewJobScreen(demo_cwd))
        await pilot.pause(1.2)
        screen = app.screen
        email_input = screen.query_one("#email")
        email_input.value = ""
        email_input.placeholder = placeholder

        if source_button:
            screen.query_one(f"#{source_button}").value = True
            await pilot.pause(0.4)
        if destination_button:
            screen.query_one(f"#{destination_button}").value = True
            await pilot.pause(0.4)

        screen.query_one("#row-email").scroll_visible(animate=False)
        await pilot.pause(0.4)
        app.save_screenshot(filename=str(svg_path))

    png_path = Path(tempfile.mkstemp(suffix=".png")[1])
    _svg_to_png(svg_path, png_path)
    return png_path


def _build_video(frames: list[tuple[Path, float]]) -> None:
    with tempfile.TemporaryDirectory(prefix="dispatch-demo-frames-") as tmp:
        tmp_path = Path(tmp)
        segment_paths: list[Path] = []
        for index, (image_path, duration) in enumerate(frames):
            segment_path = tmp_path / f"segment_{index:02d}.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    str(image_path),
                    "-t",
                    str(duration),
                    "-vf",
                    "scale=1280:720:force_original_aspect_ratio=decrease,"
                    "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=#121212",
                    "-r",
                    "30",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(segment_path),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            segment_paths.append(segment_path)

        concat_file = tmp_path / "concat.txt"
        concat_file.write_text(
            "\n".join(f"file '{path}'" for path in segment_paths) + "\n",
            encoding="utf-8",
        )

        OUTPUT_MP4.parent.mkdir(parents=True, exist_ok=True)
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
                "-c",
                "copy",
                str(OUTPUT_MP4),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


async def main() -> None:
    _require_deps()

    before_png = await _capture_email_field_screenshot(placeholder=OLD_PLACEHOLDER)
    after_png = await _capture_email_field_screenshot(placeholder=NEW_PLACEHOLDER)
    after_template_png = await _capture_email_field_screenshot(
        placeholder=NEW_PLACEHOLDER,
        source_button="src-sqltemplate",
        destination_button="dst-table",
    )
    after_existing_png = await _capture_email_field_screenshot(
        placeholder=NEW_PLACEHOLDER,
        source_button="src-existingtable",
        destination_button="dst-csv",
    )

    frames: list[tuple[Path, float]] = [
        (
            _title_slide(
                "Before",
                f'Placeholder: "{OLD_PLACEHOLDER}"',
                "#f0ad4e",
            ),
            FRAME_SECONDS,
        ),
        (before_png, FRAME_SECONDS),
        (
            _title_slide(
                "After (this PR)",
                f'Placeholder: "{NEW_PLACEHOLDER}"',
                "#5cb85c",
            ),
            FRAME_SECONDS,
        ),
        (after_png, FRAME_SECONDS),
        (
            _title_slide(
                "Consistent across flows",
                "SqlTemplate → Table (email field unchanged)",
                "#5bc0de",
            ),
            FRAME_SECONDS * 0.85,
        ),
        (after_template_png, FRAME_SECONDS),
        (
            _title_slide(
                "Consistent across flows",
                "ExistingTable → Csv (email field unchanged)",
                "#5bc0de",
            ),
            FRAME_SECONDS * 0.85,
        ),
        (after_existing_png, FRAME_SECONDS),
    ]

    _build_video(frames)
    print(f"Wrote demo video: {OUTPUT_MP4}")


if __name__ == "__main__":
    asyncio.run(main())
