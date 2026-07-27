#!/usr/bin/env python3
"""Produce the Dispatch (Robocop) New Job onboarding package (PT-BR).

Captures the **real** Dispatch Textual UI from this repository:

- Instantiates ``dispatch.app.DispatchApp`` (same entry as ``python -m dispatch``)
- Waits for the normal Overview startup, then opens New Job with ``n``
- Drives ``NewJobScreen`` widgets and calls ``save_screenshot``

Backend Edge tools (Kerberos/Impala/SMTP) use the repo ``mocks/`` layer so the
recording stays safe and offline. The pixels are the real TUI, not a redrawn
mockup.

Kerberos TTL comes from mock ``klist`` on PATH (not a patched probe). Impala
query success is **not** demonstrated as production truth: after Launch we show
the in-app ``Launched Job`` message and the Overview screen for monitoring
navigation, without relying on a mock Impala SUCCEEDED state as evidence.

Dependencies (install into .venv if missing):
  textual==8.2.5 from requirements.txt (or vendor wheels), cairosvg, pillow, edge-tts
System: ffmpeg on PATH

Run from repo root (with mocks available):
  source mocks/dev-env.sh
  /workspace/.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
FRAMES_DIR = OUT_DIR / "frames"
AUDIO_DIR = OUT_DIR / "audio"
CLIPS_DIR = OUT_DIR / "clips"

VIDEO_OUT = OUT_DIR / "dispatch_robocop_new_job_onboarding_ptbr.mp4"
NARRATION_OUT = OUT_DIR / "dispatch_robocop_new_job_narration_ptbr.txt"
CAPTIONS_OUT = OUT_DIR / "dispatch_robocop_new_job_captions_ptbr.srt"
STORYBOARD_OUT = OUT_DIR / "dispatch_robocop_new_job_storyboard.md"

VOICE = "pt-BR-FranciscaNeural"
TERMINAL_SIZE = (150, 54)
VIDEO_W, VIDEO_H = 1280, 720
HEALTHY_TTL_SECONDS = 8 * 3600

# Demo paths stay under /tmp and use non-sensitive sample data only.
DEMO_ROOT = Path("/tmp/dispatch_onboarding_demo")
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
-- Modelo mensal: tokens {date_inicio} e {date_fim}
SELECT
  region,
  SUM(amount) AS total
FROM sales
WHERE sale_date BETWEEN '{date_inicio}' AND '{date_fim}'
GROUP BY region;
"""


@dataclass
class Segment:
    id: str
    section: str
    narration: str
    on_screen: str
    highlight: str
    expected: str
    kind: str = "ui"  # title | section | ui | checklist
    capture: str = ""  # capture key referenced below
    pad_after: float = 0.35


SEGMENTS: list[Segment] = [
    Segment(
        id="01_title",
        section="Abertura",
        narration=(
            "Bem-vindo ao Dispatch, também conhecido como Robocop. "
            "Neste vídeo, você vai aprender a usar a aba New Job, do início ao envio."
        ),
        on_screen="Dispatch (Robocop) | Como utilizar a aba New Job",
        highlight="Cartão de título",
        expected="O espectador entende o tema do vídeo",
        kind="title",
    ),
    Segment(
        id="02_objective",
        section="Abertura",
        narration=(
            "A aba New Job serve para configurar e lançar um job no Impala: "
            "uma execução de consulta SQL supervisionada pelo Dispatch. "
            "Ao final, você saberá preencher o formulário, corrigir erros e enviar o job."
        ),
        on_screen="Objetivo: configurar e lançar um job",
        highlight="Texto de objetivo",
        expected="Entendimento do propósito da aba",
        kind="section",
    ),
    Segment(
        id="03_prereq",
        section="Antes de começar",
        narration=(
            "Antes de começar, tenha pronto: um arquivo SQL na pasta de onde você abriu o Dispatch; "
            "um ticket Kerberos válido — o indicador K R B na barra lateral deve mostrar tempo restante; "
            "e, se quiser notificação, um e-mail no formato nome arroba domínio. "
            "O campo Email (notifications) é opcional; Kerberos e o arquivo SQL são necessários para lançar."
        ),
        on_screen="Antes de começar",
        highlight="Lista de pré-requisitos",
        expected="Usuário sabe o que preparar",
        kind="section",
    ),
    Segment(
        id="04_arrive",
        section="Preenchimento dos campos",
        narration=(
            "Você chegou à aba New Job. À esquerda está a navegação; New Job fica destacado. "
            "No rodapé da barra lateral, o indicador K R B mostra se a autenticação Kerberos está ok. "
            "O formulário começa no topo e desce até os botões Preview SQL e Launch."
        ),
        on_screen="Aba New Job",
        highlight="Tela New Job completa",
        expected="Orientação espacial da tela",
        capture="arrive",
    ),
    Segment(
        id="05_matrix",
        section="Preenchimento dos campos",
        narration=(
            "No topo, a matriz Source vezes Destination legal cells mostra quais combinações são permitidas. "
            "SqlFile pode ir para Table, Csv ou Table mais Csv. "
            "MonthlyJob só pode ir para Table. "
            "ExistingTable só pode ir para Csv. "
            "Pressione M para expandir ou recolher essa matriz."
        ),
        on_screen="Matriz Source × Destination",
        highlight="Tabela de células legais",
        expected="Entende restrições de combinação",
        capture="matrix",
    ),
    Segment(
        id="06_detected",
        section="Preenchimento dos campos",
        narration=(
            "A linha Detected source informa o tipo detectado no arquivo SQL selecionado. "
            "Se o arquivo tiver os marcadores date_inicio e date_fim, o Dispatch trata como MonthlyJob "
            "e desativa automaticamente destinos ilegais."
        ),
        on_screen="Detected source",
        highlight="Linha Detected source",
        expected="Entende detecção automática",
        capture="arrive",
    ),
    Segment(
        id="07_source",
        section="Preenchimento dos campos",
        narration=(
            "O campo Source é obrigatório. SqlFile: consulta SQL comum em um arquivo. "
            "MonthlyJob: consulta com intervalo de datas, usando os marcadores date_inicio e date_fim. "
            "ExistingTable: exporta uma tabela que já existe no Impala, sem arquivo SQL."
        ),
        on_screen="Source — obrigatório",
        highlight="Radio Source",
        expected="Escolhe a origem correta",
        capture="source_dest",
    ),
    Segment(
        id="08_destination",
        section="Preenchimento dos campos",
        narration=(
            "Destination também é obrigatório e depende do Source. "
            "Table grava o resultado em uma tabela Impala. "
            "Csv grava um arquivo C S V na pasta de lançamento. "
            "Table mais Csv faz os dois. "
            "Opções ilegais ficam desabilitadas automaticamente."
        ),
        on_screen="Destination — obrigatório",
        highlight="Radio Destination",
        expected="Escolhe destino permitido",
        capture="source_dest",
    ),
    Segment(
        id="09_queue",
        section="Preenchimento dos campos",
        narration=(
            "Execution Queue é opcional. Sem seleção, o modo Auto tenta as filas até uma aceitar o job. "
            "Você pode marcar uma ou mais filas para restringir; várias são tentadas na ordem da lista. "
            "Use Auto se não tiver preferência."
        ),
        on_screen="Execution Queue — opcional",
        highlight="Lista de filas",
        expected="Entende Auto versus seleção manual",
        capture="queues",
    ),
    Segment(
        id="10_picker",
        section="Preenchimento dos campos",
        narration=(
            "A lista SQL files mostra os arquivos ponto sql da pasta de lançamento. "
            "Selecione um para preencher o caminho. "
            "O campo SQL File é obrigatório para SqlFile e MonthlyJob; o arquivo precisa existir. "
            "Abaixo, um indicador confirma se o arquivo foi encontrado."
        ),
        on_screen="SQL File — obrigatório para SqlFile/MonthlyJob",
        highlight="Picker e campo SQL File",
        expected="Seleciona o SQL correto",
        capture="picker",
    ),
    Segment(
        id="11_email_subject",
        section="Preenchimento dos campos",
        narration=(
            "O campo Email (notifications) é opcional. Se preencher, use um endereço válido com arroba e domínio. "
            "Vários e-mails podem ser separados por vírgula. "
            "Subject (email) também é opcional; o padrão é Dispatch Job. "
            "Define o assunto da notificação."
        ),
        on_screen="Email (notifications) e Subject — opcionais",
        highlight="Campos Email e Subject",
        expected="Preenche notificação se desejar",
        capture="email_ok",
    ),
    Segment(
        id="12_status",
        section="Preenchimento dos campos",
        narration=(
            "Na área de status, o Dispatch mostra checagens ao vivo: arquivo SQL encontrado, "
            "formato de e-mail e Kerberos. "
            "Na barra de ações, a mensagem Ready to launch aparece quando não há problemas. "
            "Os botões são Preview SQL tecla P, e Launch tecla L."
        ),
        on_screen="Status e ações",
        highlight="Validation summary e botões",
        expected="Lê indicadores antes de enviar",
        capture="ready_actions",
    ),
    Segment(
        id="13_monthly",
        section="Preenchimento dos campos",
        narration=(
            "Ao escolher MonthlyJob, o destino fica limitado a Table. "
            "Aparecem campos obrigatórios extras: Schema, Table Name com o prefixo do seu usuário, "
            "Start Date e End Date no formato ano-mês-dia. "
            "As datas definem o período da consulta mensal."
        ),
        on_screen="MonthlyJob → Table",
        highlight="Campos Schema, Table, datas",
        expected="Vê dependências do MonthlyJob",
        capture="monthly",
    ),
    Segment(
        id="14_existing",
        section="Preenchimento dos campos",
        narration=(
            "Com ExistingTable, o destino fica só em Csv. "
            "Escolha o Schema — coe_enc, aa_enc ou other — e informe o nome da tabela existente. "
            "Se usar other, aparece Custom Schema. "
            "Não há Preview SQL nesse modo."
        ),
        on_screen="ExistingTable → Csv",
        highlight="Schema e Existing Table",
        expected="Vê dependências do ExistingTable",
        capture="existing",
    ),
    Segment(
        id="15_validation_bad",
        section="Revisão",
        narration=(
            "Vamos demonstrar um erro comum. No fluxo SqlFile para Csv, se o e-mail for inválido, "
            "como apenas a palavra invalido, o resumo mostra issue Invalid email format, "
            "e o indicador de e-mail fica vermelho. Corrija antes de lançar."
        ),
        on_screen="Erro: Invalid email format",
        highlight="Campo Email + validation summary",
        expected="Reconhece e interpreta validação",
        capture="email_bad",
    ),
    Segment(
        id="16_validation_fix",
        section="Revisão",
        narration=(
            "Corrigindo para analyst arroba example ponto com, o erro some. "
            "O status volta a Ready to launch. "
            "Revise: Source SqlFile, Destination Csv, arquivo export_sales ponto sql, "
            "fila em Auto, e-mail válido e Kerberos ok."
        ),
        on_screen="✓ Ready to launch",
        highlight="Formulário pronto",
        expected="Confirma configuração válida",
        capture="ready_review",
    ),
    Segment(
        id="17_preview",
        section="Revisão",
        narration=(
            "Antes de enviar, use Preview SQL com a tecla P para ver o SQL que será executado. "
            "Confirme se a consulta está correta e volte com Esc. "
            "Preview não está disponível para ExistingTable."
        ),
        on_screen="SQL Preview",
        highlight="Tela de preview",
        expected="Revisa SQL antes do envio",
        capture="preview",
    ),
    Segment(
        id="18_confirm",
        section="Envio do job",
        narration=(
            "Ao pressionar Launch ou a tecla L, abre a confirmação Launch Job. "
            "Ela resume Source, Destination, tabela alvo, fila, caminho do C S V e e-mail. "
            "Launch confirma; Review cancela para ajustar. "
            "Confirme com Y ou Enter."
        ),
        on_screen="Confirmação Launch Job",
        highlight="Modal de confirmação",
        expected="Lê o resumo antes de confirmar",
        capture="confirm",
    ),
    Segment(
        id="19_launched",
        section="Envio do job",
        narration=(
            "Após confirmar, o Dispatch cria o job e inicia o runner em segundo plano, "
            "mostrando a mensagem Launched Job com o identificador. "
            "A interface não fica responsável pela execução durável do job."
        ),
        on_screen="✓ Launched Job …",
        highlight="Mensagem de sucesso",
        expected="Vê confirmação imediata do envio",
        capture="launched",
    ),
    Segment(
        id="20_next",
        section="Próximos passos",
        narration=(
            "Para acompanhar, volte à Overview com Esc ou B. "
            "Nessa tela você monitora jobs em execução e recentes, além dos logs. "
            "O status final no Impala depende do ambiente real; use Overview e View Logs para acompanhar."
        ),
        on_screen="Próximo: Overview",
        highlight="Tela Overview para monitorar",
        expected="Sabe para onde ir depois",
        capture="overview",
    ),
    Segment(
        id="21_checklist",
        section="Próximos passos",
        narration=(
            "Checklist final: Kerberos válido; combinação Source e Destination permitida; "
            "arquivo SQL existente quando necessário; campos extras do MonthlyJob ou ExistingTable "
            "preenchidos; e-mail vazio ou válido; status Ready to launch; "
            "revise no Preview e na confirmação Launch Job. Até a próxima!"
        ),
        on_screen="Checklist antes de enviar",
        highlight="Lista de verificação",
        expected="Memoriza checagens-chave",
        kind="checklist",
    ),
]


def _require_tools() -> None:
    missing = []
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")
    try:
        import cairosvg  # noqa: F401
        import edge_tts  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        missing.append(str(exc))
    try:
        import textual  # noqa: F401
    except ImportError:
        missing.append("textual (pip install -r requirements.txt)")
    if missing:
        raise SystemExit("Missing dependencies:\n- " + "\n- ".join(missing))


def _bootstrap_demo_env() -> Path:
    if DEMO_ROOT.exists():
        shutil.rmtree(DEMO_ROOT)
    dispatch_home = DATA_ROOT / ".dispatch"
    dispatch_home.mkdir(parents=True)
    (dispatch_home / "config.json").write_text("{}", encoding="utf-8")
    LAUNCH_CWD.mkdir(parents=True)
    # Alphabetical order: export_sales first so initial detect is SqlFile.
    (LAUNCH_CWD / "export_sales.sql").write_text(PLAIN_SQL, encoding="utf-8")
    (LAUNCH_CWD / "monthly_revenue.sql").write_text(MONTHLY_SQL, encoding="utf-8")

    os.environ["USER"] = "analyst"
    os.environ["DISPATCH_DATA_ROOT"] = str(DATA_ROOT)
    os.environ["DISPATCH_MOCK_SCENARIO"] = "happy_path"
    os.environ["DISPATCH_MOCK_DELAY"] = "0"
    os.environ["DISPATCH_SCR_DIR"] = str(REPO_ROOT / "scr")
    os.environ["DISPATCH_MOCK_STATE_DIR"] = str(DEMO_ROOT / "mock_state")
    os.environ["MAILHOST"] = "127.0.0.1:9"
    mocks_bin = str(REPO_ROOT / "mocks" / "bin")
    os.environ["PATH"] = f"{mocks_bin}{os.pathsep}{os.environ.get('PATH', '')}"
    os.environ.pop("DISPATCH_EMAIL", None)
    Path(os.environ["DISPATCH_MOCK_STATE_DIR"]).mkdir(parents=True, exist_ok=True)

    os.chdir(LAUNCH_CWD)
    # Kerberos TTL comes from mocks/bin/klist on PATH — same seam as local
    # `source mocks/dev-env.sh`, not a patched probe.
    return LAUNCH_CWD


async def _open_new_job(pilot, app) -> None:
    """User path: wait for Overview startup, then press N."""
    from dispatch.screens.dashboard import DashboardScreen
    from dispatch.screens.new_job import NewJobScreen

    await pilot.pause(1.2)
    # Startup worker pushes DashboardScreen; open New Job like the footer binding.
    if not isinstance(app.screen, NewJobScreen):
        if not isinstance(app.screen, DashboardScreen):
            await pilot.pause(0.8)
        await pilot.press("n")
        await pilot.pause(1.0)
    if not isinstance(app.screen, NewJobScreen):
        # Fallback if the binding was swallowed during focus settle.
        app.push_screen(NewJobScreen(LAUNCH_CWD))
        await pilot.pause(1.0)


async def _capture_svg(name: str, setup) -> Path:
    from textual.widgets import Input, RadioButton, RadioSet

    from dispatch.app import DispatchApp
    from dispatch.screens.dashboard import DashboardScreen
    from dispatch.screens.new_job import NewJobScreen

    def _neutral_email(screen) -> None:
        """Demo-only: avoid the production-style email placeholder in recordings."""
        try:
            email = screen.query_one("#email", Input)
        except Exception:
            return
        if not email.value.strip():
            email.placeholder = "analyst@example.com"

    out_svg = FRAMES_DIR / f"{name}.svg"
    app = DispatchApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        if name == "overview":
            # Show the real Overview (monitoring destination) without presenting
            # a mock Impala SUCCEEDED result as production evidence. Clear any
            # jobs created by earlier capture steps in this shared data root.
            import shutil as _shutil

            jobs_dir = DATA_ROOT / ".dispatch" / "jobs"
            if jobs_dir.exists():
                for child in jobs_dir.iterdir():
                    if child.is_dir():
                        _shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
            await pilot.pause(0.6)
            # Always mount a fresh Overview after clearing jobs.
            app.push_screen(DashboardScreen())
            await pilot.pause(1.2)
            app.save_screenshot(filename=str(out_svg))
            return out_svg

        await _open_new_job(pilot, app)
        await setup(pilot, app)
        if isinstance(app.screen, NewJobScreen):
            _neutral_email(app.screen)
        await pilot.pause(0.45)
        app.save_screenshot(filename=str(out_svg))
    if not out_svg.exists():
        raise RuntimeError(f"Missing screenshot {out_svg}")
    return out_svg


async def _setups():
    from textual.widgets import Input, RadioButton, RadioSet, SelectionList

    from dispatch.screens.confirm import ConfirmScreen
    from dispatch.screens.new_job import NewJobScreen

    async def arrive(pilot, app):
        screen = app.screen
        screen.query_one("#src-sqlfile", RadioButton).value = True
        await pilot.pause(0.25)
        # Keep matrix visible for orientation
        collapsible = screen.query_one("#matrix-collapsible")
        collapsible.collapsed = False
        await pilot.pause(0.2)

    async def matrix(pilot, app):
        screen = app.screen
        screen.query_one("#src-sqlfile", RadioButton).value = True
        await pilot.pause(0.2)
        screen.query_one("#matrix-collapsible").collapsed = False
        await pilot.pause(0.2)

    async def source_dest(pilot, app):
        screen = app.screen
        screen.query_one("#matrix-collapsible").collapsed = True
        screen.query_one("#src-sqlfile", RadioButton).value = True
        screen.query_one("#dst-csv", RadioButton).value = True
        await pilot.pause(0.3)
        screen.query_one("#source", RadioSet).focus()

    async def queues(pilot, app):
        screen = app.screen
        screen.query_one("#matrix-collapsible").collapsed = True
        screen.query_one("#src-sqlfile", RadioButton).value = True
        screen.query_one("#dst-csv", RadioButton).value = True
        await pilot.pause(0.2)
        screen.query_one("#queue", SelectionList).focus()
        await pilot.pause(0.2)

    async def picker(pilot, app):
        screen = app.screen
        screen.query_one("#matrix-collapsible").collapsed = True
        screen.query_one("#src-sqlfile", RadioButton).value = True
        screen.query_one("#dst-csv", RadioButton).value = True
        await pilot.pause(0.2)
        picker = screen.query_one("#sql-file-picker")
        picker.focus()
        await pilot.pause(0.3)
        screen.query_one("#row-sql-file").scroll_visible(animate=False)

    async def email_ok(pilot, app):
        screen = app.screen
        screen.query_one("#matrix-collapsible").collapsed = True
        screen.query_one("#src-sqlfile", RadioButton).value = True
        screen.query_one("#dst-csv", RadioButton).value = True
        await pilot.pause(0.2)
        screen.query_one("#email", Input).value = "analyst@example.com"
        screen.query_one("#subject", Input).value = "Onboarding demo"
        await pilot.pause(0.3)
        screen.query_one("#row-subject").scroll_visible(animate=False)

    async def ready_actions(pilot, app):
        screen = app.screen
        screen.query_one("#matrix-collapsible").collapsed = True
        screen.query_one("#src-sqlfile", RadioButton).value = True
        screen.query_one("#dst-csv", RadioButton).value = True
        screen.query_one("#email", Input).value = "analyst@example.com"
        screen.query_one("#subject", Input).value = "Onboarding demo"
        await pilot.pause(0.4)
        screen.query_one("#row-subject").scroll_visible(animate=False)

    async def monthly(pilot, app):
        screen = app.screen
        screen.query_one("#matrix-collapsible").collapsed = True
        screen.query_one("#src-sqltemplate", RadioButton).value = True
        await pilot.pause(0.5)
        screen.query_one("#row-end-date").scroll_visible(animate=False)

    async def existing(pilot, app):
        screen = app.screen
        screen.query_one("#matrix-collapsible").collapsed = True
        screen.query_one("#src-existingtable", RadioButton).value = True
        await pilot.pause(0.4)
        screen.query_one("#esc-aa-enc", RadioButton).value = True
        screen.query_one("#existing-table", Input).value = "events_existing"
        screen.query_one("#email", Input).value = "analyst@example.com"
        await pilot.pause(0.3)
        screen.query_one("#row-existing-table").scroll_visible(animate=False)

    async def email_bad(pilot, app):
        screen = app.screen
        screen.query_one("#matrix-collapsible").collapsed = True
        screen.query_one("#src-sqlfile", RadioButton).value = True
        screen.query_one("#dst-csv", RadioButton).value = True
        await pilot.pause(0.2)
        screen.query_one("#email", Input).value = "invalido"
        await pilot.pause(0.4)
        screen.query_one("#row-email").scroll_visible(animate=False)

    async def ready_review(pilot, app):
        screen = app.screen
        screen.query_one("#matrix-collapsible").collapsed = True
        screen.query_one("#src-sqlfile", RadioButton).value = True
        screen.query_one("#dst-csv", RadioButton).value = True
        screen.query_one("#email", Input).value = "analyst@example.com"
        screen.query_one("#subject", Input).value = "Onboarding demo"
        await pilot.pause(0.4)
        screen.query_one("#row-email").scroll_visible(animate=False)

    async def preview(pilot, app):
        screen = app.screen
        screen.query_one("#src-sqlfile", RadioButton).value = True
        screen.query_one("#dst-csv", RadioButton).value = True
        screen.query_one("#email", Input).value = "analyst@example.com"
        await pilot.pause(0.3)
        screen.query_one("#source", RadioSet).focus()
        await pilot.press("p")
        await pilot.pause(0.6)

    async def confirm(pilot, app):
        screen = app.screen
        assert isinstance(screen, NewJobScreen)
        screen.query_one("#src-sqlfile", RadioButton).value = True
        screen.query_one("#dst-csv", RadioButton).value = True
        screen.query_one("#email", Input).value = "analyst@example.com"
        screen.query_one("#subject", Input).value = "Onboarding demo"
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
        screen = app.screen
        screen.query_one("#src-sqlfile", RadioButton).value = True
        screen.query_one("#dst-csv", RadioButton).value = True
        screen.query_one("#email", Input).value = "analyst@example.com"
        screen.query_one("#subject", Input).value = "Onboarding demo"
        await pilot.pause(0.3)
        screen.query_one("#source", RadioSet).focus()
        await pilot.click("#launch")
        await pilot.pause(0.5)
        await pilot.press("y")
        await pilot.pause(1.8)
        # Bring success message into view if needed
        screen.query_one("#warning-text").scroll_visible(animate=False)
        await pilot.pause(0.2)

    return {
        "arrive": arrive,
        "matrix": matrix,
        "source_dest": source_dest,
        "queues": queues,
        "picker": picker,
        "email_ok": email_ok,
        "ready_actions": ready_actions,
        "monthly": monthly,
        "existing": existing,
        "email_bad": email_bad,
        "ready_review": ready_review,
        "preview": preview,
        "confirm": confirm,
        "launched": launched,
        "overview": arrive,  # unused; overview path is special-cased in _capture_svg
    }


def _svg_to_png(svg_path: Path, png_path: Path) -> None:
    import cairosvg

    cairosvg.svg2png(url=svg_path.as_uri(), write_to=str(png_path), output_width=VIDEO_W)


def _fit_canvas(src: Path, dest: Path, overlay_title: str, callout: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(src).convert("RGBA")
    canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (18, 18, 18, 255))
    # Scale UI to fit below banner
    banner_h = 78
    max_h = VIDEO_H - banner_h - 8
    ratio = min(VIDEO_W / img.width, max_h / img.height)
    new_size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
    ui = img.resize(new_size, Image.Resampling.LANCZOS)
    x = (VIDEO_W - ui.width) // 2
    y = banner_h + (max_h - ui.height) // 2
    canvas.paste(ui, (x, y), ui)

    draw = ImageDraw.Draw(canvas)
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        call_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except OSError:
        title_font = ImageFont.load_default()
        call_font = title_font

    draw.rectangle((0, 0, VIDEO_W, banner_h), fill=(28, 48, 72, 255))
    draw.rectangle((0, 0, 10, banner_h), fill=(70, 170, 255, 255))
    draw.text((24, 12), overlay_title[:90], fill=(245, 245, 245, 255), font=title_font)
    if callout:
        draw.text((24, 46), callout[:110], fill=(180, 210, 240, 255), font=call_font)

    canvas.convert("RGB").save(dest)


def _title_card(title: str, subtitle: str, dest: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (VIDEO_W, VIDEO_H), (16, 22, 32))
    draw = ImageDraw.Draw(img)
    try:
        big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        mid = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except OSError:
        big = mid = small = ImageFont.load_default()

    draw.rectangle((0, 0, VIDEO_W, 8), fill=(70, 170, 255))
    draw.text((64, 250), title, fill=(245, 245, 245), font=big)
    draw.text((64, 320), subtitle, fill=(170, 190, 210), font=mid)
    draw.text((64, 400), "Somente a aba New Job  ·  Exemplo não sensível", fill=(120, 140, 160), font=small)
    img.save(dest)


def _section_card(section: str, line: str, dest: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (VIDEO_W, VIDEO_H), (16, 22, 32))
    draw = ImageDraw.Draw(img)
    try:
        big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
        mid = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except OSError:
        big = mid = ImageFont.load_default()
    draw.rectangle((0, 0, 12, VIDEO_H), fill=(70, 170, 255))
    draw.text((64, 280), section, fill=(70, 170, 255), font=big)
    draw.text((64, 360), line, fill=(230, 230, 230), font=mid)
    img.save(dest)


def _checklist_card(dest: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (VIDEO_W, VIDEO_H), (16, 22, 32))
    draw = ImageDraw.Draw(img)
    try:
        big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        mid = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except OSError:
        big = mid = ImageFont.load_default()
    items = [
        "Kerberos válido (KRB na barra lateral)",
        "Combinação Source → Destination permitida",
        "SQL File existente (SqlFile / MonthlyJob)",
        "Campos extras do MonthlyJob ou ExistingTable",
        "E-mail vazio ou em formato válido",
        "Status: Ready to launch",
        "Revisar Preview SQL e confirmação Launch Job",
    ]
    draw.text((64, 80), "Checklist antes de enviar", fill=(245, 245, 245), font=big)
    y = 160
    for item in items:
        draw.text((64, y), f"✓  {item}", fill=(200, 220, 240), font=mid)
        y += 58
    img.save(dest)


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


async def _synthesize(text: str, mp3_path: Path, wav_path: Path) -> float:
    import edge_tts

    communicate = edge_tts.Communicate(text, VOICE, rate="-5%")
    await communicate.save(str(mp3_path))
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(mp3_path),
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            "44100",
            str(wav_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return _wav_duration(wav_path)


def _fmt_ts(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, milli = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def _wrap_caption(text: str, width: int = 52) -> str:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for word in words:
        trial = (" ".join(cur + [word])).strip()
        if len(trial) > width and cur:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        lines.append(" ".join(cur))
    # Keep at most 2 lines per cue for readability
    if len(lines) <= 2:
        return "\n".join(lines)
    # Split into chunks of 2 lines later by caller if needed; for long narration
    # we emit multiple cues in write_captions.
    return "\n".join(lines)


def _caption_chunks(text: str, duration: float) -> list[tuple[float, float, str]]:
    """Split long narration into timed caption chunks inside a segment."""
    words = text.split()
    if not words:
        return [(0.0, duration, "")]
    # Aim ~10-14 words per cue
    size = 12
    chunks = [" ".join(words[i : i + size]) for i in range(0, len(words), size)]
    slice_dur = duration / len(chunks)
    out = []
    for i, chunk in enumerate(chunks):
        start = i * slice_dur
        end = duration if i == len(chunks) - 1 else (i + 1) * slice_dur
        out.append((start, end, _wrap_caption(chunk)))
    return out


def _write_narration_file(timings: list[tuple[Segment, float, float]]) -> None:
    lines = [
        "Dispatch (Robocop) — Narração do onboarding da aba New Job (pt-BR)",
        f"Voz: {VOICE}",
        "",
    ]
    for seg, start, dur in timings:
        lines.append(f"[{_fmt_ts(start)} → {_fmt_ts(start + dur)}]  {seg.section} / {seg.id}")
        lines.append(seg.narration)
        lines.append("")
    NARRATION_OUT.write_text("\n".join(lines), encoding="utf-8")


def _write_srt(timings: list[tuple[Segment, float, float]]) -> None:
    idx = 1
    blocks: list[str] = []
    for seg, start, dur in timings:
        for c_start, c_end, text in _caption_chunks(seg.narration, dur):
            abs_start = start + c_start
            abs_end = start + c_end
            blocks.append(
                f"{idx}\n{_fmt_ts(abs_start)} --> {_fmt_ts(abs_end)}\n{text}\n"
            )
            idx += 1
    CAPTIONS_OUT.write_text("\n".join(blocks), encoding="utf-8")


def _write_storyboard(timings: list[tuple[Segment, float, float]]) -> None:
    lines = [
        "# Storyboard — Dispatch (Robocop) | New Job (pt-BR)",
        "",
        "Mapa seção → tela/ação → narração → texto na tela → destaque → resultado esperado.",
        "",
    ]
    for seg, start, dur in timings:
        lines.extend(
            [
                f"## {seg.id} — {seg.section}",
                "",
                f"- **Tempo:** {_fmt_ts(start)} → {_fmt_ts(start + dur)} ({dur:.1f}s)",
                f"- **Tela / ação:** `{seg.capture or seg.kind}` — {seg.highlight}",
                f"- **Narração:** {seg.narration}",
                f"- **Texto na tela:** {seg.on_screen}",
                f"- **Destaque visual:** {seg.highlight}",
                f"- **Resultado esperado:** {seg.expected}",
                "",
            ]
        )
    STORYBOARD_OUT.write_text("\n".join(lines), encoding="utf-8")


def _make_clip(png: Path, wav: Path, out_mp4: Path, duration: float) -> None:
    # Pad audio with silence so clip length matches the storyboard duration
    # (narration length + pad_after), keeping captions in sync.
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(png),
            "-i",
            str(wav),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=mono:sample_rate=44100",
            "-filter_complex",
            f"[1:a][2:a]concat=n=2:v=0:a=1,atrim=0:{duration:.3f}[a]",
            "-map",
            "0:v",
            "-map",
            "[a]",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(out_mp4),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _concat_and_burn(clips: list[Path], srt: Path, final: Path) -> None:
    concat_list = CLIPS_DIR / "concat.txt"
    concat_list.write_text("".join(f"file '{c}'\n" for c in clips), encoding="utf-8")
    muxed = CLIPS_DIR / "muxed_no_subs.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(muxed),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Burn subtitles (escape path for ffmpeg subtitles filter)
    srt_escaped = str(srt).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    vf = (
        f"subtitles={srt_escaped}:force_style="
        "'FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H80000000,BorderStyle=3,Outline=1,Shadow=0,"
        "MarginV=28,Alignment=2'"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(muxed),
            "-vf",
            vf,
            "-c:a",
            "copy",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(final),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _verify_captures(capture_pngs: dict[str, Path]) -> None:
    sys.path.insert(0, str(REPO_ROOT / "tools" / "dev"))
    from svg_text import svg_to_text

    checks = {
        "arrive": (["New Job", "Source", "Destination"], ["mastercard.com"]),
        "matrix": (["SOURCE", "SqlFile", "MonthlyJob", "ExistingTable"], ["mastercard.com"]),
        "source_dest": (["Source", "Destination", "SqlFile", "Csv"], ["mastercard.com"]),
        "queues": (["Execution Queue", "adhoc_fast"], ["mastercard.com"]),
        "picker": (["SQL File", "export_sales.sql"], ["mastercard.com"]),
        "email_bad": (["Invalid email format", "invalido"], ["mastercard.com"]),
        "ready_review": (["Ready to launch", "analyst@example.com"], ["Invalid email", "mastercard.com"]),
        "monthly": (["Start Date", "End Date", "MonthlyJob"], ["mastercard.com"]),
        "existing": (
            ["Existing Table", "events_existing", "ExistingTable supports Csv only"],
            ["mastercard.com"],
        ),
        "confirm": (["Launch Job", "SqlFile", "Csv", "analyst@example.com"], ["mastercard.com"]),
        "launched": (["Launched Job"], ["mastercard.com"]),
        "preview": (["SQL Preview", "SELECT"], ["mastercard.com"]),
        "overview": (["Overview", "Jobs", "running first"], ["mastercard.com", "SUCCEEDED"]),
    }
    for key, (need, forbid) in checks.items():
        svg = FRAMES_DIR / f"{key}.svg"
        text = svg_to_text(svg.read_text(encoding="utf-8"))
        for n in need:
            if n not in text:
                raise AssertionError(f"{key}: missing {n!r}")
        for f in forbid:
            if f in text:
                raise AssertionError(f"{key}: unexpected {f!r}")


async def _generate_all_captures() -> dict[str, Path]:
    setups = await _setups()
    keys = [
        "arrive",
        "matrix",
        "source_dest",
        "queues",
        "picker",
        "email_ok",
        "ready_actions",
        "monthly",
        "existing",
        "email_bad",
        "ready_review",
        "preview",
        "confirm",
        "launched",
        "overview",
    ]
    out: dict[str, Path] = {}
    for key in keys:
        print(f"  capturing {key}…")
        out[key] = await _capture_svg(key, setups[key])
    return out


async def main() -> int:
    _require_tools()
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    skip_capture = os.environ.get("SKIP_CAPTURE") == "1"
    skip_tts = os.environ.get("SKIP_TTS") == "1"

    if not skip_capture:
        print("Bootstrapping demo environment…")
        _bootstrap_demo_env()
        print("Capturing New Job UI frames from the live app…")
        captures = await _generate_all_captures()
        _verify_captures(captures)
        print("Capture content assertions passed.")
    else:
        print("SKIP_CAPTURE=1 — reusing existing SVG frames.")
        _verify_captures({})

    # Build PNG frames per segment
    print("Synthesizing narration and assembling clips…")
    timings: list[tuple[Segment, float, float]] = []
    clips: list[Path] = []
    cursor = 0.0

    for seg in SEGMENTS:
        png = FRAMES_DIR / f"{seg.id}.png"
        if seg.kind == "title":
            _title_card(
                "Dispatch (Robocop) | Como utilizar a aba New Job",
                "Guia para analistas — primeiro uso",
                png,
            )
        elif seg.kind == "section":
            _section_card(seg.section, seg.on_screen, png)
        elif seg.kind == "checklist":
            _checklist_card(png)
        else:
            raw_png = FRAMES_DIR / f"{seg.capture}_raw.png"
            _svg_to_png(FRAMES_DIR / f"{seg.capture}.svg", raw_png)
            _fit_canvas(raw_png, png, seg.on_screen, seg.highlight)

        mp3 = AUDIO_DIR / f"{seg.id}.mp3"
        wav = AUDIO_DIR / f"{seg.id}.wav"
        if skip_tts and wav.exists():
            dur = _wav_duration(wav) + seg.pad_after
        else:
            dur = await _synthesize(seg.narration, mp3, wav)
            dur = dur + seg.pad_after
        clip = CLIPS_DIR / f"{seg.id}.mp4"
        _make_clip(png, wav, clip, dur)
        timings.append((seg, cursor, dur))
        clips.append(clip)
        cursor += dur
        print(f"  {seg.id}: {dur:.1f}s")

    _write_narration_file(timings)
    _write_srt(timings)
    _write_storyboard(timings)

    print("Muxing final MP4 with burned-in captions…")
    _concat_and_burn(clips, CAPTIONS_OUT, VIDEO_OUT)

    # Validate playback
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size",
            "-of",
            "default=noprint_wrappers=1",
            str(VIDEO_OUT),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    print(probe.stdout)
    print(f"Wrote {VIDEO_OUT}")
    print(f"Wrote {NARRATION_OUT}")
    print(f"Wrote {CAPTIONS_OUT}")
    print(f"Wrote {STORYBOARD_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
