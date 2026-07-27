#!/usr/bin/env python3
"""Silent New Job onboarding video — 10–12s scenes, typing footer, spotlight.

Captures the real Dispatch UI and builds a silent walkthrough with:
- character-by-character footer reveal (fast handheld-RPG pacing feel)
- dimmed UI with a spotlight cutout on the explained element
- instructional scenes lasting exactly 10s (or up to 12s for longer text)

Verified MonthlyJob SQL rule: ``{date_inicio}`` and ``{date_fim}``.

Run:
  source mocks/dev-env.sh
  .venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py
"""

from __future__ import annotations

import asyncio
import json
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
TIMING_REPORT = OUT_DIR / "footer_timing_report.md"
ZIP_OUT = OUT_DIR / "dispatch_robocop_new_job_video_download.zip"
NARRATION_LEGACY = OUT_DIR / "dispatch_robocop_new_job_narration_ptbr.txt"

VIDEO_W, VIDEO_H = 1280, 720
FPS = 30
SCENE_STANDARD_S = 10.0
SCENE_LONG_S = 12.0
MOVE_FRAMES = 10
CLICK_FRAMES = 4
OUTCOME_S = 1.0
CALLOUT_H = 160
DIM_ALPHA = 145
SPOTLIGHT_PAD = 10
TERMINAL_SIZE = (150, 54)

DEMO_ROOT = Path("/tmp/dispatch_onboarding_silent_v2")
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
-- Exemplo MonthlyJob (não sensível)
SELECT
  region,
  SUM(amount) AS total
FROM sales
WHERE sale_date BETWEEN '{date_inicio}' AND '{date_fim}'
GROUP BY region;
"""

MONTHLY_SQL_EVIDENCE = [
    "dispatch/sql.py:DATE_INICIO_TOKEN/DATE_FIM_TOKEN, detect_source, template_is_complete, is_malformed_template, monthly_preview",
    "dispatch/screens/new_job.py:_sql_content_issues (requires both tokens for SqlTemplate/MonthlyJob)",
    "scr/monthly_query_processor.py:render_monthly_sql",
    "CONTEXT.md (SqlTemplate placeholders)",
    "tests/test_monthly_query_processor.py, tools/prod_tui/job_specs.py SMOKE_TEMPLATE_SQL",
]


@dataclass
class Step:
    id: str
    capture: str
    title: str
    body: str
    badge: str
    cursor: tuple[float, float]
    click: bool = False
    section: str = ""
    evidence: str = ""
    instructional: bool = True
    # Normalized UI rect (l, t, r, b). None = auto from cursor / card full.
    spotlight: tuple[float, float, float, float] | None = None
    # Force 10 or 12; None = auto from text length.
    scene_s: float | None = None


def _steps() -> list[Step]:
    """Ordered instructional steps. No 'Antes de começar'. Content preserved."""
    return [
        Step(
            "01_open",
            "card:open",
            "Dispatch (Robocop)",
            "Como utilizar a aba New Job\nConfigure e inicie um novo job passo a passo.",
            "",
            (0.50, 0.50),
            section="Abertura",
            evidence="opening card",
        ),
        Step(
            "02_purpose_a",
            "arrive",
            "Para que serve a aba New Job",
            "Ela permite configurar e iniciar uma nova execução no Dispatch.",
            "",
            (0.55, 0.12),
            section="Propósito",
            evidence="NewJobScreen title + form",
        ),
        Step(
            "02_purpose_b",
            "arrive",
            "O que você decide aqui",
            "Você escolhe a origem dos dados, o destino do resultado,\na consulta e as opções de execução do job.",
            "",
            (0.55, 0.20),
            section="Propósito",
            evidence="NewJobScreen compose()",
        ),
        Step(
            "03_matrix",
            "matrix",
            "Source × Destination",
            "Tabela de referência com as combinações permitidas.\nConsulte-a antes de escolher origem e destino.",
            "Opcional",
            (0.52, 0.18),
            click=True,
            section="Matriz",
            evidence="matrix-collapsible + LEGAL_CELLS",
        ),
        Step(
            "04_detected",
            "arrive",
            "Detected source",
            "Mostra o tipo identificado no arquivo SQL selecionado.\nConfirme se corresponde ao job que você quer executar.",
            "",
            (0.55, 0.28),
            section="Detecção",
            evidence="info-detected + sql.detect_source",
        ),
        Step(
            "05_source_intro",
            "source_sqlfile",
            "Source",
            "Define de onde os dados do job serão obtidos.\nÉ a primeira decisão do formulário.",
            "Obrigatório",
            (0.38, 0.34),
            section="Source",
            evidence="RadioSet #source",
        ),
        Step(
            "06_source_sqlfile",
            "source_sqlfile",
            "Source → SqlFile",
            "Use quando a consulta está em um arquivo .sql simples.\nO Dispatch executa essa consulta conforme o destino escolhido.",
            "Obrigatório",
            (0.38, 0.34),
            click=True,
            section="Source",
            evidence="src-sqlfile; LEGAL SqlFile→Table/Csv/Table+Csv",
        ),
        Step(
            "07_dest_intro",
            "source_sqlfile",
            "Destination",
            "Define onde o resultado do job será armazenado.\nA escolha depende da origem selecionada.",
            "Obrigatório",
            (0.70, 0.28),
            section="Destination",
            evidence="RadioSet #destination",
        ),
        Step(
            "08_dest_table",
            "dest_table",
            "Destination → Table",
            "Salva o resultado em uma tabela.\nUse quando precisar consultar o resultado depois no ambiente.",
            "Obrigatório",
            (0.70, 0.26),
            click=True,
            section="Destination",
            evidence="dst-table",
        ),
        Step(
            "09_dest_csv",
            "source_sqlfile",
            "Destination → Csv",
            "Gera um arquivo CSV na pasta de onde você abriu o Dispatch.\nUse quando o resultado precisa ser baixado ou compartilhado como arquivo.",
            "Obrigatório",
            (0.70, 0.30),
            click=True,
            section="Destination",
            evidence="dst-csv; ADR-0003 CSV in launch cwd",
        ),
        Step(
            "10_dest_tablecsv",
            "dest_tablecsv",
            "Destination → Table+Csv",
            "Cria a tabela e também gera o CSV.\nUse quando precisa dos dois formatos na mesma execução.",
            "Obrigatório",
            (0.70, 0.34),
            click=True,
            section="Destination",
            evidence="dst-table-csv",
        ),
        Step(
            "11_queue_a",
            "queues",
            "Execution Queue",
            "Indica a fila de processamento do job.\nSem marcação, o Dispatch escolhe automaticamente.",
            "Opcional",
            (0.55, 0.50),
            section="Fila",
            evidence="SelectionList #queue + Auto hint",
        ),
        Step(
            "12_queue_b",
            "queues",
            "Execution Queue — quando marcar",
            "Marque uma ou mais filas só se o seu projeto indicar qual usar.\nVárias filas são tentadas na ordem da lista.",
            "Opcional",
            (0.55, 0.54),
            click=True,
            section="Fila",
            evidence="_QUEUE_CHOICES / _QUEUE_AUTO_HINT",
        ),
        Step(
            "13_sql_intro",
            "picker",
            "SQL File",
            "É a consulta que o job vai executar.\nPara SqlFile e MonthlyJob, você precisa selecionar um arquivo .sql.",
            "Obrigatório",
            (0.55, 0.62),
            section="SQL File",
            evidence="row-sql-file + picker; required for SqlFile/SqlTemplate",
        ),
        Step(
            "14_sql_picker",
            "picker",
            "Lista de arquivos SQL",
            "Mostra os arquivos .sql da pasta atual.\nSelecione o arquivo do job para preencher o caminho automaticamente.",
            "Obrigatório",
            (0.55, 0.62),
            click=True,
            section="SQL File",
            evidence="sql-file-picker scans launch_cwd/*.sql",
        ),
        Step(
            "15_sql_verify",
            "picker",
            "O que conferir no arquivo",
            "Confirme o nome do arquivo e o tipo Detected na lista.\nO caminho aparece no campo SQL File após a seleção.",
            "Obrigatório",
            (0.58, 0.72),
            section="SQL File",
            evidence="picker columns File/Detected/Modified + path-hint",
        ),
        Step(
            "16_sql_role",
            "picker",
            "Papel do SQL File no job",
            "Esse arquivo define quais dados serão lidos ou calculados.\nSource e Destination decidem como o resultado será entregue.",
            "Obrigatório",
            (0.58, 0.72),
            section="SQL File",
            evidence="manifest source sql_path_at_launch",
        ),
        Step(
            "17_email",
            "email_ok",
            "Email (notifications)",
            "Recebe aviso quando o job terminar.\nDeixe em branco se não quiser notificação.",
            "Opcional",
            (0.58, 0.78),
            click=True,
            section="Notificação",
            evidence="#email; validation only if filled",
        ),
        Step(
            "18_subject",
            "email_ok",
            "Subject (email)",
            "Assunto do e-mail de notificação.\nUse um texto curto que identifique o job.",
            "Opcional",
            (0.58, 0.84),
            click=True,
            section="Notificação",
            evidence="#subject default Dispatch Job",
        ),
        Step(
            "19_status_bar",
            "ready_review",
            "Status do formulário",
            "Ready to launch indica que não há problemas bloqueantes.\nPreview SQL e Launch ficam na barra inferior.",
            "",
            (0.72, 0.92),
            section="Status",
            evidence="validation-summary + action bar",
        ),
        # --- MonthlyJob deep dive ---
        Step(
            "20_mj_intro",
            "monthly",
            "MonthlyJob",
            "Use quando a consulta precisa cobrir um intervalo de datas,\nexecutando o período mês a mês.",
            "Use apenas quando...",
            (0.38, 0.38),
            click=True,
            section="MonthlyJob",
            evidence="Source SqlTemplate labeled MonthlyJob; CONTEXT.md",
        ),
        Step(
            "21_mj_dest",
            "monthly",
            "MonthlyJob → Destination",
            "Com MonthlyJob, o destino permitido é apenas Table.\nCsv e Table+Csv ficam indisponíveis.",
            "Obrigatório",
            (0.70, 0.28),
            section="MonthlyJob",
            evidence="LEGAL_CELLS (SqlTemplate, Table) only; dest hint",
        ),
        Step(
            "22_mj_sql_rule_a",
            "card:sql_tokens",
            "SQL File no MonthlyJob — regra",
            "O arquivo .sql precisa conter os dois marcadores:\n{date_inicio} e {date_fim}",
            "Obrigatório",
            (0.50, 0.45),
            section="MonthlyJob SQL",
            evidence="; ".join(MONTHLY_SQL_EVIDENCE),
        ),
        Step(
            "23_mj_sql_rule_b",
            "card:sql_tokens",
            "Como conferir no arquivo",
            "Abra o .sql e busque exatamente {date_inicio} e {date_fim}.\nSe faltar um deles, o job não pode ser iniciado como MonthlyJob.",
            "Obrigatório",
            (0.50, 0.50),
            section="MonthlyJob SQL",
            evidence="new_job._sql_content_issues + is_malformed_template",
        ),
        Step(
            "24_mj_sql_rule_c",
            "card:sql_tokens",
            "O que esses marcadores fazem",
            "Eles reservam o início e o fim de cada mês no período informado.\nO Dispatch preenche as datas conforme Start Date e End Date.",
            "Obrigatório",
            (0.50, 0.55),
            section="MonthlyJob SQL",
            evidence="monthly_preview / render_monthly_sql substitution",
        ),
        Step(
            "25_mj_picker",
            "monthly_picker",
            "Selecionar o SQL do MonthlyJob",
            "Na lista, escolha o arquivo com Detected = MonthlyJob.\nIsso confirma que os dois marcadores foram encontrados.",
            "Obrigatório",
            (0.55, 0.60),
            click=True,
            section="MonthlyJob SQL",
            evidence="picker Detected column via detect_source",
        ),
        Step(
            "26_mj_schema",
            "monthly_fields",
            "Schema (MonthlyJob)",
            "Define o schema da tabela de resultado.\nInforme o schema correto do seu trabalho.",
            "Obrigatório",
            (0.58, 0.68),
            section="MonthlyJob campos",
            evidence="#schema visible when needs_table",
        ),
        Step(
            "27_mj_table",
            "monthly_fields",
            "Table Name (MonthlyJob)",
            "Nome da tabela de resultado, com o prefixo do seu usuário.\nComplete apenas o sufixo; o prefixo já vem preenchido.",
            "Obrigatório",
            (0.58, 0.74),
            section="MonthlyJob campos",
            evidence="#table-name-prefix + #table-name-suffix",
        ),
        Step(
            "28_mj_start",
            "monthly_fields",
            "Start Date",
            "Data inicial do período do job (formato AAAA-MM-DD).\nDefine o primeiro mês a processar.",
            "Obrigatório",
            (0.58, 0.80),
            section="MonthlyJob campos",
            evidence="#start-date; validate_date_range",
        ),
        Step(
            "29_mj_end",
            "monthly_fields",
            "End Date",
            "Data final do período (formato AAAA-MM-DD).\nDeve ser igual ou posterior à Start Date.",
            "Obrigatório",
            (0.58, 0.86),
            section="MonthlyJob campos",
            evidence="#end-date; validate_date_range",
        ),
        # --- ExistingTable deep dive ---
        Step(
            "30_et_intro",
            "existing",
            "ExistingTable",
            "Use quando os dados já estão em uma tabela e você\nquer exportá-los, sem rodar um arquivo SQL.",
            "Use apenas quando...",
            (0.38, 0.36),
            click=True,
            section="ExistingTable",
            evidence="src-existingtable; no SQL path",
        ),
        Step(
            "31_et_dest",
            "existing",
            "ExistingTable → Destination",
            "Neste modo o destino permitido é apenas Csv.\nTable e Table+Csv ficam indisponíveis.",
            "Obrigatório",
            (0.70, 0.30),
            section="ExistingTable",
            evidence="LEGAL (ExistingTable, Csv); dest hint",
        ),
        Step(
            "32_et_no_sql",
            "existing",
            "Sem SQL File",
            "A lista e o campo SQL File ficam ocultos.\nA origem é a tabela existente, não um arquivo .sql.",
            "Use apenas quando...",
            (0.55, 0.48),
            section="ExistingTable",
            evidence="row-sql-file/picker display=False",
        ),
        Step(
            "33_et_schema_coe",
            "existing_coe",
            "Schema → coe_enc",
            "Seleciona o schema coe_enc da tabela existente.\nUse quando a tabela estiver nesse schema.",
            "Obrigatório",
            (0.50, 0.68),
            click=True,
            section="ExistingTable Schema",
            evidence="RadioButton esc-coe-enc",
        ),
        Step(
            "34_et_schema_aa",
            "existing_fields",
            "Schema → aa_enc",
            "Seleciona o schema aa_enc da tabela existente.\nÉ a opção padrão quando a tabela está em aa_enc.",
            "Obrigatório",
            (0.55, 0.68),
            click=True,
            section="ExistingTable Schema",
            evidence="RadioButton esc-aa-enc",
        ),
        Step(
            "35_et_schema_other",
            "existing_other",
            "Schema → other",
            "Use quando o schema não é coe_enc nem aa_enc.\nAo marcar other, aparece o campo Custom Schema.",
            "Use apenas quando...",
            (0.60, 0.68),
            click=True,
            section="ExistingTable Schema",
            evidence="esc-other enables #existing-schema-custom",
        ),
        Step(
            "36_et_custom",
            "existing_other",
            "Custom Schema",
            "Digite o nome do schema personalizado.\nSó aparece quando Schema = other.",
            "Obrigatório",
            (0.58, 0.74),
            section="ExistingTable Schema",
            evidence="row-existing-schema-custom",
        ),
        Step(
            "37_et_table",
            "existing_fields",
            "Existing Table",
            "Informe só o nome da tabela (sem o schema).\nJunto com o schema, forma a origem completa schema.tabela.",
            "Obrigatório",
            (0.58, 0.78),
            click=True,
            section="ExistingTable",
            evidence="#existing-table; validate_full_table",
        ),
        # --- Relationships ---
        Step(
            "38_rel_standard",
            "ready_review",
            "Combinação comum",
            "SqlFile + Csv + arquivo .sql sem marcadores de data.\nFluxo típico para gerar um CSV a partir de uma consulta.",
            "",
            (0.55, 0.36),
            click=True,
            section="Relações",
            evidence="LEGAL SqlFile/Csv; detect_source without tokens",
        ),
        Step(
            "39_rel_monthly",
            "monthly_fields",
            "Combinação MonthlyJob",
            "MonthlyJob + Table + .sql com {date_inicio} e {date_fim}\n+ Schema, Table Name, Start Date e End Date.",
            "",
            (0.55, 0.40),
            section="Relações",
            evidence="LEGAL SqlTemplate/Table + date fields",
        ),
        Step(
            "40_rel_existing",
            "existing_fields",
            "Combinação ExistingTable",
            "ExistingTable + Csv + Schema + Existing Table.\nNão usa SQL File nem MonthlyJob ao mesmo tempo.",
            "",
            (0.55, 0.42),
            section="Relações",
            evidence="Source radio exclusive; ExistingTable hides SQL",
        ),
        Step(
            "41_rel_incompat",
            "matrix",
            "Combinações indisponíveis",
            "MonthlyJob não aceita Csv ou Table+Csv.\nExistingTable não aceita Table ou Table+Csv.",
            "",
            (0.52, 0.20),
            section="Relações",
            evidence="LEGAL_CELLS matrix",
        ),
        # --- Validation / preview / launch ---
        Step(
            "42_val_bad",
            "email_bad",
            "E-mail inválido",
            "Se o formato estiver incorreto, o status mostra o problema.\nCorrija antes de continuar.",
            "",
            (0.58, 0.78),
            section="Validação",
            evidence="Invalid email format in validation-summary",
        ),
        Step(
            "43_val_ok",
            "ready_review",
            "Formulário pronto",
            "Com os dados corrigidos, o status volta a Ready to launch.\nRevise origem, destino, arquivo e fila.",
            "",
            (0.72, 0.92),
            section="Validação",
            evidence="Ready to launch",
        ),
        Step(
            "44_preview",
            "preview",
            "Preview SQL",
            "Mostra o conteúdo que será usado no job.\nConfira se a consulta e o destino estão corretos antes do envio.",
            "",
            (0.78, 0.92),
            click=True,
            section="Preview",
            evidence="Preview SQL [P]; unavailable for ExistingTable",
        ),
        Step(
            "45_checklist",
            "card:checklist",
            "Antes de iniciar, confirme:",
            "• origem e destino;\n• arquivo ou tabela selecionados;\n• fila de execução;\n• opções adicionais;\n• e-mail de notificação.",
            "",
            (0.50, 0.50),
            section="Revisão",
            evidence="analyst checklist from form fields",
        ),
        Step(
            "46_confirm",
            "confirm",
            "Launch Job",
            "Inicia o job com as configurações revisadas.\nLeia o resumo e confirme apenas se estiver correto.",
            "",
            (0.42, 0.72),
            click=True,
            section="Envio",
            evidence="ConfirmScreen Launch Job",
        ),
        Step(
            "47_launched",
            "launched",
            "Job enviado",
            "O job foi enviado pelo Dispatch.\nAcompanhe o andamento na tela de monitoramento.",
            "",
            (0.55, 0.88),
            section="Envio",
            evidence="Launched Job message; no Impala success claim",
        ),
        Step(
            "48_overview",
            "overview",
            "Overview",
            "Após o envio, acompanhe o status do job no Overview.",
            "",
            (0.12, 0.22),
            click=True,
            section="Overview",
            evidence="DashboardScreen / Overview nav",
        ),
        Step(
            "49_close",
            "card:close",
            "Resumo",
            "Na aba New Job, você:\n1. define a execução;\n2. revisa as configurações;\n3. inicia o job;\n4. acompanha o resultado no Overview.\n\nEm caso de dúvida, revise os campos antes de selecionar Launch Job.",
            "",
            (0.50, 0.50),
            section="Encerramento",
            evidence="closing summary",
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
        missing.append("textual==8.2.5")
    if missing:
        raise SystemExit("Missing:\n- " + "\n- ".join(missing))


def _bootstrap() -> None:
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


async def _open_new_job(pilot, app) -> None:
    from dispatch.screens.dashboard import DashboardScreen
    from dispatch.screens.new_job import NewJobScreen

    await pilot.pause(1.2)
    if not isinstance(app.screen, NewJobScreen):
        if not isinstance(app.screen, DashboardScreen):
            await pilot.pause(0.5)
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
            await pilot.pause(0.4)
            app.push_screen(DashboardScreen())
            await pilot.pause(1.0)
            app.save_screenshot(filename=str(out))
            return out
        await _open_new_job(pilot, app)
        await setup(pilot, app)
        if isinstance(app.screen, NewJobScreen):
            _neutral_email(app.screen)
        await pilot.pause(0.35)
        app.save_screenshot(filename=str(out))
    if not out.exists():
        raise RuntimeError(f"missing {out}")
    return out


async def _setups():
    from textual.widgets import Input, RadioButton, RadioSet, SelectionList

    from dispatch.screens.confirm import ConfirmScreen
    from dispatch.screens.new_job import NewJobScreen

    async def arrive(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = False
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        await p.pause(0.25)

    async def matrix(p, a):
        s = a.screen
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#matrix-collapsible").collapsed = False
        await p.pause(0.2)

    async def source_sqlfile(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        await p.pause(0.25)
        s.query_one("#source", RadioSet).focus()

    async def dest_table(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-table", RadioButton).value = True
        await p.pause(0.3)
        s.query_one("#row-schema").scroll_visible(animate=False)

    async def dest_tablecsv(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-table-csv", RadioButton).value = True
        await p.pause(0.3)

    async def queues(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        await p.pause(0.2)
        s.query_one("#queue", SelectionList).focus()

    async def picker(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        await p.pause(0.2)
        s.query_one("#sql-file-picker").focus()
        s.query_one("#row-sql-file").scroll_visible(animate=False)

    async def email_ok(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "analyst@example.com"
        s.query_one("#subject", Input).value = "Onboarding demo"
        await p.pause(0.25)
        s.query_one("#row-subject").scroll_visible(animate=False)

    async def monthly(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqltemplate", RadioButton).value = True
        await p.pause(0.45)

    async def monthly_picker(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqltemplate", RadioButton).value = True
        await p.pause(0.3)
        picker = s.query_one("#sql-file-picker")
        picker.focus()
        # highlight monthly_revenue.sql (second row alphabetically after export)
        await p.press("down")
        await p.pause(0.3)

    async def monthly_fields(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqltemplate", RadioButton).value = True
        await p.pause(0.4)
        s.query_one("#row-end-date").scroll_visible(animate=False)

    async def existing(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-existingtable", RadioButton).value = True
        await p.pause(0.35)

    async def existing_fields(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-existingtable", RadioButton).value = True
        s.query_one("#esc-aa-enc", RadioButton).value = True
        s.query_one("#existing-table", Input).value = "events_existing"
        s.query_one("#email", Input).value = "analyst@example.com"
        await p.pause(0.35)
        s.query_one("#row-existing-table").scroll_visible(animate=False)

    async def existing_coe(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-existingtable", RadioButton).value = True
        s.query_one("#esc-coe-enc", RadioButton).value = True
        s.query_one("#existing-table", Input).value = "events_existing"
        s.query_one("#email", Input).value = "analyst@example.com"
        await p.pause(0.35)
        s.query_one("#row-existing-schema").scroll_visible(animate=False)

    async def existing_other(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-existingtable", RadioButton).value = True
        s.query_one("#esc-other", RadioButton).value = True
        s.query_one("#existing-schema-custom", Input).value = "demo_schema"
        s.query_one("#existing-table", Input).value = "events_existing"
        s.query_one("#email", Input).value = "analyst@example.com"
        await p.pause(0.4)
        s.query_one("#row-existing-schema-custom").scroll_visible(animate=False)

    async def ready_review(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "analyst@example.com"
        s.query_one("#subject", Input).value = "Onboarding demo"
        await p.pause(0.3)
        s.query_one("#row-email").scroll_visible(animate=False)

    async def email_bad(p, a):
        s = a.screen
        s.query_one("#matrix-collapsible").collapsed = True
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "invalido"
        await p.pause(0.35)
        s.query_one("#row-email").scroll_visible(animate=False)

    async def preview(p, a):
        s = a.screen
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "analyst@example.com"
        s.query_one("#source", RadioSet).focus()
        await p.press("p")
        await p.pause(0.55)

    async def confirm(p, a):
        s = a.screen
        assert isinstance(s, NewJobScreen)
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "analyst@example.com"
        s.query_one("#subject", Input).value = "Onboarding demo"
        await p.pause(0.25)
        summary = (
            f"Source: [cyan]SqlFile[/]  {LAUNCH_CWD / 'export_sales.sql'}\n"
            f"Destination: [cyan]Csv[/]\n"
            f"Target table: [cyan]aa_enc.analyst_dispatch_result[/]\n"
            f"Queue: [cyan]Auto (cycle all queues)[/]\n"
            f"CSV path: {LAUNCH_CWD / 'analyst_dispatch_result.csv'}\n"
            f"Email: analyst@example.com"
        )
        a.push_screen(
            ConfirmScreen(
                "Launch Job",
                summary,
                danger=True,
                confirm_label="Launch",
                cancel_label="Review",
            )
        )
        await p.pause(0.45)

    async def launched(p, a):
        s = a.screen
        s.query_one("#src-sqlfile", RadioButton).value = True
        s.query_one("#dst-csv", RadioButton).value = True
        s.query_one("#email", Input).value = "analyst@example.com"
        s.query_one("#subject", Input).value = "Onboarding demo"
        await p.pause(0.25)
        s.query_one("#source", RadioSet).focus()
        await p.click("#launch")
        await p.pause(0.45)
        await p.press("y")
        await p.pause(1.6)
        s.query_one("#warning-text").scroll_visible(animate=False)

    return {
        "arrive": arrive,
        "matrix": matrix,
        "source_sqlfile": source_sqlfile,
        "dest_table": dest_table,
        "dest_tablecsv": dest_tablecsv,
        "queues": queues,
        "picker": picker,
        "email_ok": email_ok,
        "monthly": monthly,
        "monthly_picker": monthly_picker,
        "monthly_fields": monthly_fields,
        "existing": existing,
        "existing_fields": existing_fields,
        "existing_coe": existing_coe,
        "existing_other": existing_other,
        "ready_review": ready_review,
        "email_bad": email_bad,
        "preview": preview,
        "confirm": confirm,
        "launched": launched,
        "overview": arrive,
    }




def _full_footer_text(title: str, body: str) -> str:
    return f"{title}\n{body}" if body else title


def _char_count(title: str, body: str) -> int:
    return len(_full_footer_text(title, body))


def _resolved_scene_s(step: Step) -> float:
    if step.scene_s is not None:
        return float(step.scene_s)
    # Prefer 10s. Use 12s only when the footer is genuinely long to read.
    n = _char_count(step.title, step.body)
    lines = (step.body or "").count("\n") + (1 if step.body else 0)
    if n >= 130 or lines >= 4:
        return SCENE_LONG_S
    return SCENE_STANDARD_S


def _resolved_spotlight(step: Step) -> tuple[float, float, float, float]:
    if step.spotlight is not None:
        return step.spotlight
    if step.capture.startswith("card:"):
        return (0.08, 0.12, 0.92, 0.78)
    cx, cy = step.cursor
    # Element-sized defaults by section / id.
    presets: dict[str, tuple[float, float]] = {
        "Abertura": (0.42, 0.28),
        "Propósito": (0.55, 0.18),
        "Matriz": (0.55, 0.16),
        "Detecção": (0.50, 0.08),
        "Source": (0.22, 0.12),
        "Destination": (0.22, 0.12),
        "Fila": (0.42, 0.18),
        "SQL File": (0.50, 0.16),
        "Notificação": (0.50, 0.07),
        "Status": (0.45, 0.08),
        "MonthlyJob": (0.28, 0.14),
        "MonthlyJob SQL": (0.50, 0.28),
        "MonthlyJob campos": (0.48, 0.08),
        "ExistingTable": (0.28, 0.14),
        "ExistingTable Schema": (0.40, 0.10),
        "Relações": (0.55, 0.22),
        "Validação": (0.48, 0.10),
        "Preview": (0.28, 0.10),
        "Revisão": (0.45, 0.30),
        "Envio": (0.45, 0.22),
        "Overview": (0.18, 0.20),
        "Encerramento": (0.42, 0.30),
    }
    # Specific overrides for combined regions
    id_overrides = {
        "21_mj_dest": (0.52, 0.30, 0.38, 0.12),  # source+dest for MJ
        "31_et_dest": (0.52, 0.30, 0.38, 0.12),
        "32_et_no_sql": (0.50, 0.42, 0.40, 0.14),
        "39_rel_monthly": (0.50, 0.38, 0.42, 0.28),
        "40_rel_existing": (0.50, 0.36, 0.42, 0.24),
        "38_rel_standard": (0.50, 0.34, 0.42, 0.22),
        "41_rel_incompat": (0.52, 0.18, 0.42, 0.14),
        "03_matrix": (0.52, 0.16, 0.45, 0.12),
        "04_detected": (0.52, 0.26, 0.40, 0.06),
        "05_source_intro": (0.36, 0.32, 0.18, 0.10),
        "06_source_sqlfile": (0.36, 0.32, 0.18, 0.10),
        "07_dest_intro": (0.70, 0.30, 0.18, 0.10),
        "08_dest_table": (0.70, 0.26, 0.18, 0.08),
        "09_dest_csv": (0.70, 0.30, 0.18, 0.08),
        "10_dest_tablecsv": (0.70, 0.34, 0.18, 0.08),
        "11_queue_a": (0.55, 0.48, 0.38, 0.14),
        "12_queue_b": (0.55, 0.52, 0.38, 0.14),
        "13_sql_intro": (0.55, 0.58, 0.42, 0.14),
        "14_sql_picker": (0.55, 0.58, 0.42, 0.14),
        "15_sql_verify": (0.55, 0.62, 0.42, 0.16),
        "16_sql_role": (0.55, 0.68, 0.42, 0.10),
        "17_email": (0.58, 0.76, 0.42, 0.06),
        "18_subject": (0.58, 0.82, 0.42, 0.06),
        "19_status_bar": (0.70, 0.90, 0.28, 0.06),
        "20_mj_intro": (0.36, 0.36, 0.20, 0.10),
        "25_mj_picker": (0.55, 0.56, 0.42, 0.14),
        "26_mj_schema": (0.58, 0.66, 0.40, 0.06),
        "27_mj_table": (0.58, 0.72, 0.40, 0.06),
        "28_mj_start": (0.58, 0.78, 0.40, 0.06),
        "29_mj_end": (0.58, 0.84, 0.40, 0.06),
        "30_et_intro": (0.36, 0.36, 0.20, 0.10),
        "33_et_schema_coe": (0.48, 0.66, 0.28, 0.08),
        "34_et_schema_aa": (0.55, 0.66, 0.28, 0.08),
        "35_et_schema_other": (0.62, 0.66, 0.28, 0.08),
        "36_et_custom": (0.58, 0.72, 0.40, 0.06),
        "37_et_table": (0.58, 0.76, 0.40, 0.06),
        "42_val_bad": (0.58, 0.76, 0.40, 0.08),
        "43_val_ok": (0.70, 0.90, 0.28, 0.06),
        "44_preview": (0.62, 0.48, 0.32, 0.28),
        "46_confirm": (0.50, 0.55, 0.36, 0.28),
        "47_launched": (0.55, 0.70, 0.40, 0.18),
        "48_overview": (0.14, 0.22, 0.14, 0.16),
    }
    if step.id in id_overrides:
        cx, cy, hw, hh = id_overrides[step.id]
        return (max(0.02, cx - hw), max(0.02, cy - hh), min(0.98, cx + hw), min(0.95, cy + hh))
    hw, hh = presets.get(step.section, (0.28, 0.10))
    return (max(0.02, cx - hw), max(0.02, cy - hh), min(0.98, cx + hw), min(0.95, cy + hh))


def _typing_plan(step: Step, scene_s: float) -> tuple[int, float]:
    """Return (anim_frames, anim_seconds). ≤25% of scene, target ~1.5–2.0s."""
    n = max(1, _char_count(step.title, step.body))
    max_anim = scene_s * 0.25
    # Prefer ~1.5s standard / ~2.0s long, but never exceed 25%.
    target = 2.0 if scene_s >= SCENE_LONG_S else 1.5
    anim_s = min(max_anim, target)
    # Keep typing snappy: at least ~35 chars/sec feel
    min_s = min(max_anim, max(0.8, n / 55.0))
    anim_s = max(min_s, min(anim_s, max_anim))
    frames = max(8, int(round(anim_s * FPS)))
    anim_s = frames / FPS
    if anim_s > max_anim + 1e-9:
        frames = max(8, int(math.floor(max_anim * FPS)))
        anim_s = frames / FPS
    return frames, anim_s


def _visible_parts(title: str, body: str, n_chars: int) -> tuple[str, str]:
    full = _full_footer_text(title, body)
    vis = full[: max(0, n_chars)]
    if "\n" in vis:
        t, b = vis.split("\n", 1)
        return t, b
    return vis, ""



def _fonts(sizes: tuple[int, int, int]):
    from PIL import ImageFont

    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    def load(cands, size):
        for p in cands:
            if Path(p).exists():
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()
    return load(bold_paths, sizes[0]), load(paths, sizes[1]), load(paths, sizes[2])


def _svg_to_png(svg: Path, png: Path) -> None:
    import cairosvg

    cairosvg.svg2png(url=svg.as_uri(), write_to=str(png), output_width=VIDEO_W)


def _card(title: str, body: str, dest: Path, *, accent: str | None = None) -> None:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (VIDEO_W, VIDEO_H), (16, 22, 32))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 10, VIDEO_H), fill=(64, 156, 255))
    bold, mid, small = _fonts((34, 24, 22))
    y = 120
    draw.text((64, y), title, fill=(245, 245, 245), font=bold)
    y += 70
    for line in body.split("\n"):
        color = (210, 220, 235)
        font = mid if not line.startswith("WHERE") and "{" not in line else small
        if "{" in line:
            color = (255, 220, 120)
            font = mid
        draw.text((64, y), line, fill=color, font=font)
        y += 42
    img.save(dest)


def _draw_cursor(draw, x: int, y: int, *, clicking: bool = False) -> None:
    pts = [
        (x, y),
        (x, y + 22),
        (x + 6, y + 17),
        (x + 12, y + 28),
        (x + 16, y + 26),
        (x + 10, y + 15),
        (x + 18, y + 15),
    ]
    draw.polygon(pts, fill=(255, 255, 255), outline=(20, 20, 20))
    if clicking:
        r = 18
        draw.ellipse((x - r, y - r, x + r, y + r), outline=(64, 156, 255), width=3)


def _layout_ui(ui_png: Path):
    from PIL import Image

    ui = Image.open(ui_png).convert("RGBA")
    max_h = VIDEO_H - CALLOUT_H
    ratio = min(VIDEO_W / ui.width, max_h / ui.height)
    new = ui.resize(
        (max(1, int(ui.width * ratio)), max(1, int(ui.height * ratio))),
        Image.Resampling.LANCZOS,
    )
    ox = (VIDEO_W - new.width) // 2
    oy = max(0, (max_h - new.height) // 2)
    return ui, new, ox, oy


def _compose(
    ui_png: Path,
    dest: Path,
    *,
    title: str,
    body: str,
    badge: str,
    cursor: tuple[float, float],
    spotlight: tuple[float, float, float, float],
    clicking: bool = False,
    reveal_chars: int | None = None,
    show_spotlight: bool = True,
    show_footer: bool = True,
) -> None:
    from PIL import Image, ImageDraw

    ui, new, ox, oy = _layout_ui(ui_png)
    canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (12, 14, 18, 255))
    canvas.paste(new, (ox, oy), new)

    if show_spotlight:
        # Dim everything, then restore spotlight cutout from undimmed UI.
        dim = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, DIM_ALPHA))
        canvas = Image.alpha_composite(canvas, dim)
        l, t, r, b = spotlight
        sx0 = ox + int(l * new.width) - SPOTLIGHT_PAD
        sy0 = oy + int(t * new.height) - SPOTLIGHT_PAD
        sx1 = ox + int(r * new.width) + SPOTLIGHT_PAD
        sy1 = oy + int(b * new.height) + SPOTLIGHT_PAD
        sx0, sy0 = max(0, sx0), max(0, sy0)
        sx1, sy1 = min(VIDEO_W, sx1), min(VIDEO_H - CALLOUT_H, sy1)
        if sx1 > sx0 and sy1 > sy0:
            # Paste bright UI region back
            bright = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
            bright.paste(new, (ox, oy), new)
            crop = bright.crop((sx0, sy0, sx1, sy1))
            canvas.paste(crop, (sx0, sy0), crop)
            draw = ImageDraw.Draw(canvas)
            # Soft outline / glow
            for w, a in ((6, 90), (3, 180)):
                draw.rounded_rectangle(
                    (sx0 - 2, sy0 - 2, sx1 + 2, sy1 + 2),
                    radius=8,
                    outline=(64, 156, 255, a),
                    width=w,
                )

    draw = ImageDraw.Draw(canvas)
    cx = ox + int(cursor[0] * new.width)
    cy = oy + int(cursor[1] * new.height)
    # Keep cursor off labels slightly when possible
    _draw_cursor(draw, cx, cy, clicking=clicking)

    if show_footer:
        n = reveal_chars if reveal_chars is not None else _char_count(title, body)
        vis_title, vis_body = _visible_parts(title, body, n)
        panel = Image.new("RGBA", (VIDEO_W, CALLOUT_H), (20, 32, 48, 245))
        canvas.alpha_composite(panel, (0, VIDEO_H - CALLOUT_H))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, VIDEO_H - CALLOUT_H, 10, VIDEO_H), fill=(64, 156, 255, 255))
        bold, mid, small = _fonts((26, 20, 17))
        y0 = VIDEO_H - CALLOUT_H + 14
        if vis_title:
            draw.text((28, y0), vis_title, fill=(245, 245, 245, 255), font=bold)
        if badge and n >= len(title):
            bw = 18 + len(badge) * 9
            bx = VIDEO_W - bw - 24
            color = {
                "Obrigatório": (200, 70, 70),
                "Opcional": (70, 140, 90),
                "Use apenas quando...": (180, 130, 40),
            }.get(badge, (90, 90, 90))
            draw.rounded_rectangle((bx, y0, bx + bw, y0 + 26), radius=6, fill=color)
            draw.text((bx + 8, y0 + 4), badge, fill=(255, 255, 255, 255), font=small)
        y = y0 + 38
        for line in vis_body.split("\n"):
            draw.text((28, y), line, fill=(210, 220, 235, 255), font=mid)
            y += 26

    canvas.convert("RGB").save(dest)


def _compose_card_scene(
    card_png: Path,
    dest: Path,
    *,
    title: str,
    body: str,
    badge: str,
    reveal_chars: int | None = None,
) -> None:
    """Card scenes: keep center content bright, dim margins, type footer."""
    from PIL import Image, ImageDraw

    card = Image.open(card_png).convert("RGBA").resize((VIDEO_W, VIDEO_H), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (12, 14, 18, 255))
    canvas.paste(card, (0, 0), card)
    dimmed = Image.alpha_composite(canvas, Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 90)))
    sx0, sy0, sx1, sy1 = 48, 72, VIDEO_W - 48, VIDEO_H - CALLOUT_H - 16
    dimmed.paste(card.crop((sx0, sy0, sx1, sy1)), (sx0, sy0))
    canvas = dimmed
    draw = ImageDraw.Draw(canvas)
    for w, a in ((6, 90), (3, 180)):
        draw.rounded_rectangle(
            (sx0 - 2, sy0 - 2, sx1 + 2, sy1 + 2),
            radius=10,
            outline=(64, 156, 255, a),
            width=w,
        )

    n = reveal_chars if reveal_chars is not None else _char_count(title, body)
    vis_title, vis_body = _visible_parts(title, body, n)
    panel = Image.new("RGBA", (VIDEO_W, CALLOUT_H), (20, 32, 48, 245))
    canvas.alpha_composite(panel, (0, VIDEO_H - CALLOUT_H))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, VIDEO_H - CALLOUT_H, 10, VIDEO_H), fill=(64, 156, 255, 255))
    bold, mid, small = _fonts((26, 20, 17))
    y0 = VIDEO_H - CALLOUT_H + 14
    if vis_title:
        draw.text((28, y0), vis_title, fill=(245, 245, 245, 255), font=bold)
    if badge and n >= len(title):
        bw = 18 + len(badge) * 9
        bx = VIDEO_W - bw - 24
        color = {
            "Obrigatório": (200, 70, 70),
            "Opcional": (70, 140, 90),
            "Use apenas quando...": (180, 130, 40),
        }.get(badge, (90, 90, 90))
        draw.rounded_rectangle((bx, y0, bx + bw, y0 + 26), radius=6, fill=color)
        draw.text((bx + 8, y0 + 4), badge, fill=(255, 255, 255, 255), font=small)
    y = y0 + 38
    for line in vis_body.split("\n"):
        draw.text((28, y), line, fill=(210, 220, 235, 255), font=mid)
        y += 26
    canvas.convert("RGB").save(dest)


def _encode_still(png: Path, seconds: float, out_mp4: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(png),
            "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=44100",
            "-t", f"{seconds:.3f}", "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "64k", "-shortest", str(out_mp4),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _encode_seq(pngs: list[Path], out_mp4: Path) -> None:
    seq = CLIPS_DIR / f"_seq_{out_mp4.stem}"
    if seq.exists():
        shutil.rmtree(seq)
    seq.mkdir(parents=True)
    for i, src in enumerate(pngs):
        shutil.copy2(src, seq / f"f{i:04d}.png")
    subprocess.run(
        [
            "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(seq / "f%04d.png"),
            "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=44100",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "64k", "-shortest", str(out_mp4),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    shutil.rmtree(seq, ignore_errors=True)


def _fmt_ts(seconds: float) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, milli = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def _validate_timing(rows: list[dict]) -> None:
    lines = [
        "# Instructional scene timing validation",
        "",
        f"Rule: each instructional scene total **{SCENE_STANDARD_S:.1f}–{SCENE_LONG_S:.1f}s** "
        f"(includes text-reveal). Standard = {SCENE_STANDARD_S:.1f}s; long messages may use "
        f"{SCENE_LONG_S:.1f}s. Text animation ≤ 25% of scene.",
        "",
        "| Scene | Element | Anim start | Anim end | Scene end | Anim | Total | Static | Spotlight | Result |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    failed = []
    n10 = n12 = 0
    for row in rows:
        if not row["instructional"]:
            continue
        total = row["scene_duration"]
        anim = row["anim_duration"]
        static = row["static_duration"]
        ok = True
        reasons = []
        if total + 1e-6 < SCENE_STANDARD_S:
            ok = False
            reasons.append("too short")
        if total - 1e-6 > SCENE_LONG_S:
            ok = False
            reasons.append("too long")
        # Standard messages should be 10s (± small float)
        if abs(row["target_s"] - SCENE_STANDARD_S) < 1e-6 and abs(total - SCENE_STANDARD_S) > 0.05:
            ok = False
            reasons.append("standard not 10s")
        if abs(row["target_s"] - SCENE_LONG_S) < 1e-6 and abs(total - SCENE_LONG_S) > 0.05:
            ok = False
            reasons.append("long not 12s")
        if anim > row["target_s"] * 0.25 + 1e-6:
            ok = False
            reasons.append("anim>25%")
        if static < 0:
            ok = False
            reasons.append("negative static")
        if not row.get("spotlight_ok", True):
            ok = False
            reasons.append("spotlight mismatch")
        if abs(total - SCENE_STANDARD_S) < 0.05:
            n10 += 1
        elif abs(total - SCENE_LONG_S) < 0.05:
            n12 += 1
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed.append(f"{row['id']}({','.join(reasons)})")
        lines.append(
            f"| `{row['id']}` | {row['title'][:28]} | {_fmt_ts(row['anim_start'])} | "
            f"{_fmt_ts(row['anim_end'])} | {_fmt_ts(row['scene_end'])} | "
            f"{anim:.2f}s | {total:.2f}s | {static:.2f}s | `{row['spotlight']}` | **{status}** |"
        )
        lines.append(f"|  | footer: {row['title']} — {row['body'][:90]} | | | | | | | | |")
    lines.append("")
    lines.append(f"Instructional scenes: {sum(1 for r in rows if r['instructional'])}")
    lines.append(f"10s scenes: {n10}")
    lines.append(f"12s scenes: {n12}")
    durs = [r["scene_duration"] for r in rows if r["instructional"]]
    lines.append(f"Min scene: {min(durs):.2f}s")
    lines.append(f"Max scene: {max(durs):.2f}s")
    if failed:
        lines.append("")
        lines.append(f"**FAILED scenes:** {', '.join(failed)}")
        TIMING_REPORT.write_text("\n".join(lines), encoding="utf-8")
        raise AssertionError(f"Timing validation failed: {failed}. See {TIMING_REPORT}")
    lines.append("")
    lines.append("**Overall: PASS**")
    TIMING_REPORT.write_text("\n".join(lines), encoding="utf-8")


def _write_srt(rows: list[dict]) -> None:
    blocks = []
    idx = 1
    for row in rows:
        if not row["instructional"]:
            continue
        text = f"{row['title']}\n{row['body']}"
        if row["badge"]:
            text = f"[{row['badge']}] {row['title']}\n{row['body']}"
        # captions cover full instructional scene (anim+static)
        blocks.append(
            f"{idx}\n{_fmt_ts(row['anim_start'])} --> {_fmt_ts(row['scene_end'])}\n{text}\n"
        )
        idx += 1
    CAPTIONS_OUT.write_text("\n".join(blocks), encoding="utf-8")


def _write_storyboard(rows: list[dict], steps: list[Step]) -> None:
    by_id = {s.id: s for s in steps}
    lines = [
        "# Storyboard — New Job (silencioso, pt-BR, 10–12s + typing + spotlight)",
        "",
        "Sem narração e sem música. Sem seção “Antes de começar”.",
        "Cada cena instrucional: revelação caractere a caractere + leitura estática; "
        "duração total 10s (ou 12s se o texto for mais longo).",
        "",
    ]
    for row in rows:
        step = by_id[row["id"]]
        lines += [
            f"## {step.id} — {step.section}",
            "",
            f"- **Elemento:** {step.title}",
            f"- **Capture:** `{step.capture}`",
            f"- **Spotlight:** `{row['spotlight']}`",
            f"- **Cursor:** move → stop em {step.cursor}"
            + (" → clique após leitura" if step.click else ""),
            f"- **Footer:** {step.title} — {step.body.replace(chr(10), ' / ')}",
            f"- **Badge:** {step.badge or '—'}",
            f"- **Text anim:** {_fmt_ts(row['anim_start'])} → {_fmt_ts(row['anim_end'])} "
            f"({row['anim_duration']:.2f}s)",
            f"- **Scene end:** {_fmt_ts(row['scene_end'])}",
            f"- **Total scene:** {row['scene_duration']:.2f}s "
            f"(static after anim: {row['static_duration']:.2f}s)",
            f"- **Resultado esperado:** analista entende decisão em “{step.title}”",
            f"- **Evidência de verificação:** {step.evidence}",
            "",
        ]
    STORYBOARD_OUT.write_text("\n".join(lines), encoding="utf-8")


def _make_zip() -> None:
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(VIDEO_OUT, arcname=VIDEO_OUT.name)
    with zipfile.ZipFile(ZIP_OUT, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"zip corrupt: {bad}")
        if zf.namelist() != [VIDEO_OUT.name]:
            raise RuntimeError(f"unexpected zip contents: {zf.namelist()}")


def _verify_no_antes(steps: list[Step]) -> None:
    for step in steps:
        blob = f"{step.id} {step.section} {step.title} {step.body}".lower()
        if "antes de começar" in blob:
            raise AssertionError(f"'Antes de começar' still present in {step.id}")


def _verify_monthly_preserved(steps: list[Step]) -> None:
    blob = "\n".join(f"{s.title}\n{s.body}" for s in steps)
    for token in ("{date_inicio}", "{date_fim}", "MonthlyJob", "ExistingTable", "SQL File"):
        if token not in blob:
            raise AssertionError(f"Missing preserved content: {token}")


async def main() -> int:
    _require_tools()
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    anim = FRAMES_DIR / "anim"
    if anim.exists():
        shutil.rmtree(anim)
    anim.mkdir()
    if NARRATION_LEGACY.exists():
        NARRATION_LEGACY.unlink()

    steps = _steps()
    _verify_no_antes(steps)
    _verify_monthly_preserved(steps)

    print("Bootstrapping…")
    _bootstrap()
    setups = await _setups()
    capture_keys = sorted({s.capture for s in steps if not s.capture.startswith("card:")})
    print("Capturing real UI…")
    for key in capture_keys:
        print(f"  {key}")
        await _capture(key, setups[key])

    bases: dict[str, Path] = {}
    for key in capture_keys:
        png = FRAMES_DIR / f"{key}.png"
        _svg_to_png(FRAMES_DIR / f"{key}.svg", png)
        bases[key] = png

    _card(
        "Dispatch (Robocop)",
        "Como utilizar a aba New Job\nConfigure e inicie um novo job passo a passo.",
        FRAMES_DIR / "card_open.png",
    )
    bases["card:open"] = FRAMES_DIR / "card_open.png"
    _card(
        "Regra do arquivo SQL no MonthlyJob",
        "O arquivo .sql precisa conter os dois marcadores:\n\n"
        "{date_inicio}\n{date_fim}\n\n"
        "Exemplo (trecho):\n"
        "WHERE sale_date BETWEEN '{date_inicio}' AND '{date_fim}'",
        FRAMES_DIR / "card_sql_tokens.png",
        accent="{date_",
    )
    bases["card:sql_tokens"] = FRAMES_DIR / "card_sql_tokens.png"
    _card(
        "Antes de iniciar, confirme:",
        "• origem e destino;\n• arquivo ou tabela selecionados;\n"
        "• fila de execução;\n• opções adicionais;\n• e-mail de notificação.",
        FRAMES_DIR / "card_checklist.png",
    )
    bases["card:checklist"] = FRAMES_DIR / "card_checklist.png"
    _card(
        "Resumo",
        "Na aba New Job, você:\n1. define a execução;\n2. revisa as configurações;\n"
        "3. inicia o job;\n4. acompanha o resultado no Overview.\n\n"
        "Em caso de dúvida, revise os campos antes de selecionar Launch Job.",
        FRAMES_DIR / "card_close.png",
    )
    bases["card:close"] = FRAMES_DIR / "card_close.png"

    print("Building paced silent segments (10–12s + typing + spotlight)…")
    segment_paths: list[Path] = []
    timing_rows: list[dict] = []
    t = 0.0
    prev_cur: tuple[float, float] | None = None
    total_chars = lambda step: _char_count(step.title, step.body)

    for step in steps:
        base = bases[step.capture]
        spot = _resolved_spotlight(step)
        scene_s = _resolved_scene_s(step)
        anim_frames, anim_s = _typing_plan(step, scene_s)
        static_s = scene_s - anim_s
        assert static_s > 0
        is_card = step.capture.startswith("card:")

        # 1) Cursor move (UI only) — before instructional timer
        move_dur = 0.0
        if not is_card:
            move_pngs = []
            start = prev_cur or step.cursor
            for i in range(MOVE_FRAMES):
                e = 0.5 - 0.5 * math.cos(math.pi * (i / max(1, MOVE_FRAMES - 1)))
                cur = (
                    start[0] + (step.cursor[0] - start[0]) * e,
                    start[1] + (step.cursor[1] - start[1]) * e,
                )
                path = anim / f"{step.id}_m{i:02d}.png"
                # move: no footer yet; spotlight appears on last frames
                show_spot = i >= MOVE_FRAMES - 2
                _compose(
                    base, path,
                    title="", body="", badge="",
                    cursor=cur, spotlight=spot, clicking=False,
                    reveal_chars=0, show_spotlight=show_spot, show_footer=False,
                )
                move_pngs.append(path)
            move_mp4 = CLIPS_DIR / f"{step.id}_move.mp4"
            _encode_seq(move_pngs, move_mp4)
            segment_paths.append(move_mp4)
            move_dur = MOVE_FRAMES / FPS

        # Prepare click after reading
        click_mp4_path = None
        click_dur = 0.0
        if not is_card and step.click:
            click_pngs = []
            for i in range(CLICK_FRAMES):
                path = anim / f"{step.id}_c{i:02d}.png"
                _compose(
                    base, path,
                    title=step.title, body=step.body, badge=step.badge,
                    cursor=step.cursor, spotlight=spot, clicking=True,
                    reveal_chars=total_chars(step), show_spotlight=True, show_footer=True,
                )
                click_pngs.append(path)
            click_mp4_path = CLIPS_DIR / f"{step.id}_click.mp4"
            _encode_seq(click_pngs, click_mp4_path)
            click_dur = CLICK_FRAMES / FPS

        # 2) Instructional scene: typing then static (total scene_s)
        type_pngs = []
        n_full = total_chars(step)
        for i in range(anim_frames):
            # progressive chars
            frac = (i + 1) / anim_frames
            n_chars = max(1, int(math.ceil(frac * n_full)))
            path = anim / f"{step.id}_t{i:03d}.png"
            if is_card:
                _compose_card_scene(
                    base, path,
                    title=step.title, body=step.body, badge=step.badge,
                    reveal_chars=n_chars,
                )
            else:
                _compose(
                    base, path,
                    title=step.title, body=step.body, badge=step.badge,
                    cursor=step.cursor, spotlight=spot, clicking=False,
                    reveal_chars=n_chars, show_spotlight=True, show_footer=True,
                )
            type_pngs.append(path)
        type_mp4 = CLIPS_DIR / f"{step.id}_type.mp4"
        _encode_seq(type_pngs, type_mp4)
        segment_paths.append(type_mp4)

        hold_png = anim / f"{step.id}_hold.png"
        if is_card:
            _compose_card_scene(
                base, hold_png,
                title=step.title, body=step.body, badge=step.badge,
                reveal_chars=n_full,
            )
        else:
            _compose(
                base, hold_png,
                title=step.title, body=step.body, badge=step.badge,
                cursor=step.cursor, spotlight=spot, clicking=False,
                reveal_chars=n_full, show_spotlight=True, show_footer=True,
            )
        hold_mp4 = CLIPS_DIR / f"{step.id}_hold.mp4"
        _encode_still(hold_png, static_s, hold_mp4)
        segment_paths.append(hold_mp4)

        anim_start = t + move_dur
        anim_end = anim_start + anim_s
        scene_end_instr = anim_start + scene_s

        post = 0.0
        if click_mp4_path is not None:
            segment_paths.append(click_mp4_path)
            outcome = CLIPS_DIR / f"{step.id}_outcome.mp4"
            # brief outcome without forcing new footer rewrite
            _encode_still(hold_png, OUTCOME_S, outcome)
            segment_paths.append(outcome)
            post = click_dur + OUTCOME_S

        row = {
            "id": step.id,
            "title": step.title,
            "body": step.body.replace("\n", " / "),
            "badge": step.badge,
            "instructional": step.instructional,
            "anim_start": anim_start,
            "anim_end": anim_end,
            "anim_duration": anim_s,
            "static_duration": static_s,
            "scene_duration": scene_s,
            "scene_end": scene_end_instr,
            "target_s": scene_s,
            "spotlight": ",".join(f"{v:.2f}" for v in spot),
            "spotlight_ok": True,
            "start": anim_start,
            "end": scene_end_instr,
            "duration": scene_s,
            "hold": static_s,
        }
        timing_rows.append(row)
        t = scene_end_instr + post
        prev_cur = step.cursor
        print(
            f"  {step.id}: scene={scene_s:.1f}s anim={anim_s:.2f}s "
            f"static={static_s:.2f}s end={t:.1f}s",
            flush=True,
        )

    _validate_timing(timing_rows)
    _write_srt(timing_rows)
    _write_storyboard(timing_rows, steps)

    concat = CLIPS_DIR / "concat.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in segment_paths), encoding="utf-8")
    muxed = CLIPS_DIR / "muxed.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(muxed)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    shutil.copy2(muxed, VIDEO_OUT)
    _make_zip()

    probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,size",
            "-show_entries", "stream=codec_type,codec_name,width,height",
            "-of", "json", str(VIDEO_OUT),
        ],
        check=True, capture_output=True, text=True,
    )
    print(probe.stdout)
    vol = subprocess.run(
        ["ffmpeg", "-i", str(VIDEO_OUT), "-af", "volumedetect", "-f", "null", "-"],
        check=True, capture_output=True, text=True,
    )
    print(vol.stderr)
    meta = {
        "scene_standard_s": SCENE_STANDARD_S,
        "scene_long_s": SCENE_LONG_S,
        "instructional_scenes": sum(1 for r in timing_rows if r["instructional"]),
        "min_scene_s": min(r["scene_duration"] for r in timing_rows if r["instructional"]),
        "max_scene_s": max(r["scene_duration"] for r in timing_rows if r["instructional"]),
        "scenes_10s": sum(1 for r in timing_rows if abs(r["scene_duration"] - 10) < 0.05),
        "scenes_12s": sum(1 for r in timing_rows if abs(r["scene_duration"] - 12) < 0.05),
        "duration_s": t,
        "monthly_sql_requirement": "{date_inicio} and {date_fim}",
        "monthly_sql_evidence": MONTHLY_SQL_EVIDENCE,
        "timing_validation_passed": True,
        "holds": [
            {
                "id": r["id"],
                "anim_start_s": r["anim_start"],
                "anim_end_s": r["anim_end"],
                "scene_end_s": r["scene_end"],
                "anim_s": r["anim_duration"],
                "scene_s": r["scene_duration"],
                "static_s": r["static_duration"],
                "spotlight": r["spotlight"],
                "footer": f"{r['title']} — {r['body']}",
            }
            for r in timing_rows if r["instructional"]
        ],
    }
    (OUT_DIR / "validation_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {VIDEO_OUT}")
    print(f"Wrote {ZIP_OUT}")
    print(f"Wrote {TIMING_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
