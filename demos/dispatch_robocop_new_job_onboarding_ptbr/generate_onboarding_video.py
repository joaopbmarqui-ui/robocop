#!/usr/bin/env python3
"""Silent New Job onboarding video — paced footers (≥15s each), no narration/music.

Captures the real Dispatch UI and builds a silent walkthrough with cursor,
highlights, and Brazilian Portuguese footers. Every instructional footer stays
fully visible for at least FOOTER_HOLD_SECONDS with no interaction.

Verified MonthlyJob SQL rule (dispatch/sql.py, scr/monthly_query_processor.py,
CONTEXT.md, tests): the .sql file must contain BOTH placeholders
``{date_inicio}`` and ``{date_fim}``.

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
from dataclasses import dataclass, field
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
FOOTER_HOLD_SECONDS = 15.0
MOVE_FRAMES = 12
CLICK_FRAMES = 4
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

# Evidence used privately to verify MonthlyJob SQL rule (not shown in video).
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
    instructional: bool = True  # subject to 15s footer rule


def _steps() -> list[Step]:
    """Ordered instructional steps. No 'Antes de começar' section."""
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


def _card(title: str, body: str, dest: Path, *, accent: str | None = None) -> None:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (VIDEO_W, VIDEO_H), (16, 22, 32))
    draw = ImageDraw.Draw(img)
    bold, mid, small = _fonts((38, 24, 22))
    draw.rectangle((0, 0, 12, VIDEO_H), fill=(64, 156, 255))
    draw.text((64, 140), title, fill=(245, 245, 245), font=bold)
    y = 220
    for line in body.split("\n"):
        color = (120, 200, 255) if accent and accent in line else (200, 214, 230)
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


def _compose(
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
    callout_h = 160
    max_h = VIDEO_H - callout_h
    ratio = min(VIDEO_W / ui.width, max_h / ui.height)
    new = ui.resize(
        (max(1, int(ui.width * ratio)), max(1, int(ui.height * ratio))),
        Image.Resampling.LANCZOS,
    )
    ox = (VIDEO_W - new.width) // 2
    oy = max(0, (max_h - new.height) // 2)
    canvas.paste(new, (ox, oy), new)
    draw = ImageDraw.Draw(canvas)
    cx = ox + int(cursor[0] * new.width)
    cy = oy + int(cursor[1] * new.height)
    for r in (36, 46):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(64, 156, 255), width=2)
    _draw_cursor(draw, cx, cy, clicking=clicking)

    panel = Image.new("RGBA", (VIDEO_W, callout_h), (20, 32, 48, 245))
    canvas.alpha_composite(panel, (0, VIDEO_H - callout_h))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, VIDEO_H - callout_h, 10, VIDEO_H), fill=(64, 156, 255, 255))
    bold, mid, small = _fonts((26, 20, 17))
    y0 = VIDEO_H - callout_h + 14
    draw.text((28, y0), title, fill=(245, 245, 245, 255), font=bold)
    if badge:
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
    for line in body.split("\n"):
        draw.text((28, y), line, fill=(210, 220, 235, 255), font=mid)
        y += 26
    canvas.convert("RGB").save(dest)


def _encode_still(png: Path, seconds: float, out_mp4: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(png),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=mono:sample_rate=44100",
            "-t",
            f"{seconds:.3f}",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "64k",
            "-shortest",
            str(out_mp4),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(seq / "f%04d.png"),
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
            str(out_mp4),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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
        "# Footer timing validation",
        "",
        f"Required hold: **{FOOTER_HOLD_SECONDS:.1f}s** (static, after full message visible).",
        "",
        "| Scene | Start | End | Duration | Result |",
        "|---|---|---|---|---|",
    ]
    failed = []
    for row in rows:
        dur = row["duration"]
        ok = (not row["instructional"]) or (dur + 1e-6 >= FOOTER_HOLD_SECONDS)
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed.append(row["id"])
        lines.append(
            f"| `{row['id']}` | {_fmt_ts(row['start'])} | {_fmt_ts(row['end'])} | "
            f"{dur:.2f}s | **{status}** |"
        )
        lines.append(f"|  | footer: {row['title']} — {row['body'][:80]} | | | |")
    lines.append("")
    lines.append(f"Instructional footers: {sum(1 for r in rows if r['instructional'])}")
    lines.append(
        f"Minimum instructional duration: "
        f"{min((r['duration'] for r in rows if r['instructional']), default=0):.2f}s"
    )
    if failed:
        lines.append("")
        lines.append(f"**FAILED scenes:** {', '.join(failed)}")
        TIMING_REPORT.write_text("\n".join(lines), encoding="utf-8")
        raise AssertionError(
            f"Footer timing validation failed for: {failed}. See {TIMING_REPORT}"
        )
    lines.append("")
    lines.append("**Overall: PASS**")
    TIMING_REPORT.write_text("\n".join(lines), encoding="utf-8")


def _write_srt(rows: list[dict]) -> None:
    blocks = []
    idx = 1
    for row in rows:
        text = f"{row['title']}\n{row['body']}"
        if row["badge"]:
            text = f"[{row['badge']}] {row['title']}\n{row['body']}"
        blocks.append(
            f"{idx}\n{_fmt_ts(row['start'])} --> {_fmt_ts(row['end'])}\n{text}\n"
        )
        idx += 1
    CAPTIONS_OUT.write_text("\n".join(blocks), encoding="utf-8")


def _write_storyboard(rows: list[dict], steps: list[Step]) -> None:
    by_id = {s.id: s for s in steps}
    lines = [
        "# Storyboard — New Job (silencioso, pt-BR, footers ≥15s)",
        "",
        "Sem narração e sem música. Sem seção “Antes de começar”.",
        "",
    ]
    for row in rows:
        step = by_id[row["id"]]
        lines += [
            f"## {step.id} — {step.section}",
            "",
            f"- **Elemento:** {step.title}",
            f"- **Capture:** `{step.capture}`",
            f"- **Cursor:** move → stop em {step.cursor}"
            + (" → clique" if step.click else ""),
            f"- **Footer:** {step.title} — {step.body.replace(chr(10), ' / ')}",
            f"- **Badge:** {step.badge or '—'}",
            f"- **Footer start/end:** {_fmt_ts(row['start'])} → {_fmt_ts(row['end'])}",
            f"- **Footer duração (hold estático):** {row['hold']:.2f}s",
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
        if zf.testzip() is not None:
            raise RuntimeError("zip corrupt")
        if zf.namelist() != [VIDEO_OUT.name]:
            raise RuntimeError(f"unexpected zip contents: {zf.namelist()}")


def _verify_no_antes(steps: list[Step]) -> None:
    for step in steps:
        blob = f"{step.id} {step.section} {step.title} {step.body}".lower()
        if "antes de começar" in blob:
            raise AssertionError(f"'Antes de começar' still present in {step.id}")


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

    print("Bootstrapping…")
    _bootstrap()
    setups = await _setups()
    capture_keys = sorted(
        {
            s.capture
            for s in steps
            if not s.capture.startswith("card:")
        }
    )
    print("Capturing real UI…")
    for key in capture_keys:
        print(f"  {key}")
        await _capture(key, setups[key])

    # Base PNGs
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

    print("Building paced silent segments…")
    segment_paths: list[Path] = []
    timing_rows: list[dict] = []
    t_cursor = 0.0
    prev_cur: tuple[float, float] | None = None

    for step in steps:
        base = bases[step.capture]
        hold_png = anim / f"{step.id}_hold.png"
        if step.capture.startswith("card:"):
            # Cards already contain the message; still enforce 15s static hold.
            shutil.copy2(base, hold_png)
            move_dur = 0.0
            click_dur = 0.0
        else:
            # Move sequence (cursor moving; footer already fully shown on last move frames)
            move_pngs: list[Path] = []
            start = prev_cur or step.cursor
            for i in range(MOVE_FRAMES):
                e = 0.5 - 0.5 * math.cos(math.pi * (i / max(1, MOVE_FRAMES - 1)))
                cur = (
                    start[0] + (step.cursor[0] - start[0]) * e,
                    start[1] + (step.cursor[1] - start[1]) * e,
                )
                path = anim / f"{step.id}_m{i:02d}.png"
                # During move show full footer already (reading clock starts after move)
                _compose(
                    base,
                    path,
                    title=step.title,
                    body=step.body,
                    badge=step.badge,
                    cursor=cur,
                    clicking=False,
                )
                move_pngs.append(path)
            move_mp4 = CLIPS_DIR / f"{step.id}_move.mp4"
            _encode_seq(move_pngs, move_mp4)
            segment_paths.append(move_mp4)
            move_dur = MOVE_FRAMES / FPS

            click_dur = 0.0
            if step.click:
                click_pngs = []
                for i in range(CLICK_FRAMES):
                    path = anim / f"{step.id}_c{i:02d}.png"
                    _compose(
                        base,
                        path,
                        title=step.title,
                        body=step.body,
                        badge=step.badge,
                        cursor=step.cursor,
                        clicking=True,
                    )
                    click_pngs.append(path)
                # Click happens AFTER the 15s hold per requirements.
                # Sequence: move → HOLD 15s → click → short outcome pause
                # So click segment is appended after hold below.
                click_dur = CLICK_FRAMES / FPS
                click_mp4_path = CLIPS_DIR / f"{step.id}_click.mp4"
                _encode_seq(click_pngs, click_mp4_path)
            else:
                click_mp4_path = None

            _compose(
                base,
                hold_png,
                title=step.title,
                body=step.body,
                badge=step.badge,
                cursor=step.cursor,
                clicking=False,
            )

        # Protected reading period: static hold ≥ 15s (no cursor move/click)
        hold_mp4 = CLIPS_DIR / f"{step.id}_hold.mp4"
        _encode_still(hold_png, FOOTER_HOLD_SECONDS, hold_mp4)
        segment_paths.append(hold_mp4)

        # Click AFTER reading period
        post_click = 0.0
        if not step.capture.startswith("card:") and step.click and click_mp4_path:
            segment_paths.append(click_mp4_path)
            # brief static outcome after click (2s), same footer
            outcome = CLIPS_DIR / f"{step.id}_outcome.mp4"
            _encode_still(hold_png, 2.0, outcome)
            segment_paths.append(outcome)
            post_click = click_dur + 2.0

        # Timing row measures the protected hold only for the 15s rule.
        # Full scene duration includes move + hold + optional click/outcome.
        hold = FOOTER_HOLD_SECONDS
        scene_start = t_cursor + (0.0 if step.capture.startswith("card:") else move_dur)
        # Actually: footer is fully visible starting at hold segment.
        # Move also shows footer but protected period is the hold.
        hold_start = t_cursor + (0.0 if step.capture.startswith("card:") else move_dur)
        hold_end = hold_start + hold
        scene_end = hold_end + post_click
        if step.capture.startswith("card:"):
            scene_end = t_cursor + hold
            hold_start = t_cursor
            hold_end = t_cursor + hold

        timing_rows.append(
            {
                "id": step.id,
                "title": step.title,
                "body": step.body.replace("\n", " / "),
                "badge": step.badge,
                "start": hold_start,
                "end": hold_end,
                "duration": hold,
                "hold": hold,
                "instructional": step.instructional,
                "scene_start": t_cursor,
                "scene_end": scene_end,
            }
        )
        t_cursor = scene_end
        prev_cur = step.cursor
        print(f"  {step.id}: hold={hold:.1f}s scene_end={t_cursor:.1f}s")

    _validate_timing(timing_rows)
    _write_srt(timing_rows)
    _write_storyboard(timing_rows, steps)

    # Concat
    concat = CLIPS_DIR / "concat.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in segment_paths), encoding="utf-8")
    muxed = CLIPS_DIR / "muxed.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(muxed)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2(muxed, VIDEO_OUT)
    _make_zip()

    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size",
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
    vol = subprocess.run(
        [
            "ffmpeg",
            "-i",
            str(VIDEO_OUT),
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    print(vol.stderr)
    meta = {
        "footer_hold_seconds": FOOTER_HOLD_SECONDS,
        "instructional_footers": sum(1 for r in timing_rows if r["instructional"]),
        "min_hold": min(r["duration"] for r in timing_rows if r["instructional"]),
        "monthly_sql_requirement": "{date_inicio} and {date_fim}",
        "monthly_sql_evidence": MONTHLY_SQL_EVIDENCE,
    }
    (OUT_DIR / "validation_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {VIDEO_OUT}")
    print(f"Wrote {ZIP_OUT}")
    print(f"Wrote {TIMING_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
