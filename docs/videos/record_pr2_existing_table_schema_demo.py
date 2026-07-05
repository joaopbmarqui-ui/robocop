#!/usr/bin/env python3
"""Record an animated GIF demo for PR #2: ExistingTable schema selector.

Drives the real Dispatch Textual app through ``run_test``, captures SVG
screenshots at each step, converts them to PNG, and assembles a GIF with
step captions burned in.

Usage::

    source mocks/dev-env.sh
    python3 -m pip install cairosvg pillow   # one-time demo deps
    python3 docs/videos/record_pr2_existing_table_schema_demo.py

Output::

    docs/videos/pr2-existing-table-schema-demo.gif
    docs/videos/pr2-existing-table-schema-demo/frames/*.png
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = Path(__file__).resolve().parent
FRAMES_DIR = OUT_DIR / "pr2-existing-table-schema-demo" / "frames"
GIF_PATH = OUT_DIR / "pr2-existing-table-schema-demo.gif"
TERMINAL_SIZE = (120, 40)
PNG_WIDTH = 1200
FRAME_MS = 2200


@dataclass(frozen=True)
class DemoStep:
    slug: str
    caption: str
    action: object  # async (pilot, app, screen) -> None


def _bootstrap_environment() -> Path:
    base = Path(tempfile.mkdtemp(prefix="dispatch-pr2-demo-"))
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
    import dispatch.kerberos as kerberos

    async def _fake_ttl() -> int:
        return 8 * 3600

    kerberos.ticket_ttl_seconds = _fake_ttl  # type: ignore[assignment]


def _write_installed_version() -> None:
    from dispatch import config
    from dispatch.version import __version__

    config.installed_version_path().write_text(__version__, encoding="utf-8")


async def _open_new_job(pilot, app, screen) -> None:
    pass


async def _select_existing_table(pilot, app, screen) -> None:
    from textual.widgets import RadioButton

    screen.query_one("#src-existingtable", RadioButton).value = True
    await pilot.pause(0.35)


async def _select_coe_enc(pilot, app, screen) -> None:
    from textual.widgets import Input, RadioButton

    screen.query_one("#existing-schema-coe", RadioButton).value = True
    screen.query_one("#existing-table", Input).value = "events_existing"
    await pilot.pause(0.35)


async def _select_other_custom_schema(pilot, app, screen) -> None:
    from textual.widgets import Input, RadioButton

    screen.query_one("#existing-schema-other", RadioButton).value = True
    screen.query_one("#schema", Input).value = "analytics"
    screen.query_one("#existing-table", Input).value = "events_existing"
    await pilot.pause(0.35)


async def _show_aa_enc_default(pilot, app, screen) -> None:
    from textual.widgets import Input, RadioButton

    screen.query_one("#existing-schema-aa", RadioButton).value = True
    screen.query_one("#existing-table", Input).value = "dispatch_smoke_seed"
    await pilot.pause(0.35)


STEPS: list[DemoStep] = [
    DemoStep(
        "before-sqlfile",
        "Before: SqlFile selected — no ExistingTable schema controls",
        _open_new_job,
    ),
    DemoStep(
        "existingtable-schema-selector",
        "After: ExistingTable shows coe_enc / aa_enc / other schema selector",
        _select_existing_table,
    ),
    DemoStep(
        "preset-coe-enc",
        "Preset coe_enc: manual Schema field stays hidden",
        _select_coe_enc,
    ),
    DemoStep(
        "custom-other-schema",
        'Other: manual Schema input enabled (analytics.events_existing)',
        _select_other_custom_schema,
    ),
    DemoStep(
        "preset-aa-enc",
        "Preset aa_enc: table name only — launch uses aa_enc.dispatch_smoke_seed",
        _show_aa_enc_default,
    ),
]


def _svg_to_png(svg_path: Path) -> bytes:
    try:
        import cairosvg
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise SystemExit(
            "Missing demo dependency cairosvg. Install with:\n"
            "  python3 -m pip install cairosvg pillow"
        ) from exc
    return cairosvg.svg2png(url=str(svg_path), output_width=PNG_WIDTH)


def _captioned_png(svg_path: Path, caption: str, out_path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise SystemExit(
            "Missing demo dependency pillow. Install with:\n"
            "  python3 -m pip install cairosvg pillow"
        ) from exc

    base = Image.open(BytesIO(_svg_to_png(svg_path))).convert("RGBA")
    bar_h = 56
    canvas = Image.new("RGBA", (base.width, base.height + bar_h), (18, 18, 18, 255))
    canvas.paste(base, (0, bar_h))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    draw.text((16, 16), caption, fill=(240, 240, 240, 255), font=font)
    canvas.convert("RGB").save(out_path, format="PNG")


def _build_gif(frame_paths: list[Path], out_path: Path) -> None:
    from PIL import Image

    images = [Image.open(path).convert("P", palette=Image.ADAPTIVE) for path in frame_paths]
    images[0].save(
        out_path,
        save_all=True,
        append_images=images[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
    )


async def _capture_demo() -> list[Path]:
    from dispatch.app import DispatchApp
    from dispatch.screens.new_job import NewJobScreen

    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    svg_dir = FRAMES_DIR / "svg"
    svg_dir.mkdir(exist_ok=True)
    png_paths: list[Path] = []

    app = DispatchApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause(0.6)
        app.push_screen(NewJobScreen(app.launch_cwd))
        await pilot.pause(0.6)
        screen = app.screen

        for index, step in enumerate(STEPS, start=1):
            await step.action(pilot, app, screen)
            svg_path = svg_dir / f"{step.slug}.svg"
            app.save_screenshot(str(svg_path))
            png_path = FRAMES_DIR / f"{index:02d}-{step.slug}.png"
            _captioned_png(svg_path, step.caption, png_path)
            png_paths.append(png_path)
            print(f"Captured {png_path.relative_to(REPO_ROOT)}")

    return png_paths


def main() -> int:
    launch_cwd = _bootstrap_environment()
    _install_healthy_kerberos()
    _write_installed_version()
    os.chdir(launch_cwd)

    if FRAMES_DIR.exists():
        import shutil

        shutil.rmtree(FRAMES_DIR)
    frame_paths = asyncio.run(_capture_demo())
    _build_gif(frame_paths, GIF_PATH)
    print(f"\nGIF written -> {GIF_PATH.relative_to(REPO_ROOT)}")
    print(f"Frame PNGs -> {FRAMES_DIR.relative_to(REPO_ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
