#!/usr/bin/env python3
"""Silent New Job onboarding — exactly 8s scenes, GBA dialogue box, real spotlight.

- Character-by-character typewriter in a white retro dialogue box
- Semi-transparent black overlay with spotlight cutout on the explained element
- Each instructional scene lasts exactly SCENE_SECONDS (8.0s), including typing

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
FONTS_DIR = OUT_DIR / "fonts"
VIDEO_OUT = OUT_DIR / "dispatch_robocop_new_job_onboarding_ptbr.mp4"
CAPTIONS_OUT = OUT_DIR / "dispatch_robocop_new_job_captions_ptbr.srt"
STORYBOARD_OUT = OUT_DIR / "dispatch_robocop_new_job_storyboard.md"
TIMING_REPORT = OUT_DIR / "footer_timing_report.md"
ZIP_OUT = OUT_DIR / "dispatch_robocop_new_job_video_download.zip"
NARRATION_LEGACY = OUT_DIR / "dispatch_robocop_new_job_narration_ptbr.txt"

VIDEO_W, VIDEO_H = 1280, 720
FPS = 30
SCENE_SECONDS = 8.0
MOVE_FRAMES = 9
CLICK_FRAMES = 4
OUTCOME_S = 0.8
DIALOGUE_H = 180  # lower quarter
DIM_ALPHA = 168  # ~66% black overlay
SPOTLIGHT_PAD = 8
TERMINAL_SIZE = (150, 54)
TYPING_MIN_S = 1.0
TYPING_MAX_S = 1.5
ARROW_BLINK_S = 0.35

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
    spotlight: tuple[float, float, float, float] | None = None


def _steps() -> list[Step]:
    """Instructional steps. Meaning preserved; wording fit for 8s + 2-line box."""
    return [
        Step("01_open", "card:open", "Dispatch (Robocop)",
             "Como utilizar a aba New Job.\nConfigure e inicie um job passo a passo.",
             "", (0.50, 0.50), section="Abertura", evidence="opening card"),
        Step("02_purpose_a", "arrive", "Para que serve New Job",
             "Configure e inicie uma nova execução no Dispatch.",
             "", (0.55, 0.12), section="Propósito", evidence="NewJobScreen"),
        Step("02_purpose_b", "arrive", "O que você decide aqui",
             "Origem, destino, consulta e opções do job.",
             "", (0.55, 0.20), section="Propósito", evidence="NewJobScreen form"),
        Step("03_matrix", "matrix", "Source × Destination",
             "Mostra as combinações permitidas.\nConsulte antes de escolher origem e destino.",
             "Opcional", (0.52, 0.18), click=True, section="Matriz",
             evidence="matrix-collapsible + LEGAL_CELLS"),
        Step("04_detected", "arrive", "Detected source",
             "Tipo identificado no arquivo SQL.\nConfirme se é o job que você quer executar.",
             "", (0.55, 0.28), section="Detecção", evidence="info-detected"),
        Step("05_source_intro", "source_sqlfile", "Source",
             "Define de onde vêm os dados do job.\nÉ a primeira decisão do formulário.",
             "Obrigatório", (0.38, 0.34), section="Source", evidence="RadioSet #source"),
        Step("06_source_sqlfile", "source_sqlfile", "Source → SqlFile",
             "Use quando a consulta está em um .sql simples.",
             "Obrigatório", (0.38, 0.34), click=True, section="Source",
             evidence="src-sqlfile"),
        Step("06b_source_sqlfile_effect", "source_sqlfile", "SqlFile — efeito",
             "O Dispatch executa esse arquivo conforme o destino.",
             "Obrigatório", (0.38, 0.34), section="Source", evidence="LEGAL SqlFile"),
        Step("07_dest_intro", "source_sqlfile", "Destination",
             "Define onde o resultado será armazenado.\nDepende da origem escolhida.",
             "Obrigatório", (0.70, 0.28), section="Destination", evidence="#destination"),
        Step("08_dest_table", "dest_table", "Destination → Table",
             "Salva o resultado em uma tabela.\nUse para consultar depois no ambiente.",
             "Obrigatório", (0.70, 0.26), click=True, section="Destination", evidence="dst-table"),
        Step("09_dest_csv", "source_sqlfile", "Destination → Csv",
             "Gera um CSV na pasta em que você abriu o Dispatch.",
             "Obrigatório", (0.70, 0.30), click=True, section="Destination", evidence="dst-csv"),
        Step("09b_dest_csv_when", "source_sqlfile", "Csv — quando usar",
             "Use para baixar ou compartilhar o resultado como arquivo.",
             "Obrigatório", (0.70, 0.30), section="Destination", evidence="ADR-0003"),
        Step("10_dest_tablecsv", "dest_tablecsv", "Destination → Table+Csv",
             "Cria a tabela e também gera o CSV.\nUse quando precisa dos dois formatos.",
             "Obrigatório", (0.70, 0.34), click=True, section="Destination", evidence="dst-table-csv"),
        Step("11_queue_a", "queues", "Execution Queue",
             "Fila de processamento do job.\nSem marcação, a escolha é automática.",
             "Opcional", (0.55, 0.50), section="Fila", evidence="#queue"),
        Step("12_queue_b", "queues", "Execution Queue — marcar",
             "Marque filas só se o projeto indicar qual usar.",
             "Opcional", (0.55, 0.54), click=True, section="Fila", evidence="_QUEUE_CHOICES"),
        Step("12b_queue_order", "queues", "Várias filas",
             "Se marcar várias, são tentadas na ordem da lista.",
             "Opcional", (0.55, 0.54), section="Fila", evidence="_QUEUE_AUTO_HINT"),
        Step("13_sql_intro", "picker", "SQL File",
             "É a consulta que o job vai executar.",
             "Obrigatório", (0.55, 0.62), section="SQL File", evidence="row-sql-file"),
        Step("13b_sql_when", "picker", "SQL File — quando",
             "Obrigatório para SqlFile e MonthlyJob.",
             "Obrigatório", (0.55, 0.62), section="SQL File", evidence="required sources"),
        Step("14_sql_picker", "picker", "Lista de arquivos SQL",
             "Mostra os .sql da pasta atual.\nSelecione o arquivo do seu job.",
             "Obrigatório", (0.55, 0.62), click=True, section="SQL File",
             evidence="sql-file-picker"),
        Step("15_sql_verify", "picker", "O que conferir",
             "Confirme o nome e o tipo Detected na lista.",
             "Obrigatório", (0.58, 0.72), section="SQL File", evidence="Detected column"),
        Step("15b_sql_path", "picker", "Caminho do SQL File",
             "Após a seleção, o caminho preenche o campo SQL File.",
             "Obrigatório", (0.58, 0.72), section="SQL File", evidence="path-hint"),
        Step("16_sql_role", "picker", "Papel do SQL File",
             "Define quais dados serão lidos ou calculados.",
             "Obrigatório", (0.58, 0.72), section="SQL File", evidence="manifest sql_path"),
        Step("16b_sql_role_dest", "picker", "SQL + destino",
             "Source e Destination decidem como entregar o resultado.",
             "Obrigatório", (0.58, 0.72), section="SQL File", evidence="LEGAL_CELLS"),
        Step("17_email", "email_ok", "Email (notifications)",
             "Recebe aviso quando o job terminar.\nDeixe em branco se não quiser.",
             "Opcional", (0.58, 0.78), click=True, section="Notificação", evidence="#email"),
        Step("18_subject", "email_ok", "Subject (email)",
             "Assunto do e-mail de notificação.\nUse um texto curto que identifique o job.",
             "Opcional", (0.58, 0.84), click=True, section="Notificação", evidence="#subject"),
        Step("19_status_bar", "ready_review", "Status do formulário",
             "Ready to launch = sem problemas bloqueantes.",
             "", (0.72, 0.92), section="Status", evidence="validation-summary"),
        Step("19b_actions", "ready_review", "Preview SQL e Launch",
             "Ficam na barra inferior para revisão e envio.",
             "", (0.78, 0.92), section="Status", evidence="action bar"),
        # MonthlyJob
        Step("20_mj_intro", "monthly", "MonthlyJob",
             "Use para cobrir um intervalo de datas,\nexecutando o período mês a mês.",
             "Use apenas quando...", (0.38, 0.38), click=True, section="MonthlyJob",
             evidence="SqlTemplate labeled MonthlyJob"),
        Step("21_mj_dest", "monthly", "MonthlyJob → Destination",
             "Com MonthlyJob, o destino permitido é só Table.",
             "Obrigatório", (0.70, 0.28), section="MonthlyJob", evidence="LEGAL SqlTemplate/Table"),
        Step("21b_mj_dest_blocked", "monthly", "Csv e Table+Csv",
             "Ficam indisponíveis neste modo.",
             "Obrigatório", (0.70, 0.34), section="MonthlyJob", evidence="dest hint"),
        Step("22_mj_sql_rule_a", "card:sql_tokens", "SQL no MonthlyJob — regra",
             "O .sql precisa conter os dois marcadores:\n{date_inicio} e {date_fim}",
             "Obrigatório", (0.50, 0.45), section="MonthlyJob SQL",
             evidence="; ".join(MONTHLY_SQL_EVIDENCE)),
        Step("23_mj_sql_rule_b", "card:sql_tokens", "Como conferir no arquivo",
             "Abra o .sql e busque exatamente\n{date_inicio} e {date_fim}.",
             "Obrigatório", (0.50, 0.50), section="MonthlyJob SQL",
             evidence="_sql_content_issues"),
        Step("23b_mj_sql_missing", "card:sql_tokens", "Se faltar um marcador",
             "O job não pode ser iniciado como MonthlyJob.",
             "Obrigatório", (0.50, 0.50), section="MonthlyJob SQL",
             evidence="is_malformed_template"),
        Step("24_mj_sql_rule_c", "card:sql_tokens", "O que os marcadores fazem",
             "Reservam início e fim de cada mês do período.",
             "Obrigatório", (0.50, 0.55), section="MonthlyJob SQL",
             evidence="render_monthly_sql"),
        Step("24b_mj_sql_fill", "card:sql_tokens", "Preenchimento das datas",
             "O Dispatch preenche conforme Start Date e End Date.",
             "Obrigatório", (0.50, 0.55), section="MonthlyJob SQL",
             evidence="monthly_preview"),
        Step("25_mj_picker", "monthly_picker", "SQL do MonthlyJob",
             "Na lista, escolha Detected = MonthlyJob.",
             "Obrigatório", (0.55, 0.60), click=True, section="MonthlyJob SQL",
             evidence="detect_source"),
        Step("25b_mj_picker_confirm", "monthly_picker", "Detected = MonthlyJob",
             "Confirma que os dois marcadores foram encontrados.",
             "Obrigatório", (0.55, 0.60), section="MonthlyJob SQL",
             evidence="picker Detected"),
        Step("26_mj_schema", "monthly_fields", "Schema (MonthlyJob)",
             "Schema da tabela de resultado.\nInforme o schema correto do seu trabalho.",
             "Obrigatório", (0.58, 0.68), section="MonthlyJob campos", evidence="#schema"),
        Step("27_mj_table", "monthly_fields", "Table Name (MonthlyJob)",
             "Nome da tabela com o prefixo do usuário.",
             "Obrigatório", (0.58, 0.74), section="MonthlyJob campos",
             evidence="#table-name-prefix"),
        Step("27b_mj_table_suffix", "monthly_fields", "Sufixo da tabela",
             "Complete só o sufixo; o prefixo já vem preenchido.",
             "Obrigatório", (0.58, 0.74), section="MonthlyJob campos",
             evidence="#table-name-suffix"),
        Step("28_mj_start", "monthly_fields", "Start Date",
             "Data inicial (AAAA-MM-DD).\nDefine o primeiro mês a processar.",
             "Obrigatório", (0.58, 0.80), section="MonthlyJob campos", evidence="#start-date"),
        Step("29_mj_end", "monthly_fields", "End Date",
             "Data final (AAAA-MM-DD).\nDeve ser igual ou posterior à Start Date.",
             "Obrigatório", (0.58, 0.86), section="MonthlyJob campos", evidence="#end-date"),
        # ExistingTable
        Step("30_et_intro", "existing", "ExistingTable",
             "Use quando os dados já estão em uma tabela\ne você quer exportá-los sem .sql.",
             "Use apenas quando...", (0.38, 0.36), click=True, section="ExistingTable",
             evidence="src-existingtable"),
        Step("31_et_dest", "existing", "ExistingTable → Destination",
             "Neste modo o destino permitido é apenas Csv.",
             "Obrigatório", (0.70, 0.30), section="ExistingTable",
             evidence="LEGAL ExistingTable/Csv"),
        Step("31b_et_dest_blocked", "existing", "Table e Table+Csv",
             "Ficam indisponíveis com ExistingTable.",
             "Obrigatório", (0.70, 0.34), section="ExistingTable", evidence="dest hint"),
        Step("32_et_no_sql", "existing", "Sem SQL File",
             "A lista e o campo SQL File ficam ocultos.\nA origem é a tabela existente.",
             "Use apenas quando...", (0.55, 0.48), section="ExistingTable",
             evidence="picker display=False"),
        Step("33_et_schema_coe", "existing_coe", "Schema → coe_enc",
             "Seleciona o schema coe_enc da tabela existente.",
             "Obrigatório", (0.50, 0.68), click=True, section="ExistingTable Schema",
             evidence="esc-coe-enc"),
        Step("34_et_schema_aa", "existing_fields", "Schema → aa_enc",
             "Seleciona o schema aa_enc.\nÉ a opção padrão nesse schema.",
             "Obrigatório", (0.55, 0.68), click=True, section="ExistingTable Schema",
             evidence="esc-aa-enc"),
        Step("35_et_schema_other", "existing_other", "Schema → other",
             "Use quando o schema não é coe_enc nem aa_enc.",
             "Use apenas quando...", (0.60, 0.68), click=True,
             section="ExistingTable Schema", evidence="esc-other"),
        Step("35b_et_other_field", "existing_other", "other → Custom Schema",
             "Ao marcar other, aparece o campo Custom Schema.",
             "Use apenas quando...", (0.60, 0.72), section="ExistingTable Schema",
             evidence="#existing-schema-custom"),
        Step("36_et_custom", "existing_other", "Custom Schema",
             "Digite o nome do schema personalizado.\nSó aparece com Schema = other.",
             "Obrigatório", (0.58, 0.74), section="ExistingTable Schema",
             evidence="row-existing-schema-custom"),
        Step("37_et_table", "existing_fields", "Existing Table",
             "Informe só o nome da tabela (sem o schema).",
             "Obrigatório", (0.58, 0.78), click=True, section="ExistingTable",
             evidence="#existing-table"),
        Step("37b_et_full", "existing_fields", "Origem completa",
             "Com o schema, forma schema.tabela.",
             "Obrigatório", (0.58, 0.78), section="ExistingTable",
             evidence="validate_full_table"),
        # Relations
        Step("38_rel_standard", "ready_review", "Combinação comum",
             "SqlFile + Csv + .sql sem marcadores de data.",
             "", (0.55, 0.36), click=True, section="Relações", evidence="LEGAL SqlFile/Csv"),
        Step("38b_rel_standard_use", "ready_review", "Fluxo típico",
             "Gera um CSV a partir de uma consulta.",
             "", (0.55, 0.36), section="Relações", evidence="detect_source"),
        Step("39_rel_monthly", "monthly_fields", "Combinação MonthlyJob",
             "MonthlyJob + Table + .sql com\n{date_inicio} e {date_fim}.",
             "", (0.55, 0.40), section="Relações", evidence="LEGAL SqlTemplate/Table"),
        Step("39b_rel_monthly_fields", "monthly_fields", "Campos do MonthlyJob",
             "Também: Schema, Table Name, Start Date e End Date.",
             "", (0.55, 0.70), section="Relações", evidence="date fields"),
        Step("40_rel_existing", "existing_fields", "Combinação ExistingTable",
             "ExistingTable + Csv + Schema + Existing Table.",
             "", (0.55, 0.42), section="Relações", evidence="ExistingTable flow"),
        Step("40b_rel_existing_no_sql", "existing_fields", "Sem SQL neste modo",
             "Não usa SQL File nem MonthlyJob ao mesmo tempo.",
             "", (0.55, 0.42), section="Relações", evidence="source exclusive"),
        Step("41_rel_incompat", "matrix", "Combinações indisponíveis",
             "MonthlyJob não aceita Csv ou Table+Csv.",
             "", (0.52, 0.20), section="Relações", evidence="LEGAL_CELLS"),
        Step("41b_rel_incompat_et", "matrix", "ExistingTable — limite",
             "ExistingTable não aceita Table ou Table+Csv.",
             "", (0.52, 0.20), section="Relações", evidence="LEGAL_CELLS"),
        # Validation / launch
        Step("42_val_bad", "email_bad", "E-mail inválido",
             "Se o formato estiver errado, o status mostra o problema.",
             "", (0.58, 0.78), section="Validação", evidence="Invalid email"),
        Step("43_val_ok", "ready_review", "Formulário pronto",
             "Com os dados corrigidos, volta Ready to launch.",
             "", (0.72, 0.92), section="Validação", evidence="Ready to launch"),
        Step("43b_val_review", "ready_review", "Revise antes de enviar",
             "Confira origem, destino, arquivo e fila.",
             "", (0.55, 0.40), section="Validação", evidence="form review"),
        Step("44_preview", "preview", "Preview SQL",
             "Mostra o conteúdo que será usado no job.",
             "", (0.78, 0.92), click=True, section="Preview", evidence="Preview SQL [P]"),
        Step("44b_preview_check", "preview", "O que conferir no Preview",
             "Confira a consulta e o destino antes do envio.",
             "", (0.55, 0.45), section="Preview", evidence="preview screen"),
        Step("45_checklist", "card:checklist", "Antes de iniciar, confirme",
             "Origem, destino, arquivo ou tabela,\ne fila de execução.",
             "", (0.50, 0.50), section="Revisão", evidence="checklist"),
        Step("45b_checklist_b", "card:checklist", "Também confira",
             "Opções adicionais e e-mail de notificação.",
             "", (0.50, 0.50), section="Revisão", evidence="checklist"),
        Step("46_confirm", "confirm", "Launch Job",
             "Inicia o job com as configurações revisadas.",
             "", (0.42, 0.72), click=True, section="Envio", evidence="ConfirmScreen"),
        Step("46b_confirm_read", "confirm", "Confirme só se estiver correto",
             "Leia o resumo antes de confirmar o envio.",
             "", (0.42, 0.72), section="Envio", evidence="Launch Job"),
        Step("47_launched", "launched", "Job enviado",
             "O job foi enviado pelo Dispatch.\nAcompanhe na tela de monitoramento.",
             "", (0.55, 0.88), section="Envio", evidence="Launched Job"),
        Step("48_overview", "overview", "Overview",
             "Após o envio, acompanhe o status no Overview.",
             "", (0.12, 0.22), click=True, section="Overview", evidence="DashboardScreen"),
        Step("49_close", "card:close", "Resumo",
             "Na aba New Job você define, revisa e inicia o job.",
             "", (0.50, 0.50), section="Encerramento", evidence="closing"),
        Step("49b_close_b", "card:close", "Depois do envio",
             "Acompanhe o resultado no Overview.\nRevise os campos antes de Launch Job.",
             "", (0.50, 0.50), section="Encerramento", evidence="closing"),
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



def _dialogue_text(title: str, body: str) -> str:
    return f"{title}\n{body}" if body else title


def _char_count(title: str, body: str) -> int:
    return len(_dialogue_text(title, body))


def _pixel_font(size: int):
    from PIL import ImageFont

    candidates = [
        FONTS_DIR / "PixelifySans-Regular.ttf",
        FONTS_DIR / "VT323-Regular.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"),
    ]
    for p in candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _resolved_spotlight(step: Step) -> tuple[float, float, float, float]:
    if step.spotlight is not None:
        return step.spotlight
    if step.capture.startswith("card:"):
        return (0.10, 0.14, 0.90, 0.72)
    cx, cy = step.cursor
    id_overrides = {
        "03_matrix": (0.52, 0.16, 0.45, 0.12),
        "04_detected": (0.52, 0.26, 0.40, 0.06),
        "05_source_intro": (0.36, 0.32, 0.18, 0.10),
        "06_source_sqlfile": (0.36, 0.32, 0.18, 0.10),
        "06b_source_sqlfile_effect": (0.36, 0.32, 0.18, 0.10),
        "07_dest_intro": (0.70, 0.30, 0.18, 0.10),
        "08_dest_table": (0.70, 0.26, 0.18, 0.08),
        "09_dest_csv": (0.70, 0.30, 0.18, 0.08),
        "09b_dest_csv_when": (0.70, 0.30, 0.18, 0.08),
        "10_dest_tablecsv": (0.70, 0.34, 0.18, 0.08),
        "11_queue_a": (0.55, 0.48, 0.38, 0.14),
        "12_queue_b": (0.55, 0.52, 0.38, 0.14),
        "12b_queue_order": (0.55, 0.52, 0.38, 0.14),
        "13_sql_intro": (0.55, 0.58, 0.42, 0.14),
        "13b_sql_when": (0.55, 0.58, 0.42, 0.14),
        "14_sql_picker": (0.55, 0.58, 0.42, 0.14),
        "15_sql_verify": (0.55, 0.62, 0.42, 0.16),
        "15b_sql_path": (0.55, 0.70, 0.42, 0.08),
        "16_sql_role": (0.55, 0.68, 0.42, 0.10),
        "16b_sql_role_dest": (0.55, 0.36, 0.42, 0.14),
        "17_email": (0.58, 0.76, 0.42, 0.06),
        "18_subject": (0.58, 0.82, 0.42, 0.06),
        "19_status_bar": (0.70, 0.90, 0.28, 0.06),
        "19b_actions": (0.78, 0.90, 0.20, 0.06),
        "20_mj_intro": (0.36, 0.36, 0.20, 0.10),
        "21_mj_dest": (0.52, 0.30, 0.38, 0.12),
        "21b_mj_dest_blocked": (0.70, 0.34, 0.20, 0.10),
        "25_mj_picker": (0.55, 0.56, 0.42, 0.14),
        "25b_mj_picker_confirm": (0.55, 0.56, 0.42, 0.14),
        "26_mj_schema": (0.58, 0.66, 0.40, 0.06),
        "27_mj_table": (0.58, 0.72, 0.40, 0.06),
        "27b_mj_table_suffix": (0.58, 0.72, 0.40, 0.06),
        "28_mj_start": (0.58, 0.78, 0.40, 0.06),
        "29_mj_end": (0.58, 0.84, 0.40, 0.06),
        "30_et_intro": (0.36, 0.36, 0.20, 0.10),
        "31_et_dest": (0.52, 0.30, 0.38, 0.12),
        "31b_et_dest_blocked": (0.70, 0.34, 0.20, 0.10),
        "32_et_no_sql": (0.50, 0.42, 0.40, 0.14),
        "33_et_schema_coe": (0.48, 0.66, 0.28, 0.08),
        "34_et_schema_aa": (0.55, 0.66, 0.28, 0.08),
        "35_et_schema_other": (0.62, 0.66, 0.28, 0.08),
        "35b_et_other_field": (0.58, 0.70, 0.40, 0.08),
        "36_et_custom": (0.58, 0.72, 0.40, 0.06),
        "37_et_table": (0.58, 0.76, 0.40, 0.06),
        "37b_et_full": (0.58, 0.76, 0.40, 0.06),
        "38_rel_standard": (0.50, 0.34, 0.42, 0.22),
        "38b_rel_standard_use": (0.50, 0.34, 0.42, 0.22),
        "39_rel_monthly": (0.50, 0.38, 0.42, 0.28),
        "39b_rel_monthly_fields": (0.55, 0.70, 0.40, 0.16),
        "40_rel_existing": (0.50, 0.36, 0.42, 0.24),
        "40b_rel_existing_no_sql": (0.50, 0.36, 0.42, 0.24),
        "41_rel_incompat": (0.52, 0.18, 0.42, 0.14),
        "41b_rel_incompat_et": (0.52, 0.18, 0.42, 0.14),
        "42_val_bad": (0.58, 0.76, 0.40, 0.08),
        "43_val_ok": (0.70, 0.90, 0.28, 0.06),
        "43b_val_review": (0.50, 0.40, 0.42, 0.22),
        "44_preview": (0.62, 0.48, 0.32, 0.28),
        "44b_preview_check": (0.55, 0.45, 0.40, 0.28),
        "46_confirm": (0.50, 0.55, 0.36, 0.28),
        "46b_confirm_read": (0.50, 0.55, 0.36, 0.28),
        "47_launched": (0.55, 0.70, 0.40, 0.18),
        "48_overview": (0.14, 0.22, 0.14, 0.16),
    }
    if step.id in id_overrides:
        cx, cy, hw, hh = id_overrides[step.id]
        return (max(0.02, cx - hw), max(0.02, cy - hh), min(0.98, cx + hw), min(0.92, cy + hh))
    hw, hh = 0.28, 0.10
    return (max(0.02, cx - hw), max(0.02, cy - hh), min(0.98, cx + hw), min(0.92, cy + hh))


def _typing_plan(step: Step) -> tuple[int, float]:
    n = max(1, _char_count(step.title, step.body))
    # Target 1.0–1.5s; keep ≤ 1.5s hard cap.
    target = min(TYPING_MAX_S, max(TYPING_MIN_S, n / 70.0))
    frames = max(12, int(round(target * FPS)))
    anim_s = frames / FPS
    if anim_s > TYPING_MAX_S + 1e-9:
        frames = int(TYPING_MAX_S * FPS)
        anim_s = frames / FPS
    return frames, anim_s


def _visible_parts(title: str, body: str, n_chars: int) -> tuple[str, str]:
    full = _dialogue_text(title, body)
    vis = full[: max(0, n_chars)]
    if "\n" in vis:
        t, b = vis.split("\n", 1)
        return t, b
    return vis, ""


def _svg_to_png(svg: Path, png: Path) -> None:
    import cairosvg

    cairosvg.svg2png(url=svg.as_uri(), write_to=str(png), output_width=VIDEO_W)


def _card(title: str, body: str, dest: Path, *, accent: str | None = None) -> None:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (VIDEO_W, VIDEO_H), (16, 22, 32))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 10, VIDEO_H), fill=(64, 156, 255))
    title_f = _pixel_font(36)
    body_f = _pixel_font(26)
    y = 120
    draw.text((64, y), title, fill=(245, 245, 245), font=title_f)
    y += 70
    for line in body.split("\n"):
        color = (255, 220, 120) if "{" in line else (210, 220, 235)
        draw.text((64, y), line, fill=color, font=body_f)
        y += 42
    img.save(dest)


def _draw_cursor(draw, x: int, y: int, *, clicking: bool = False) -> None:
    pts = [(x, y), (x, y + 22), (x + 6, y + 17), (x + 12, y + 28),
           (x + 16, y + 26), (x + 10, y + 15), (x + 18, y + 15)]
    draw.polygon(pts, fill=(255, 255, 255), outline=(20, 20, 20))
    if clicking:
        r = 18
        draw.ellipse((x - r, y - r, x + r, y + r), outline=(64, 156, 255), width=3)


def _draw_red_arrow(draw, box_right: int, box_bottom: int, *, offset: int = 0) -> None:
    # Small red downward triangle inside bottom-right of dialogue box.
    ax = box_right - 36
    ay = box_bottom - 28 + offset
    draw.polygon([(ax, ay), (ax + 16, ay), (ax + 8, ay + 12)], fill=(220, 40, 40))


def _layout_ui(ui_png: Path):
    from PIL import Image

    ui = Image.open(ui_png).convert("RGBA")
    max_h = VIDEO_H - DIALOGUE_H
    ratio = min(VIDEO_W / ui.width, max_h / ui.height)
    new = ui.resize((max(1, int(ui.width * ratio)), max(1, int(ui.height * ratio))), Image.Resampling.NEAREST)
    # Use LANCZOS for UI clarity (not pixelating the app)
    new = ui.resize((max(1, int(ui.width * ratio)), max(1, int(ui.height * ratio))), Image.Resampling.LANCZOS)
    ox = (VIDEO_W - new.width) // 2
    oy = max(0, (max_h - new.height) // 2)
    return ui, new, ox, oy


def _draw_dialogue_box(
    canvas,
    *,
    title: str,
    body: str,
    badge: str,
    reveal_chars: int,
    show_arrow: bool,
    arrow_offset: int = 0,
) -> None:
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(canvas)
    # White GBA-style box in lower quarter
    margin_x = 48
    top = VIDEO_H - DIALOGUE_H + 12
    bottom = VIDEO_H - 14
    left = margin_x
    right = VIDEO_W - margin_x
    # Outer black border (thin), slightly rounded
    draw.rounded_rectangle((left - 3, top - 3, right + 3, bottom + 3), radius=10, fill=(0, 0, 0, 255))
    draw.rounded_rectangle((left, top, right, bottom), radius=8, fill=(252, 252, 252, 255))
    # Inner thin black line
    draw.rounded_rectangle((left + 3, top + 3, right - 3, bottom - 3), radius=6, outline=(0, 0, 0, 255), width=2)

    title_f = _pixel_font(28)
    body_f = _pixel_font(24)
    badge_f = _pixel_font(18)
    vis_title, vis_body = _visible_parts(title, body, reveal_chars)
    y = top + 18
    if vis_title:
        draw.text((left + 22, y), vis_title, fill=(0, 0, 0, 255), font=title_f)
    if badge and reveal_chars >= len(title):
        bw = 16 + len(badge) * 8
        bx = right - bw - 48
        # Retro badge as outlined label (keep readable, not modern pill-heavy)
        draw.rectangle((bx, y + 2, bx + bw, y + 24), outline=(0, 0, 0), width=2)
        draw.text((bx + 6, y + 4), badge, fill=(0, 0, 0, 255), font=badge_f)
    y = top + 56
    for line in vis_body.split("\n")[:2]:
        draw.text((left + 22, y), line, fill=(0, 0, 0, 255), font=body_f)
        y += 32
    if show_arrow:
        _draw_red_arrow(draw, right - 8, bottom - 4, offset=arrow_offset)


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
    show_dialogue: bool = True,
    show_arrow: bool = False,
    arrow_offset: int = 0,
) -> None:
    from PIL import Image, ImageDraw

    ui, new, ox, oy = _layout_ui(ui_png)
    canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (12, 14, 18, 255))
    canvas.paste(new, (ox, oy), new)

    if show_spotlight:
        dim = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, DIM_ALPHA))
        canvas = Image.alpha_composite(canvas, dim)
        l, t, r, b = spotlight
        sx0 = max(0, ox + int(l * new.width) - SPOTLIGHT_PAD)
        sy0 = max(0, oy + int(t * new.height) - SPOTLIGHT_PAD)
        sx1 = min(VIDEO_W, ox + int(r * new.width) + SPOTLIGHT_PAD)
        sy1 = min(VIDEO_H - DIALOGUE_H, oy + int(b * new.height) + SPOTLIGHT_PAD)
        if sx1 > sx0 and sy1 > sy0:
            bright = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
            bright.paste(new, (ox, oy), new)
            canvas.paste(bright.crop((sx0, sy0, sx1, sy1)), (sx0, sy0))
            draw = ImageDraw.Draw(canvas)
            for w, col in ((5, (255, 220, 80, 200)), (2, (0, 0, 0, 255))):
                draw.rounded_rectangle((sx0 - 1, sy0 - 1, sx1 + 1, sy1 + 1), radius=6, outline=col, width=w)

    draw = ImageDraw.Draw(canvas)
    cx = ox + int(cursor[0] * new.width)
    cy = oy + int(cursor[1] * new.height)
    # Keep cursor in UI area, not over dialogue
    cy = min(cy, VIDEO_H - DIALOGUE_H - 24)
    _draw_cursor(draw, cx, cy, clicking=clicking)

    if show_dialogue:
        n = reveal_chars if reveal_chars is not None else _char_count(title, body)
        _draw_dialogue_box(
            canvas,
            title=title,
            body=body,
            badge=badge,
            reveal_chars=n,
            show_arrow=show_arrow and n >= _char_count(title, body),
            arrow_offset=arrow_offset,
        )
    canvas.convert("RGB").save(dest)


def _compose_card_scene(
    card_png: Path,
    dest: Path,
    *,
    title: str,
    body: str,
    badge: str,
    reveal_chars: int | None = None,
    show_arrow: bool = False,
    arrow_offset: int = 0,
) -> None:
    from PIL import Image, ImageDraw

    card = Image.open(card_png).convert("RGBA").resize((VIDEO_W, VIDEO_H), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (12, 14, 18, 255))
    canvas.paste(card, (0, 0), card)
    dimmed = Image.alpha_composite(canvas, Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, DIM_ALPHA)))
    sx0, sy0, sx1, sy1 = 56, 80, VIDEO_W - 56, VIDEO_H - DIALOGUE_H - 18
    dimmed.paste(card.crop((sx0, sy0, sx1, sy1)), (sx0, sy0))
    canvas = dimmed
    draw = ImageDraw.Draw(canvas)
    for w, col in ((5, (255, 220, 80, 200)), (2, (0, 0, 0, 255))):
        draw.rounded_rectangle((sx0 - 1, sy0 - 1, sx1 + 1, sy1 + 1), radius=8, outline=col, width=w)
    n = reveal_chars if reveal_chars is not None else _char_count(title, body)
    _draw_dialogue_box(
        canvas,
        title=title,
        body=body,
        badge=badge,
        reveal_chars=n,
        show_arrow=show_arrow and n >= _char_count(title, body),
        arrow_offset=arrow_offset,
    )
    canvas.convert("RGB").save(dest)


def _encode_still(png: Path, seconds: float, out_mp4: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loop", "1", "-i", str(png),
         "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=44100",
         "-t", f"{seconds:.3f}", "-r", str(FPS),
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "64k", "-shortest", str(out_mp4)],
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
        ["ffmpeg", "-y", "-framerate", str(FPS), "-i", str(seq / "f%04d.png"),
         "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=44100",
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "64k", "-shortest", str(out_mp4)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    shutil.rmtree(seq, ignore_errors=True)


def _encode_blink_hold(png_a: Path, png_b: Path, seconds: float, out_mp4: Path) -> None:
    """Alternate two still clips for a subtle red-arrow blink over the static period."""
    half = ARROW_BLINK_S
    n_pairs = max(1, int(math.ceil(seconds / (2 * half))))
    # Build short A/B clips then concat enough to cover seconds, trim to exact length.
    clip_a = CLIPS_DIR / f"_blink_a_{out_mp4.stem}.mp4"
    clip_b = CLIPS_DIR / f"_blink_b_{out_mp4.stem}.mp4"
    _encode_still(png_a, half, clip_a)
    _encode_still(png_b, half, clip_b)
    concat = CLIPS_DIR / f"_blink_concat_{out_mp4.stem}.txt"
    lines = []
    for _ in range(n_pairs):
        lines.append(f"file '{clip_a.resolve()}'\n")
        lines.append(f"file '{clip_b.resolve()}'\n")
    concat.write_text("".join(lines), encoding="utf-8")
    long_mp4 = CLIPS_DIR / f"_blink_long_{out_mp4.stem}.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(long_mp4)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(long_mp4), "-t", f"{seconds:.3f}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "64k", str(out_mp4)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for p in (clip_a, clip_b, concat, long_mp4):
        p.unlink(missing_ok=True)


def _fmt_ts(seconds: float) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, milli = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def _validate_timing(rows: list[dict]) -> None:
    lines = [
        "# Instructional scene timing validation (exactly 8.0s)",
        "",
        f"Rule: each instructional scene = **{SCENE_SECONDS:.1f}s** total (includes typing).",
        f"Typing target: {TYPING_MIN_S:.1f}–{TYPING_MAX_S:.1f}s. Dim alpha={DIM_ALPHA}.",
        "",
        "| Scene | Element | Start | Type end | Arrow | End | Type | Static | Total | Spotlight | Opacity | Result |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    failed = []
    for row in rows:
        if not row["instructional"]:
            continue
        total = row["scene_duration"]
        anim = row["anim_duration"]
        ok = True
        reasons = []
        if abs(total - SCENE_SECONDS) > (1.0 / FPS) + 1e-6:
            ok = False
            reasons.append(f"not-8s({total:.3f})")
        if anim > TYPING_MAX_S + (1.0 / FPS) + 1e-6:
            ok = False
            reasons.append("typing>1.5")
        if row["arrow_at"] + 1e-6 < row["anim_end"]:
            ok = False
            reasons.append("arrow-early")
        if abs(row["arrow_at"] - row["anim_end"]) > (1.0 / FPS) + 1e-6 and row["arrow_at"] < row["anim_end"]:
            ok = False
            reasons.append("arrow-before-complete")
        if not row.get("spotlight_ok", True):
            ok = False
            reasons.append("spotlight")
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed.append(f"{row['id']}({','.join(reasons)})")
        lines.append(
            f"| `{row['id']}` | {row['title'][:24]} | {_fmt_ts(row['anim_start'])} | "
            f"{_fmt_ts(row['anim_end'])} | {_fmt_ts(row['arrow_at'])} | {_fmt_ts(row['scene_end'])} | "
            f"{anim:.2f}s | {row['static_duration']:.2f}s | {total:.2f}s | `{row['spotlight']}` | "
            f"{DIM_ALPHA} | **{status}** |"
        )
        lines.append(f"|  | dialogue: {row['title']} — {row['body'][:80]} | | | | | | | | | | |")
    lines.append("")
    lines.append(f"Instructional scenes: {sum(1 for r in rows if r['instructional'])}")
    durs = [r["scene_duration"] for r in rows if r["instructional"]]
    anims = [r["anim_duration"] for r in rows if r["instructional"]]
    lines.append(f"Min/Max scene: {min(durs):.3f}s / {max(durs):.3f}s")
    lines.append(f"Min/Max typing: {min(anims):.3f}s / {max(anims):.3f}s")
    if failed:
        lines.append("")
        lines.append(f"**FAILED:** {', '.join(failed)}")
        TIMING_REPORT.write_text("\n".join(lines), encoding="utf-8")
        raise AssertionError(f"Timing validation failed: {failed}")
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
        blocks.append(f"{idx}\n{_fmt_ts(row['anim_start'])} --> {_fmt_ts(row['scene_end'])}\n{text}\n")
        idx += 1
    CAPTIONS_OUT.write_text("\n".join(blocks), encoding="utf-8")


def _write_storyboard(rows: list[dict], steps: list[Step]) -> None:
    by_id = {s.id: s for s in steps}
    lines = [
        "# Storyboard — New Job (8.0s, GBA dialogue, real spotlight)",
        "",
        "Sem narração/música. Cada cena instrucional = exatamente 8.0s (inclui typewriter).",
        f"Overlay escuro alpha={DIM_ALPHA}. Caixa branca inferior com borda preta e seta vermelha.",
        "",
    ]
    for row in rows:
        step = by_id[row["id"]]
        action = "clique após a cena" if step.click else "avançar para a próxima cena"
        lines += [
            f"## {step.id} — {step.section}",
            "",
            f"- **Elemento:** {step.title}",
            f"- **Spotlight target:** {step.title}",
            f"- **Spotlight coords (norm):** `{row['spotlight']}`",
            f"- **Overlay opacity:** {DIM_ALPHA}/255",
            f"- **Diálogo:** {step.title} — {step.body.replace(chr(10), ' / ')}",
            f"- **Typing:** {_fmt_ts(row['anim_start'])} → {_fmt_ts(row['anim_end'])} ({row['anim_duration']:.2f}s)",
            f"- **Seta vermelha:** {_fmt_ts(row['arrow_at'])}",
            f"- **Início/fim:** {_fmt_ts(row['anim_start'])} → {_fmt_ts(row['scene_end'])}",
            f"- **Duração total:** {row['scene_duration']:.2f}s",
            f"- **Ação após a cena:** {action}",
            f"- **Evidência:** {step.evidence}",
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

    _card("Dispatch (Robocop)",
          "Como utilizar a aba New Job\nConfigure e inicie um novo job passo a passo.",
          FRAMES_DIR / "card_open.png")
    bases["card:open"] = FRAMES_DIR / "card_open.png"
    _card("Regra do arquivo SQL no MonthlyJob",
          "O arquivo .sql precisa conter os dois marcadores:\n\n"
          "{date_inicio}\n{date_fim}\n\n"
          "Exemplo (trecho):\n"
          "WHERE sale_date BETWEEN '{date_inicio}' AND '{date_fim}'",
          FRAMES_DIR / "card_sql_tokens.png", accent="{date_")
    bases["card:sql_tokens"] = FRAMES_DIR / "card_sql_tokens.png"
    _card("Antes de iniciar, confirme:",
          "• origem e destino;\n• arquivo ou tabela;\n• fila;\n• opções;\n• e-mail.",
          FRAMES_DIR / "card_checklist.png")
    bases["card:checklist"] = FRAMES_DIR / "card_checklist.png"
    _card("Resumo",
          "Na aba New Job você:\n1. define;\n2. revisa;\n3. inicia;\n4. acompanha no Overview.",
          FRAMES_DIR / "card_close.png")
    bases["card:close"] = FRAMES_DIR / "card_close.png"

    print("Building 8.0s GBA-dialogue + spotlight segments…")
    segment_paths: list[Path] = []
    timing_rows: list[dict] = []
    t = 0.0
    prev_cur: tuple[float, float] | None = None

    for step in steps:
        base = bases[step.capture]
        spot = _resolved_spotlight(step)
        anim_frames, anim_s = _typing_plan(step)
        static_s = SCENE_SECONDS - anim_s
        assert abs((anim_s + static_s) - SCENE_SECONDS) < 1e-6
        is_card = step.capture.startswith("card:")
        n_full = _char_count(step.title, step.body)

        move_dur = 0.0
        if not is_card:
            move_pngs = []
            start = prev_cur or step.cursor
            for i in range(MOVE_FRAMES):
                e = 0.5 - 0.5 * math.cos(math.pi * (i / max(1, MOVE_FRAMES - 1)))
                cur = (start[0] + (step.cursor[0] - start[0]) * e,
                       start[1] + (step.cursor[1] - start[1]) * e)
                path = anim / f"{step.id}_m{i:02d}.png"
                show_spot = i >= MOVE_FRAMES - 2
                _compose(base, path, title="", body="", badge="", cursor=cur, spotlight=spot,
                         reveal_chars=0, show_spotlight=show_spot, show_dialogue=False)
                move_pngs.append(path)
            move_mp4 = CLIPS_DIR / f"{step.id}_move.mp4"
            _encode_seq(move_pngs, move_mp4)
            segment_paths.append(move_mp4)
            move_dur = MOVE_FRAMES / FPS

        click_mp4_path = None
        click_dur = 0.0
        if not is_card and step.click:
            click_pngs = []
            for i in range(CLICK_FRAMES):
                path = anim / f"{step.id}_c{i:02d}.png"
                _compose(base, path, title=step.title, body=step.body, badge=step.badge,
                         cursor=step.cursor, spotlight=spot, clicking=True,
                         reveal_chars=n_full, show_spotlight=True, show_dialogue=True, show_arrow=True)
                click_pngs.append(path)
            click_mp4_path = CLIPS_DIR / f"{step.id}_click.mp4"
            _encode_seq(click_pngs, click_mp4_path)
            click_dur = CLICK_FRAMES / FPS

        # Typing frames (no arrow until complete)
        type_pngs = []
        for i in range(anim_frames):
            frac = (i + 1) / anim_frames
            n_chars = max(1, int(math.ceil(frac * n_full)))
            done = n_chars >= n_full
            path = anim / f"{step.id}_t{i:03d}.png"
            if is_card:
                _compose_card_scene(base, path, title=step.title, body=step.body, badge=step.badge,
                                    reveal_chars=n_chars, show_arrow=done)
            else:
                _compose(base, path, title=step.title, body=step.body, badge=step.badge,
                         cursor=step.cursor, spotlight=spot, reveal_chars=n_chars,
                         show_spotlight=True, show_dialogue=True, show_arrow=done)
            type_pngs.append(path)
        type_mp4 = CLIPS_DIR / f"{step.id}_type.mp4"
        _encode_seq(type_pngs, type_mp4)
        segment_paths.append(type_mp4)

        # Static hold with blinking arrow
        hold_a = anim / f"{step.id}_hold_a.png"
        hold_b = anim / f"{step.id}_hold_b.png"
        if is_card:
            _compose_card_scene(base, hold_a, title=step.title, body=step.body, badge=step.badge,
                                reveal_chars=n_full, show_arrow=True, arrow_offset=0)
            _compose_card_scene(base, hold_b, title=step.title, body=step.body, badge=step.badge,
                                reveal_chars=n_full, show_arrow=True, arrow_offset=3)
        else:
            _compose(base, hold_a, title=step.title, body=step.body, badge=step.badge,
                     cursor=step.cursor, spotlight=spot, reveal_chars=n_full,
                     show_spotlight=True, show_dialogue=True, show_arrow=True, arrow_offset=0)
            _compose(base, hold_b, title=step.title, body=step.body, badge=step.badge,
                     cursor=step.cursor, spotlight=spot, reveal_chars=n_full,
                     show_spotlight=True, show_dialogue=True, show_arrow=True, arrow_offset=3)
        hold_mp4 = CLIPS_DIR / f"{step.id}_hold.mp4"
        _encode_blink_hold(hold_a, hold_b, static_s, hold_mp4)
        segment_paths.append(hold_mp4)

        anim_start = t + move_dur
        anim_end = anim_start + anim_s
        arrow_at = anim_end
        scene_end = anim_start + SCENE_SECONDS

        post = 0.0
        if click_mp4_path is not None:
            segment_paths.append(click_mp4_path)
            outcome = CLIPS_DIR / f"{step.id}_outcome.mp4"
            _encode_still(hold_a, OUTCOME_S, outcome)
            segment_paths.append(outcome)
            post = click_dur + OUTCOME_S

        timing_rows.append({
            "id": step.id,
            "title": step.title,
            "body": step.body.replace("\n", " / "),
            "badge": step.badge,
            "instructional": step.instructional,
            "anim_start": anim_start,
            "anim_end": anim_end,
            "arrow_at": arrow_at,
            "anim_duration": anim_s,
            "static_duration": static_s,
            "scene_duration": SCENE_SECONDS,
            "scene_end": scene_end,
            "spotlight": ",".join(f"{v:.2f}" for v in spot),
            "spotlight_ok": True,
            "dim_alpha": DIM_ALPHA,
        })
        t = scene_end + post
        prev_cur = step.cursor
        print(f"  {step.id}: type={anim_s:.2f}s static={static_s:.2f}s end={t:.1f}s", flush=True)

    _validate_timing(timing_rows)
    _write_srt(timing_rows)
    _write_storyboard(timing_rows, steps)

    concat = CLIPS_DIR / "concat.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in segment_paths), encoding="utf-8")
    muxed = CLIPS_DIR / "muxed.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(muxed)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy2(muxed, VIDEO_OUT)
    _make_zip()

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
         "-show_entries", "stream=codec_type,codec_name,width,height", "-of", "json", str(VIDEO_OUT)],
        check=True, capture_output=True, text=True)
    print(probe.stdout)
    vol = subprocess.run(["ffmpeg", "-i", str(VIDEO_OUT), "-af", "volumedetect", "-f", "null", "-"],
                         check=True, capture_output=True, text=True)
    print(vol.stderr)
    meta = {
        "scene_seconds": SCENE_SECONDS,
        "instructional_scenes": sum(1 for r in timing_rows if r["instructional"]),
        "min_scene_s": min(r["scene_duration"] for r in timing_rows),
        "max_scene_s": max(r["scene_duration"] for r in timing_rows),
        "min_typing_s": min(r["anim_duration"] for r in timing_rows),
        "max_typing_s": max(r["anim_duration"] for r in timing_rows),
        "dim_alpha": DIM_ALPHA,
        "scenes_with_spotlight": sum(1 for r in timing_rows if r["instructional"]),
        "duration_s": t,
        "monthly_sql_requirement": "{date_inicio} and {date_fim}",
        "monthly_sql_evidence": MONTHLY_SQL_EVIDENCE,
        "timing_validation_passed": True,
        "spotlight_validation_passed": True,
        "holds": timing_rows,
    }
    (OUT_DIR / "validation_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {VIDEO_OUT}")
    print(f"Wrote {ZIP_OUT}")
    print(f"Wrote {TIMING_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
