#!/usr/bin/env python3
"""Silent visual New Job onboarding video for Dispatch (Robocop).

Captures the real Dispatch Textual UI (DispatchApp → Overview → N → NewJobScreen)
and builds a narration-free walkthrough with:

- visible mouse cursor and click indicators
- field highlights
- short Brazilian Portuguese on-screen callouts
- silent audio track (no voice, no music)

Output package (demos/dispatch_robocop_new_job_onboarding_ptbr/):
  dispatch_robocop_new_job_onboarding_ptbr.mp4
  dispatch_robocop_new_job_captions_ptbr.srt
  dispatch_robocop_new_job_storyboard.md
  dispatch_robocop_new_job_video_download.zip

Run:
  source mocks/dev-env.sh
  /workspace/.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py
"""

from __future__ import annotations

import asyncio
import math
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
FRAMES_DIR = OUT_DIR / "frames"
CLIPS_DIR = OUT_DIR / "clips"
VIDEO_OUT = OUT_DIR / "dispatch_robocop_new_job_onboarding_ptbr.mp4"
CAPTIONS_OUT = OUT_DIR / "dispatch_robocop_new_job_captions_ptbr.srt"
STORYBOARD_OUT = OUT_DIR / "dispatch_robocop_new_job_storyboard.md"
ZIP_OUT = OUT_DIR / "dispatch_robocop_new_job_video_download.zip"
NARRATION_LEGACY = OUT_DIR / "dispatch_robocop_new_job_narration_ptbr.txt"

VIDEO_W, VIDEO_H = 1280, 720
BANNER_H = 0  # callouts are overlays; UI uses full canvas with bottom/top bars
FPS = 30
TERMINAL_SIZE = (150, 54)

DEMO_ROOT = Path("/tmp/dispatch_onboarding_silent")
LAUNCH_CWD = DEMO_ROOT / "sql"
DATA_ROOT = DEMO_ROOT / "data"

PLAIN_SQL = """\
-- Exemplo didático (não sensível)
SELECT
  region,
  amount
FROM sales
WHERE amount > 0
ORDER BY region;
"""

MONTHLY_SQL = """\
-- Consulta com intervalo de datas
SELECT
  region,
  SUM(amount) AS total
FROM sales
WHERE sale_date BETWEEN '{date_inicio}' AND '{date_fim}'
GROUP BY region;
"""


@dataclass
class Step:
    id: str
    capture: str  # capture key or "card:*"
    title: str
    body: str
    badge: str  # "" | "Obrigatório" | "Opcional" | "Use apenas quando..."
    cursor: tuple[float, float]  # normalized 0-1 over UI area
    hold: float = 3.2
    click: bool = False
    section: str = ""


# Cursor targets approximate New Job layout (sidebar ~12% width).
STEPS: list[Step] = [
    Step(
        "01_open",
        "card:open",
        "Dispatch (Robocop)",
        "Como utilizar a aba New Job\nConfigure e inicie um novo job passo a passo.",
        "",
        (0.5, 0.5),
        hold=3.5,
        section="Abertura",
    ),
    Step(
        "02_purpose",
        "arrive",
        "Para que serve",
        "A aba New Job permite configurar e iniciar uma nova execução no Dispatch.\n"
        "Você define a origem, o destino, a consulta e as opções de execução do job.",
        "",
        (0.55, 0.12),
        hold=4.2,
        section="Propósito",
    ),
    Step(
        "03_ready",
        "card:ready",
        "Antes de começar",
        "Tenha pronto:\n"
        "• o arquivo SQL do seu job (quando usar SqlFile ou MonthlyJob);\n"
        "• a origem e o destino desejados;\n"
        "• e-mail de notificação, se quiser receber aviso.",
        "",
        (0.5, 0.45),
        hold=4.5,
        section="Antes de começar",
    ),
    Step(
        "04_matrix",
        "matrix",
        "Source × Destination",
        "Mostra quais combinações de origem e destino são permitidas.\n"
        "Use como referência rápida antes de escolher as opções.",
        "Opcional",
        (0.52, 0.18),
        hold=3.8,
        click=True,
        section="Matriz",
    ),
    Step(
        "05_detected",
        "arrive",
        "Detected source",
        "Indica o tipo detectado no arquivo SQL selecionado.\n"
        "Confira se corresponde ao que você pretende executar.",
        "",
        (0.55, 0.28),
        hold=3.5,
        section="Detecção",
    ),
    Step(
        "06_source",
        "source_sqlfile",
        "Source",
        "Define de onde os dados serão obtidos.\n"
        "SqlFile: consulta em arquivo SQL.\n"
        "MonthlyJob: consulta com período de datas.\n"
        "ExistingTable: exporta uma tabela já existente.",
        "Obrigatório",
        (0.38, 0.36),
        hold=5.0,
        click=True,
        section="Source",
    ),
    Step(
        "07_destination",
        "source_sqlfile",
        "Destination",
        "Define onde o resultado do job será armazenado.\n"
        "Table: salva em tabela.\n"
        "Csv: gera arquivo CSV.\n"
        "Table+Csv: faz os dois.",
        "Obrigatório",
        (0.68, 0.36),
        hold=4.8,
        click=True,
        section="Destination",
    ),
    Step(
        "08_queue",
        "queues",
        "Execution Queue",
        "Define a fila em que o job será processado.\n"
        "Sem seleção = automático.\n"
        "Escolha conforme a orientação do seu projeto.",
        "Opcional",
        (0.55, 0.52),
        hold=4.5,
        click=True,
        section="Fila",
    ),
    Step(
        "09_picker",
        "picker",
        "Lista de arquivos SQL",
        "Lista os arquivos .sql da pasta atual.\n"
        "Selecione o arquivo do job para preencher o caminho.",
        "Obrigatório",
        (0.55, 0.62),
        hold=4.0,
        click=True,
        section="SQL",
    ),
    Step(
        "10_sql_file",
        "picker",
        "SQL File",
        "Caminho do arquivo SQL que será usado no job.\n"
        "Confirme se o arquivo indicado é o correto.",
        "Obrigatório",
        (0.58, 0.72),
        hold=3.6,
        section="SQL",
    ),
    Step(
        "11_email",
        "email_ok",
        "Email (notifications)",
        "Envia aviso quando o job terminar.\n"
        "Deixe em branco se não precisar de notificação.",
        "Opcional",
        (0.58, 0.78),
        hold=4.0,
        click=True,
        section="Notificação",
    ),
    Step(
        "12_subject",
        "email_ok",
        "Subject (email)",
        "Define o assunto do e-mail de notificação.\n"
        "Use um texto curto que identifique o job.",
        "Opcional",
        (0.58, 0.84),
        hold=3.6,
        click=True,
        section="Notificação",
    ),
    Step(
        "13_monthly",
        "monthly",
        "MonthlyJob",
        "Use quando o job precisa rodar com um intervalo de datas.\n"
        "Neste modo o destino fica em Table e aparecem Schema,\n"
        "Table Name, Start Date e End Date.",
        "Use apenas quando...",
        (0.38, 0.40),
        hold=5.2,
        click=True,
        section="MonthlyJob",
    ),
    Step(
        "14_monthly_fields",
        "monthly_fields",
        "Campos do MonthlyJob",
        "Schema e Table Name: onde o resultado será salvo.\n"
        "Start Date e End Date: período da consulta.\n"
        "Revise as datas antes de continuar.",
        "Obrigatório",
        (0.58, 0.78),
        hold=4.8,
        section="MonthlyJob",
    ),
    Step(
        "15_existing",
        "existing",
        "ExistingTable",
        "Use quando os dados já estão em uma tabela e você\n"
        "só precisa exportar o resultado em CSV.\n"
        "Neste modo o destino fica limitado a Csv.",
        "Use apenas quando...",
        (0.38, 0.44),
        hold=5.0,
        click=True,
        section="ExistingTable",
    ),
    Step(
        "16_existing_fields",
        "existing_fields",
        "Schema e Existing Table",
        "Escolha o schema e informe o nome da tabela existente.\n"
        "Se o schema não estiver na lista, use other.",
        "Obrigatório",
        (0.58, 0.72),
        hold=4.2,
        section="ExistingTable",
    ),
    Step(
        "17_back_sqlfile",
        "ready_review",
        "Exemplo prático",
        "Voltamos para SqlFile → Csv com o arquivo export_sales.sql.\n"
        "Este é o fluxo mais comum para gerar um CSV.",
        "",
        (0.55, 0.36),
        hold=4.0,
        click=True,
        section="Exemplo",
    ),
    Step(
        "18_validation_bad",
        "email_bad",
        "E-mail inválido",
        "Revise o formato antes de continuar.\n"
        "O status mostra o problema até a correção.",
        "",
        (0.58, 0.78),
        hold=4.0,
        section="Validação",
    ),
    Step(
        "19_validation_fix",
        "ready_review",
        "Pronto para enviar",
        "Com o e-mail corrigido, o status volta a Ready to launch.\n"
        "Confira origem, destino, arquivo e fila antes do envio.",
        "",
        (0.72, 0.92),
        hold=4.2,
        section="Validação",
    ),
    Step(
        "20_preview",
        "preview",
        "Preview",
        "Revise a configuração e o conteúdo do job antes do envio.\n"
        "Confirme se a consulta e o destino estão corretos.",
        "",
        (0.78, 0.92),
        hold=4.5,
        click=True,
        section="Preview",
    ),
    Step(
        "21_checklist",
        "card:checklist",
        "Antes de iniciar, confirme:",
        "• origem e destino;\n"
        "• arquivo selecionado;\n"
        "• fila de execução;\n"
        "• opções adicionais;\n"
        "• e-mail de notificação.",
        "",
        (0.5, 0.5),
        hold=5.0,
        section="Revisão",
    ),
    Step(
        "22_confirm",
        "confirm",
        "Launch Job",
        "Inicia o job com as configurações revisadas.\n"
        "Leia o resumo e confirme apenas se estiver correto.",
        "",
        (0.42, 0.72),
        hold=4.5,
        click=True,
        section="Envio",
    ),
    Step(
        "23_launched",
        "launched",
        "Job enviado",
        "O job foi enviado pelo Dispatch.\n"
        "Acompanhe o andamento na tela de monitoramento.",
        "",
        (0.55, 0.88),
        hold=4.0,
        section="Envio",
    ),
    Step(
        "24_overview",
        "overview",
        "Próximo passo",
        "Após o envio, acompanhe o status do job no Overview.",
        "",
        (0.12, 0.22),
        hold=3.8,
        click=True,
        section="Overview",
    ),
    Step(
        "25_close",
        "card:close",
        "Resumo",
        "Na aba New Job, você:\n"
        "1. define a execução;\n"
        "2. revisa as configurações;\n"
        "3. inicia o job;\n"
        "4. acompanha o resultado no Overview.\n\n"
        "Em caso de dúvida, revise os campos antes de selecionar Launch Job.",
        "",
        (0.5, 0.5),
        hold=6.0,
        section="Encerramento",
    ),
]


def _require_tools() -> None:
    missing = []
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")
    try:
        import cairosvg  # noqa: F401
        from PIL import Image, ImageDraw, ImageFont  # noqa: F401
    except ImportError as exc:
        missing.append(str(exc))
    try:
        import textual  # noqa: F401
    except ImportError:
        missing.append("textual==8.2.5 (pip install -r requirements.txt)")
    if missing:
        raise SystemExit("Missing dependencies:\n- " + "\n- ".join(missing))


def _bootstrap() -> Path:
    if DEMO_ROOT.exists():
        shutil.rmtree(DEMO_ROOT)
    home = DATA_ROOT / ".dispatch"
    home.mkdir(parents=True)
    (home / "config.json").write_text("{}", encoding="utf-8")
    LAUNCH_CWD.mkdir(parents=True)
    (LAUNCH_CWD / "export_sales.sql").write_text(PLAIN_SQL, encoding="utf-8")
    (LAUNCH_CWD / "monthly_revenue.sql").write_text(MONTHLY_SQL, encoding="utf-8")
    os.environ["USER"] = "analyst"
    os.environ["DISPATCH_DATA_ROOT"] = str(DATA_ROOT)
    os.environ["DISPATCH_MOCK_SCENARIO"] = "happy_path"
    os.environ["DISPATCH_MOCK_DELAY"] = "0"
    os.environ["DISPATCH_SCR_DIR"] = str(REPO_ROOT / "scr")
    os.environ["DISPATCH_MOCK_STATE_DIR"] = str(DEMO_ROOT / "mock_state")
    os.environ["MAILHOST"] = "127.0.0.1:9"
    os.environ["PATH"] = f"{REPO_ROOT / 'mocks' / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"
    os.environ.pop("DISPATCH_EMAIL", None)
    Path(os.environ["DISPATCH_MOCK_STATE_DIR"]).mkdir(parents=True, exist_ok=True)
    os.chdir(LAUNCH_CWD)
    return LAUNCH_CWD


async def _open_new_job(pilot, app) -> None:
    from dispatch.screens.dashboard import DashboardScreen
    from dispatch.screens.new_job import NewJobScreen

    await pilot.pause(1.2)
    if not isinstance(app.screen, NewJobScreen):
        if not isinstance(app.screen, DashboardScreen):
            await pilot.pause(0.6)
        await pilot.press("n")
        await pilot.pause(1.0)
    if not isinstance(app.screen, NewJobScreen):
        app.push_screen(NewJobScreen(LAUNCH_CWD))
        await pilot.pause(1.0)


def _neutral_email(screen) -> None:
    from textual.widgets import Input

    try:
        email = screen.query_one("#email", Input)
    except Exception:
        return
    if not email.value.strip():
        email.placeholder = "analyst@example.com"


async def _capture(name: str, setup) -> Path:
    from textual.widgets import Input, RadioButton, RadioSet

    from dispatch.app import DispatchApp
    from dispatch.screens.confirm import ConfirmScreen
    from dispatch.screens.dashboard import DashboardScreen
    from dispatch.screens.new_job import NewJobScreen

    out = FRAMES_DIR / f"{name}.svg"
    app = DispatchApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        if name == "overview":
            jobs = DATA_ROOT / ".dispatch" / "jobs"
            if jobs.exists():
                for child in jobs.iterdir():
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
            await pilot.pause(0.5)
            app.push_screen(DashboardScreen())
            await pilot.pause(1.0)
            app.save_screenshot(filename=str(out))
            return out

        await _open_new_job(pilot, app)
        await setup(pilot, app)
        if isinstance(app.screen, NewJobScreen):
            _neutral_email(app.screen)
        await pilot.pause(0.4)
        app.save_screenshot(filename=str(out))
    if not out.exists():
        raise RuntimeError(f"missing {out}")
    return out


async def _setups():
    from textual.widgets import Input, RadioButton, RadioSet, SelectionList

    from dispatch.screens.confirm import ConfirmScreen
    from dispatch.screens.new_job import NewJobScreen

    async def arrive(pilot, app):
        s = app.screen
        s.query_one("#matrix-collapsible").collapsed = False
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        await pilot.pause(0.3)

    async def matrix(pilot, app):
        s = app.screen
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#matrix-collapsible").collapsed = False
        await pilot.pause(0.2)

    async def source_sqlfile(pilot, app):
        s = app.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        await pilot.pause(0.3)
        s.query_one("#source", RadioSet).focus()

    async def queues(pilot, app):
        s = app.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        await pilot.pause(0.2)
        s.query_one("#queue", SelectionList).focus()

    async def picker(pilot, app):
        s = app.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        await pilot.pause(0.2)
        s.query_one("#sql-file-picker").focus()
        s.query_one("#row-sql-file").scroll_visible(animate=False)

    async def email_ok(pilot, app):
        s = app.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "analyst@example.com"
        s.query_one("#subject", Input).value = "Onboarding demo"
        await pilot.pause(0.3)
        s.query_one("#row-subject").scroll_visible(animate=False)

    async def monthly(pilot, app):
        s = app.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqltemplate", RadioButton).value = True
        await pilot.pause(0.5)
        s.query_one("#row-start-date").scroll_visible(animate=False)

    async def monthly_fields(pilot, app):
        s = app.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqltemplate", RadioButton).value = True
        await pilot.pause(0.5)
        s.query_one("#row-end-date").scroll_visible(animate=False)

    async def existing(pilot, app):
        s = app.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-existingtable", RadioButton).value = True
        await pilot.pause(0.4)

    async def existing_fields(pilot, app):
        s = app.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-existingtable", RadioButton).value = True
        s.query_one("#esc-aa-enc", RadioButton).value = True
        s.query_one("#existing-table", Input).value = "events_existing"
        s.query_one("#email", Input).value = "analyst@example.com"
        await pilot.pause(0.4)
        s.query_one("#row-existing-table").scroll_visible(animate=False)

    async def ready_review(pilot, app):
        s = app.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "analyst@example.com"
        s.query_one("#subject", Input).value = "Onboarding demo"
        await pilot.pause(0.4)
        s.query_one("#row-email").scroll_visible(animate=False)

    async def email_bad(pilot, app):
        s = app.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "invalido"
        await pilot.pause(0.4)
        s.query_one("#row-email").scroll_visible(animate=False)

    async def preview(pilot, app):
        s = app.screen
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "analyst@example.com"
        s.query_one("#source", RadioSet).focus()
        await pilot.press("p")
        await pilot.pause(0.6)

    async def confirm(pilot, app):
        s = app.screen
        assert isinstance(s, NewJobScreen)
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "analyst@example.com"
        s.query_one("#subject", Input).value = "Onboarding demo"
        await pilot.pause(0.3)
        sql_path = str(LAUNCH_CWD / "export_sales.sql")
        csv_path = str(LAUNCH_CWD / "analyst_dispatch_result.csv")
        summary = (
            f"Source: [cyan]SqlFile[/]  {sql_path}\n"
            f"Destination: [cyan]Csv[/]\n"
            f"Target table: [cyan]aa_enc.analyst_dispatch_result[/]\n"
            f"Queue: [cyan]Auto (cycle all queues)[/]\n"
            f"CSV path: {csv_path}\n"
            f"Email: analyst@example.com"
        )
        app.push_screen(
            ConfirmScreen(
                "Launch Job",
                summary,
                danger=True,
                confirm_label="Launch",
                cancel_label="Review",
            )
        )
        await pilot.pause(0.5)

    async def launched(pilot, app):
        s = app.screen
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "analyst@example.com"
        s.query_one("#subject", Input).value = "Onboarding demo"
        await pilot.pause(0.3)
        s.query_one("#source", RadioSet).focus()
        await pilot.click("#launch")
        await pilot.pause(0.5)
        await pilot.press("y")
        await pilot.pause(1.8)
        s.query_one("#warning-text").scroll_visible(animate=False)

    return {
        "arrive": arrive,
        "matrix": matrix,
        "source_sqlfile": source_sqlfile,
        "queues": queues,
        "picker": picker,
        "email_ok": email_ok,
        "monthly": monthly,
        "monthly_fields": monthly_fields,
        "existing": existing,
        "existing_fields": existing_fields,
        "ready_review": ready_review,
        "email_bad": email_bad,
        "preview": preview,
        "confirm": confirm,
        "launched": launched,
        "overview": arrive,
    }


def _fonts(sizes: tuple[int, int, int]):
    from PIL import ImageFont

    try:
        return (
            ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", sizes[0]),
            ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", sizes[1]),
            ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", sizes[2]),
        )
    except OSError:
        f = ImageFont.load_default()
        return f, f, f


def _svg_to_png(svg: Path, png: Path) -> None:
    import cairosvg

    cairosvg.svg2png(url=svg.as_uri(), write_to=str(png), output_width=VIDEO_W)


def _card(title: str, body: str, dest: Path) -> None:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (VIDEO_W, VIDEO_H), (16, 22, 32))
    draw = ImageDraw.Draw(img)
    bold, mid, small = _fonts((40, 26, 20))
    draw.rectangle((0, 0, 12, VIDEO_H), fill=(64, 156, 255))
    draw.text((64, 180), title, fill=(245, 245, 245), font=bold)
    y = 260
    for line in body.split("\n"):
        draw.text((64, y), line, fill=(200, 214, 230), font=mid if "•" not in line else small)
        y += 40
    img.save(dest)


def _draw_cursor(draw, x: int, y: int, *, clicking: bool = False) -> None:
    # Arrow cursor
    pts = [(x, y), (x, y + 22), (x + 6, y + 17), (x + 12, y + 28), (x + 16, y + 26), (x + 10, y + 15), (x + 18, y + 15)]
    draw.polygon(pts, fill=(255, 255, 255), outline=(20, 20, 20))
    if clicking:
        r = 18
        draw.ellipse((x - r, y - r, x + r, y + r), outline=(64, 156, 255), width=3)


def _draw_highlight(draw, cx: int, cy: int) -> None:
    # Soft focus ring around interaction point
    for i, alpha_color in enumerate([(64, 156, 255), (64, 156, 255)]):
        r = 36 + i * 10
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=alpha_color, width=2)


def _compose_ui_frame(
    ui_png: Path,
    dest: Path,
    *,
    title: str,
    body: str,
    badge: str,
    cursor: tuple[float, float],
    clicking: bool = False,
) -> None:
    from PIL import Image, ImageDraw

    ui = Image.open(ui_png).convert("RGBA")
    canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (12, 14, 18, 255))
    # Fit UI leaving room for bottom callout
    callout_h = 148
    max_h = VIDEO_H - callout_h
    ratio = min(VIDEO_W / ui.width, max_h / ui.height)
    new = ui.resize((max(1, int(ui.width * ratio)), max(1, int(ui.height * ratio))), Image.Resampling.LANCZOS)
    ox = (VIDEO_W - new.width) // 2
    oy = (max_h - new.height) // 2
    canvas.paste(new, (ox, oy), new)

    draw = ImageDraw.Draw(canvas)
    # Highlight + cursor in UI coordinates
    cx = ox + int(cursor[0] * new.width)
    cy = oy + int(cursor[1] * new.height)
    _draw_highlight(draw, cx, cy)
    _draw_cursor(draw, cx, cy, clicking=clicking)

    # Bottom callout panel
    panel = Image.new("RGBA", (VIDEO_W, callout_h), (20, 32, 48, 245))
    canvas.alpha_composite(panel, (0, VIDEO_H - callout_h))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, VIDEO_H - callout_h, 10, VIDEO_H), fill=(64, 156, 255, 255))
    bold, mid, small = _fonts((26, 20, 18))
    y0 = VIDEO_H - callout_h + 16
    draw.text((28, y0), title, fill=(245, 245, 245, 255), font=bold)
    if badge:
        bw = 16 + len(badge) * 10
        bx = VIDEO_W - bw - 28
        color = {
            "Obrigatório": (200, 70, 70),
            "Opcional": (70, 140, 90),
            "Use apenas quando...": (180, 130, 40),
        }.get(badge, (90, 90, 90))
        draw.rounded_rectangle((bx, y0, bx + bw, y0 + 28), radius=6, fill=color)
        draw.text((bx + 10, y0 + 4), badge, fill=(255, 255, 255, 255), font=small)
    y = y0 + 40
    for line in body.split("\n"):
        draw.text((28, y), line, fill=(210, 220, 235, 255), font=mid)
        y += 26

    canvas.convert("RGB").save(dest)


def _animate_step(
    base_png: Path,
    step: Step,
    out_dir: Path,
    prev_cursor: tuple[float, float] | None,
) -> list[Path]:
    """Produce PNG sequence: move → highlight/read → optional click → hold."""
    from PIL import Image

    frames: list[Path] = []
    start = prev_cursor or step.cursor
    move_frames = 18
    for i in range(move_frames):
        t = i / max(1, move_frames - 1)
        # ease-in-out
        e = 0.5 - 0.5 * math.cos(math.pi * t)
        cur = (start[0] + (step.cursor[0] - start[0]) * e, start[1] + (step.cursor[1] - start[1]) * e)
        path = out_dir / f"{step.id}_m{i:02d}.png"
        # During move, show title only lightly
        _compose_ui_frame(
            base_png,
            path,
            title=step.title,
            body=step.body.split("\n")[0],
            badge=step.badge,
            cursor=cur,
            clicking=False,
        )
        frames.append(path)

    # Click pulse
    if step.click:
        for i in range(6):
            path = out_dir / f"{step.id}_c{i:02d}.png"
            _compose_ui_frame(
                base_png,
                path,
                title=step.title,
                body=step.body,
                badge=step.badge,
                cursor=step.cursor,
                clicking=True,
            )
            frames.append(path)

    # Hold for reading
    hold_n = max(1, int(step.hold * FPS))
    hold_png = out_dir / f"{step.id}_hold.png"
    _compose_ui_frame(
        base_png,
        hold_png,
        title=step.title,
        body=step.body,
        badge=step.badge,
        cursor=step.cursor,
        clicking=False,
    )
    for i in range(hold_n):
        # reuse same file path entries (ffmpeg concat by repeating)
        frames.append(hold_png)
    return frames


def _fmt_ts(seconds: float) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, milli = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def _write_srt(timings: list[tuple[Step, float, float]]) -> None:
    blocks = []
    idx = 1
    for step, start, dur in timings:
        text = f"{step.title}\n{step.body}"
        if step.badge:
            text = f"[{step.badge}] {step.title}\n{step.body}"
        # chunk long bodies into readable cues
        lines = text.split("\n")
        chunks = []
        cur: list[str] = []
        for line in lines:
            cur.append(line)
            if len(cur) >= 2:
                chunks.append("\n".join(cur))
                cur = []
        if cur:
            chunks.append("\n".join(cur))
        slice_dur = dur / len(chunks)
        for i, chunk in enumerate(chunks):
            a = start + i * slice_dur
            b = start + dur if i == len(chunks) - 1 else start + (i + 1) * slice_dur
            blocks.append(f"{idx}\n{_fmt_ts(a)} --> {_fmt_ts(b)}\n{chunk}\n")
            idx += 1
    CAPTIONS_OUT.write_text("\n".join(blocks), encoding="utf-8")


def _write_storyboard(timings: list[tuple[Step, float, float]]) -> None:
    lines = [
        "# Storyboard — New Job (silencioso, pt-BR)",
        "",
        "Vídeo sem narração e sem música. Explicações on-screen + cursor/cliques.",
        "",
    ]
    for step, start, dur in timings:
        lines += [
            f"## {step.id} — {step.section or step.title}",
            "",
            f"- **Tempo:** {_fmt_ts(start)} → {_fmt_ts(start + dur)} ({dur:.1f}s)",
            f"- **Tela:** `{step.capture}`",
            f"- **Destaque / cursor:** {step.cursor}{' + clique' if step.click else ''}",
            f"- **Badge:** {step.badge or '—'}",
            f"- **Texto na tela:** {step.title} — {step.body.replace(chr(10), ' / ')}",
            f"- **Resultado esperado:** analista entende o uso prático de “{step.title}”",
            "",
        ]
    STORYBOARD_OUT.write_text("\n".join(lines), encoding="utf-8")


def _build_silent_mp4(frame_paths: list[Path], duration_hint: float) -> None:
    """Encode PNG sequence to MP4 with silent audio track."""
    n = len(frame_paths)
    seq_dir = CLIPS_DIR / "seq"
    if seq_dir.exists():
        shutil.rmtree(seq_dir)
    seq_dir.mkdir(parents=True)
    for i, src in enumerate(frame_paths):
        shutil.copy2(src, seq_dir / f"f{i:05d}.png")

    silent = CLIPS_DIR / "silent.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(seq_dir / "f%05d.png"),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=mono:sample_rate=44100",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "64k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(silent),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    shutil.copy2(silent, VIDEO_OUT)
    print(f"frames={n} duration_hint={duration_hint:.1f}s -> {VIDEO_OUT}")


def _make_zip() -> None:
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(VIDEO_OUT, arcname=VIDEO_OUT.name)
    # validate
    with zipfile.ZipFile(ZIP_OUT, "r") as zf:
        bad = zf.testzip()
        names = zf.namelist()
    if bad:
        raise RuntimeError(f"zip corrupt: {bad}")
    if names != [VIDEO_OUT.name]:
        raise RuntimeError(f"zip contents unexpected: {names}")
    print(f"zip ok: {ZIP_OUT} ({ZIP_OUT.stat().st_size} bytes) names={names}")


def _verify_captures() -> None:
    sys.path.insert(0, str(REPO_ROOT / "tools" / "dev"))
    from svg_text import svg_to_text

    checks = {
        "arrive": (["New Job", "Source", "Destination"], ["mastercard.com"]),
        "matrix": (["SOURCE", "SqlFile", "MonthlyJob"], ["mastercard.com"]),
        "source_sqlfile": (["SqlFile", "Csv"], ["mastercard.com"]),
        "queues": (["Execution Queue"], ["mastercard.com"]),
        "picker": (["export_sales.sql", "SQL File"], ["mastercard.com"]),
        "email_ok": (["analyst@example.com", "Onboarding demo"], ["mastercard.com"]),
        "monthly": (["MonthlyJob", "MonthlyJob supports Table only"], ["mastercard.com"]),
        "monthly_fields": (["Start Date", "End Date", "Schema"], ["mastercard.com"]),
        "existing": (["ExistingTable supports Csv only"], ["mastercard.com"]),
        "existing_fields": (["events_existing"], ["mastercard.com"]),
        "email_bad": (["Invalid email format", "invalido"], ["mastercard.com"]),
        "ready_review": (["Ready to launch", "analyst@example.com"], ["Invalid email", "mastercard.com"]),
        "preview": (["SQL Preview", "SELECT"], ["mastercard.com"]),
        "confirm": (["Launch Job", "Destination: Csv"], ["mastercard.com"]),
        "launched": (["Launched Job"], ["mastercard.com"]),
        "overview": (["Overview", "Jobs"], ["mastercard.com", "SUCCEEDED"]),
    }
    for key, (need, forbid) in checks.items():
        text = svg_to_text((FRAMES_DIR / f"{key}.svg").read_text(encoding="utf-8"))
        for n in need:
            if n not in text:
                raise AssertionError(f"{key}: missing {n!r}")
        for f in forbid:
            if f in text:
                raise AssertionError(f"{key}: unexpected {f!r}")


async def main() -> int:
    _require_tools()
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    anim_dir = FRAMES_DIR / "anim"
    if anim_dir.exists():
        shutil.rmtree(anim_dir)
    anim_dir.mkdir(parents=True)

    # Remove obsolete narration deliverable
    if NARRATION_LEGACY.exists():
        NARRATION_LEGACY.unlink()

    print("Bootstrapping…")
    _bootstrap()
    setups = await _setups()
    capture_keys = [
        "arrive",
        "matrix",
        "source_sqlfile",
        "queues",
        "picker",
        "email_ok",
        "monthly",
        "monthly_fields",
        "existing",
        "existing_fields",
        "ready_review",
        "email_bad",
        "preview",
        "confirm",
        "launched",
        "overview",
    ]
    print("Capturing real New Job UI…")
    for key in capture_keys:
        print(f"  {key}")
        await _capture(key, setups[key])
    _verify_captures()
    print("Capture assertions OK")

    # Prepare base PNGs / cards
    base_pngs: dict[str, Path] = {}
    for key in capture_keys:
        png = FRAMES_DIR / f"{key}.png"
        _svg_to_png(FRAMES_DIR / f"{key}.svg", png)
        base_pngs[key] = png
    _card(
        "Dispatch (Robocop)",
        "Como utilizar a aba New Job\nConfigure e inicie um novo job passo a passo.",
        FRAMES_DIR / "card_open.png",
    )
    base_pngs["card:open"] = FRAMES_DIR / "card_open.png"
    _card(
        "Antes de começar",
        "Tenha pronto:\n• o arquivo SQL do seu job (SqlFile ou MonthlyJob);\n"
        "• a origem e o destino desejados;\n• e-mail de notificação, se quiser receber aviso.",
        FRAMES_DIR / "card_ready.png",
    )
    base_pngs["card:ready"] = FRAMES_DIR / "card_ready.png"
    _card(
        "Antes de iniciar, confirme:",
        "• origem e destino;\n• arquivo selecionado;\n• fila de execução;\n"
        "• opções adicionais;\n• e-mail de notificação.",
        FRAMES_DIR / "card_checklist.png",
    )
    base_pngs["card:checklist"] = FRAMES_DIR / "card_checklist.png"
    _card(
        "Resumo",
        "Na aba New Job, você:\n1. define a execução;\n2. revisa as configurações;\n"
        "3. inicia o job;\n4. acompanha o resultado no Overview.\n\n"
        "Em caso de dúvida, revise os campos antes de selecionar Launch Job.",
        FRAMES_DIR / "card_close.png",
    )
    base_pngs["card:close"] = FRAMES_DIR / "card_close.png"

    print("Composing silent visual frames…")
    all_frames: list[Path] = []
    timings: list[tuple[Step, float, float]] = []
    cursor = 0.0
    prev_cursor: tuple[float, float] | None = None
    for step in STEPS:
        if step.capture.startswith("card:"):
            # treat card as static with cursor hold (still show callout style via card itself)
            hold_n = max(1, int(step.hold * FPS))
            card = base_pngs[step.capture]
            for _ in range(hold_n):
                all_frames.append(card)
            timings.append((step, cursor, step.hold))
            cursor += step.hold
            prev_cursor = step.cursor
            print(f"  {step.id}: card {step.hold:.1f}s")
            continue

        seq = _animate_step(base_pngs[step.capture], step, anim_dir, prev_cursor)
        # duration = move(~0.6s) + click(~0.2s) + hold
        move_s = 18 / FPS
        click_s = (6 / FPS) if step.click else 0.0
        dur = move_s + click_s + step.hold
        all_frames.extend(seq)
        timings.append((step, cursor, dur))
        cursor += dur
        prev_cursor = step.cursor
        print(f"  {step.id}: {dur:.1f}s ({len(seq)} frames)")

    _write_srt(timings)
    _write_storyboard(timings)
    print("Encoding silent MP4…")
    _build_silent_mp4(all_frames, cursor)
    _make_zip()

    # Validate
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,format_name",
            "-show_entries",
            "stream=codec_type,codec_name,width,height",
            "-of",
            "json",
            str(VIDEO_OUT),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    print(probe.stdout)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(VIDEO_OUT), "-f", "null", "-"],
        check=True,
    )
    print("DECODE_OK")

    # Ensure no narration file remains
    assert not NARRATION_LEGACY.exists(), "narration file should be removed"
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
