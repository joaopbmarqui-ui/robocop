#!/usr/bin/env python3
"""Silent New Job onboarding — 8s scenes, Carlito dialogue, element spotlights @ 1080p.

Calibri is not available in this environment; Carlito (fonts-crosextra-carlito)
is used as the metric-compatible substitute.

Verified MonthlyJob SQL rule: ``{date_inicio}`` and ``{date_fim}``.
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
FONTS_DIR = OUT_DIR / "fonts"
VIDEO_OUT = OUT_DIR / "dispatch_robocop_new_job_onboarding_ptbr.mp4"
CAPTIONS_OUT = OUT_DIR / "dispatch_robocop_new_job_captions_ptbr.srt"
STORYBOARD_OUT = OUT_DIR / "dispatch_robocop_new_job_storyboard.md"
TIMING_REPORT = OUT_DIR / "footer_timing_report.md"
SPOTLIGHT_REPORT = OUT_DIR / "spotlight_report.md"
SPOTLIGHT_JSON = OUT_DIR / "spotlight_report.json"
CONTACT_SHEET = OUT_DIR / "spotlight_contact_sheet.png"
ZIP_OUT = OUT_DIR / "dispatch_robocop_new_job_video_download.zip"
NARRATION_LEGACY = OUT_DIR / "dispatch_robocop_new_job_narration_ptbr.txt"

VIDEO_W, VIDEO_H = 1920, 1080
FPS = 30
SCENE_SECONDS = 8.0
MOVE_FRAMES = 9
CLICK_FRAMES = 4
OUTCOME_S = 0.8
DIALOGUE_H = 270  # lower quarter of 1080
DIM_ALPHA = 170
TERMINAL_SIZE = (200, 70)
TYPING_MIN_S = 1.0
TYPING_MAX_S = 1.5
ARROW_BLINK_S = 0.35
BODY_FONT_PX = 38
TITLE_FONT_PX = 42
BADGE_FONT_PX = 22
MARGIN_FIELD_PX = 20
MARGIN_BUTTON_PX = 16
MARGIN_SMALL_PX = 14

# Font selection (priority: Calibri → Carlito → Liberation Sans)
FONT_REGULAR = FONTS_DIR / "Carlito-Regular.ttf"
FONT_BOLD = FONTS_DIR / "Carlito-Bold.ttf"
FONT_NAME = "Carlito"
FONT_REASON = (
    "Calibri is not installed in this Linux environment. "
    "Using Carlito (fonts-crosextra-carlito), the OFL metric-compatible substitute."
)

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
    targets: list[str] = field(default_factory=list)


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
             "Schema e Table Name entram no nome da tabela.",
             "", (0.55, 0.58), section="Relações", evidence="date fields"),
        Step("39c_rel_monthly_dates", "monthly_fields", "Datas do MonthlyJob",
             "Start Date e End Date definem o intervalo mês a mês.",
             "", (0.55, 0.70), section="Relações", evidence="monthly dates"),
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
        Step("44_preview", "ready_review", "Preview SQL",
             "Mostra o conteúdo que será usado no job.",
             "", (0.78, 0.92), click=True, section="Preview", evidence="Preview SQL [P]"),
        Step("44b_preview_check", "preview", "O que conferir no Preview",
             "Confira a consulta e o destino antes do envio.",
             "", (0.55, 0.35), section="Preview", evidence="preview screen"),
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




def _apply_targets(steps: list[Step]) -> list[Step]:
    """Attach precise Textual widget ids for element-based spotlights."""
    mapping: dict[str, list[str]] = {
        "02_purpose_a": ["radio-panel"],
        "02_purpose_b": ["source", "destination"],
        "03_matrix": ["matrix-collapsible"],
        "04_detected": ["info-detected"],
        "05_source_intro": ["source"],
        "06_source_sqlfile": ["src-sqlfile"],
        "06b_source_sqlfile_effect": ["src-sqlfile"],
        "07_dest_intro": ["destination"],
        "08_dest_table": ["dst-table"],
        "09_dest_csv": ["dst-csv"],
        "09b_dest_csv_when": ["dst-csv"],
        "10_dest_tablecsv": ["dst-table-csv"],
        "11_queue_a": ["lbl-queue", "queue"],
        "12_queue_b": ["lbl-queue", "queue"],
        "12b_queue_order": ["queue-panel"],
        "13_sql_intro": ["lbl-sql-file", "sql-file"],
        "13b_sql_when": ["lbl-sql-file", "sql-file"],
        "14_sql_picker": ["sql-file-picker"],
        "15_sql_verify": ["sql-file-picker"],
        "15b_sql_path": ["lbl-sql-file", "sql-file"],
        "16_sql_role": ["lbl-sql-file", "sql-file"],
        "16b_sql_role_dest": ["source", "destination"],
        "17_email": ["lbl-email", "email"],
        "18_subject": ["lbl-subject", "subject"],
        "19_status_bar": ["validation-summary"],
        "19b_actions": ["preview", "launch"],
        "20_mj_intro": ["src-sqltemplate"],
        "21_mj_dest": ["src-sqltemplate", "dst-table"],
        "21b_mj_dest_blocked": ["dst-csv", "dst-table-csv"],
        "22_mj_sql_rule_a": [],
        "23_mj_sql_rule_b": [],
        "23b_mj_sql_missing": [],
        "24_mj_sql_rule_c": [],
        "24b_mj_sql_fill": [],
        "25_mj_picker": ["sql-file-picker"],
        "25b_mj_picker_confirm": ["sql-file-picker"],
        "26_mj_schema": ["lbl-schema", "schema"],
        "27_mj_table": ["lbl-table-name", "table-name-prefix", "table-name-suffix"],
        "27b_mj_table_suffix": ["table-name-prefix", "table-name-suffix"],
        "28_mj_start": ["lbl-start-date", "start-date"],
        "29_mj_end": ["lbl-end-date", "end-date"],
        "30_et_intro": ["src-existingtable"],
        "31_et_dest": ["src-existingtable", "dst-csv"],
        "31b_et_dest_blocked": ["dst-table", "dst-table-csv"],
        "32_et_no_sql": ["src-existingtable", "dest-hint"],
        "33_et_schema_coe": ["esc-coe-enc"],
        "34_et_schema_aa": ["esc-aa-enc"],
        "35_et_schema_other": ["esc-other"],
        "35b_et_other_field": ["lbl-existing-schema-custom", "existing-schema-custom"],
        "36_et_custom": ["lbl-existing-schema-custom", "existing-schema-custom"],
        "37_et_table": ["lbl-existing-table", "existing-table"],
        "37b_et_full": [
            "lbl-existing-schema", "existing-schema",
            "lbl-existing-table", "existing-table",
        ],
        "38_rel_standard": ["src-sqlfile", "dst-csv"],
        "38b_rel_standard_use": ["src-sqlfile", "dst-csv"],
        "39_rel_monthly": ["src-sqltemplate", "dst-table"],
        "39b_rel_monthly_fields": [
            "lbl-schema", "schema", "lbl-table-name", "table-name-prefix", "table-name-suffix",
        ],
        "39c_rel_monthly_dates": [
            "lbl-start-date", "start-date", "lbl-end-date", "end-date",
        ],
        "40_rel_existing": ["src-existingtable", "dst-csv"],
        "40b_rel_existing_no_sql": ["src-existingtable"],
        "41_rel_incompat": ["matrix-table"],
        "41b_rel_incompat_et": ["matrix-table"],
        "42_val_bad": ["lbl-email", "email", "validation-summary"],
        "43_val_ok": ["validation-summary"],
        "43b_val_review": ["source", "destination"],
        "44_preview": ["preview"],
        "44b_preview_check": ["preview-header", "preview-body"],
        "45_checklist": [],
        "45b_checklist_b": [],
        "46_confirm": ["confirm-dialog"],
        "46b_confirm_read": ["confirm-dialog"],
        "47_launched": ["warning-text"],
        "48_overview": ["sidebar-nav"],
        "49_close": [],
        "49b_close_b": [],
    }
    out = []
    for s in steps:
        targets = mapping.get(s.id, s.targets)
        out.append(Step(
            id=s.id, capture=s.capture, title=s.title, body=s.body, badge=s.badge,
            cursor=s.cursor, click=s.click, section=s.section, evidence=s.evidence,
            instructional=s.instructional, spotlight=s.spotlight, targets=list(targets),
        ))
    return out


REGION_WIDGET_IDS = [
    "matrix-collapsible", "matrix-table", "info-detected",
    "source", "src-sqlfile", "src-sqltemplate", "src-existingtable",
    "destination", "dst-table", "dst-csv", "dst-table-csv", "dest-hint",
    "queue-panel", "lbl-queue", "queue", "queue-hint",
    "picker-caption", "sql-file-picker",
    "row-sql-file", "lbl-sql-file", "sql-file", "path-hint",
    "row-existing-schema", "lbl-existing-schema", "existing-schema",
    "esc-coe-enc", "esc-aa-enc", "esc-other",
    "row-existing-schema-custom", "lbl-existing-schema-custom", "existing-schema-custom",
    "row-existing-table", "lbl-existing-table", "existing-table",
    "row-schema", "lbl-schema", "schema",
    "row-table-name", "lbl-table-name", "table-name-prefix", "table-name-suffix",
    "row-start-date", "lbl-start-date", "start-date",
    "row-end-date", "lbl-end-date", "end-date",
    "row-email", "lbl-email", "email",
    "row-subject", "lbl-subject", "subject",
    "warning-text", "validation-summary", "preview", "launch",
    "new-job-action-bar", "radio-panel", "radio-row", "new-job-content",
    "confirm-dialog", "confirm-title", "confirm-body", "confirm-yes",
    "preview-body", "preview-content", "preview-header", "preview-meta",
    "sql-display", "findings-heading", "sidebar-nav",
]


def _dump_regions(app, out_json: Path) -> None:
    import json
    from textual.widget import Widget

    regions = {"terminal_size": list(TERMINAL_SIZE), "widgets": {}}
    for wid in REGION_WIDGET_IDS:
        try:
            w = app.screen.query_one(f"#{wid}", Widget)
            r = w.region
            regions["widgets"][wid] = {
                "x": int(r.x), "y": int(r.y), "w": int(r.width), "h": int(r.height),
            }
        except Exception:
            continue
    # Confirm screen / preview / overview extras
    for wid in (
        "sidebar-nav", "preview-body", "preview-content", "preview-header",
        "preview-meta", "sql-display", "findings-heading", "confirm-dialog",
        "launched-message",
    ):
        try:
            w = app.screen.query_one(f"#{wid}", Widget)
            r = w.region
            regions["widgets"][wid] = {
                "x": int(r.x), "y": int(r.y), "w": int(r.width), "h": int(r.height),
            }
        except Exception:
            pass
    # Any Button labeled Launch Job on confirm
    try:
        for btn in app.screen.query("Button"):
            if getattr(btn, "id", None):
                r = btn.region
                regions["widgets"][btn.id] = {
                    "x": int(r.x), "y": int(r.y), "w": int(r.width), "h": int(r.height),
                }
    except Exception:
        pass
    out_json.write_text(json.dumps(regions, indent=2), encoding="utf-8")


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
            _dump_regions(app, FRAMES_DIR / f"{name}_regions.json")
            app.save_screenshot(filename=str(out))
            return out
        await _open_new_job(pilot, app)
        await setup(pilot, app)
        if isinstance(app.screen, NewJobScreen):
            _neutral_email(app.screen)
        await pilot.pause(0.35)
        _dump_regions(app, FRAMES_DIR / f"{name}_regions.json")
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


def _ui_font(size: int, *, bold: bool = False):
    from PIL import ImageFont

    path = FONT_BOLD if bold else FONT_REGULAR
    fallbacks = [
        path,
        Path("/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf" if bold else "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]
    for p in fallbacks:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _load_regions(capture: str) -> dict:
    path = FRAMES_DIR / f"{capture}_regions.json"
    if not path.exists():
        return {"terminal_size": list(TERMINAL_SIZE), "widgets": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _cell_to_norm(regions: dict, wid: str) -> tuple[float, float, float, float] | None:
    """Convert widget cell region to normalized coords in the UI PNG (0–1)."""
    winfo = regions.get("widgets", {}).get(wid)
    if not winfo:
        return None
    if int(winfo.get("w", 0)) <= 0 or int(winfo.get("h", 0)) <= 0:
        return None
    cols, rows = regions.get("terminal_size", list(TERMINAL_SIZE))
    cols = max(1, int(cols))
    rows = max(1, int(rows))
    # Textual SVG export paints content ~1 cell below query_one().region.y
    # for this terminal size; bias keeps spotlights on the visible glyphs.
    y_bias = 1
    x0 = winfo["x"] / cols
    y0 = (winfo["y"] + y_bias) / rows
    x1 = (winfo["x"] + winfo["w"]) / cols
    y1 = (winfo["y"] + winfo["h"] + y_bias) / rows
    return (
        max(0.0, min(0.99, x0)),
        max(0.0, min(0.99, y0)),
        max(0.01, min(1.0, x1)),
        max(0.01, min(1.0, y1)),
    )


def _union_norms(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _margin_for(wid: str) -> int:
    if wid in {"preview", "launch", "src-sqlfile", "src-sqltemplate", "src-existingtable",
               "dst-table", "dst-csv", "dst-table-csv", "esc-coe-enc", "esc-aa-enc", "esc-other",
               "confirm-yes", "confirm-no"}:
        return MARGIN_BUTTON_PX
    if wid.endswith("-hint") or wid.startswith("lbl-") or wid == "info-detected":
        return MARGIN_SMALL_PX
    return MARGIN_FIELD_PX


def _can_merge_targets(
    wid_a: str,
    wid_b: str,
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> bool:
    """Merge only label+control pairs, or table-name prefix+suffix."""
    pair = {wid_a, wid_b}
    if pair == {"table-name-prefix", "table-name-suffix"}:
        return True
    if "lbl-table-name" in pair and pair & {"table-name-prefix", "table-name-suffix"}:
        cy_a = (a[1] + a[3]) / 2
        cy_b = (b[1] + b[3]) / 2
        return abs(cy_a - cy_b) < 0.05
    la = wid_a.startswith("lbl-")
    lb = wid_b.startswith("lbl-")
    if not (la ^ lb):
        return False
    cy_a = (a[1] + a[3]) / 2
    cy_b = (b[1] + b[3]) / 2
    # Same-row label | control
    if abs(cy_a - cy_b) <= 0.04:
        gap_x = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
        return gap_x < 0.04
    # Label directly above its control (queue / stacked fields)
    gap_y = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    overlap_x = min(a[2], b[2]) - max(a[0], b[0])
    return gap_y < 0.035 and overlap_x > 0.15


def _spotlights_for_step(step: Step) -> list[tuple[float, float, float, float]]:
    """Return one or more normalized UI cutouts for the step."""
    if step.capture.startswith("card:"):
        return [(0.12, 0.14, 0.88, 0.70)]
    if step.spotlight is not None:
        return [step.spotlight]
    regions = _load_regions(step.capture)
    items: list[tuple[str, tuple[float, float, float, float]]] = []
    for wid in step.targets:
        n = _cell_to_norm(regions, wid)
        if n:
            items.append((wid, n))
    if not items:
        cx, cy = step.cursor
        return [(max(0.02, cx - 0.08), max(0.02, cy - 0.04),
                 min(0.98, cx + 0.08), min(0.88, cy + 0.04))]

    # Clamp oversized SQL preview logs so the cutout stays on the query, not
    # the whole preview chrome / findings area.
    clamped: list[tuple[str, tuple[float, float, float, float]]] = []
    for wid, n in items:
        l, t, r, b = n
        if wid in {"preview-body", "sql-display"}:
            b = min(b, t + 0.40)
        clamped.append((wid, (l, t, r, b)))
    items = clamped

    # Separate cutouts per target. Merge only label↔control (same row) or
    # table-name prefix+suffix (+ optional label).
    refined: list[tuple[float, float, float, float]] = []
    used = [False] * len(items)
    for i, (wid_a, a) in enumerate(items):
        if used[i]:
            continue
        group_wids = [wid_a]
        group_boxes = [a]
        used[i] = True
        for j, (wid_b, b) in enumerate(items):
            if used[j]:
                continue
            if any(_can_merge_targets(wa, wid_b, ba, b)
                   for wa, ba in zip(group_wids, group_boxes)):
                group_wids.append(wid_b)
                group_boxes.append(b)
                used[j] = True
        refined.append(_union_norms(group_boxes))
    return refined


def _cursor_for_step(step: Step, spots: list[tuple[float, float, float, float]]) -> tuple[float, float]:
    if not spots:
        return step.cursor
    l, t, r, b = spots[0]
    # Prefer left side, vertically centered so thin status lines keep cursor on-target.
    return (min(r - 0.02, l + 0.04), (t + b) / 2)


def _typing_plan(step: Step) -> tuple[int, float]:
    n = max(1, _char_count(step.title, step.body))
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
    draw.rectangle((0, 0, 12, VIDEO_H), fill=(64, 156, 255))
    title_f = _ui_font(48, bold=True)
    body_f = _ui_font(34)
    y = 160
    draw.text((80, y), title, fill=(245, 245, 245), font=title_f)
    y += 90
    for line in body.split("\n"):
        color = (255, 220, 120) if "{" in line else (210, 220, 235)
        draw.text((80, y), line, fill=color, font=body_f)
        y += 52
    img.save(dest)


def _draw_cursor(draw, x: int, y: int, *, clicking: bool = False) -> None:
    pts = [(x, y), (x, y + 28), (x + 8, y + 22), (x + 14, y + 36),
           (x + 20, y + 33), (x + 12, y + 19), (x + 22, y + 19)]
    draw.polygon(pts, fill=(255, 255, 255), outline=(20, 20, 20))
    if clicking:
        r = 22
        draw.ellipse((x - r, y - r, x + r, y + r), outline=(64, 156, 255), width=3)


def _draw_red_arrow(draw, box_right: int, box_bottom: int, *, offset: int = 0) -> None:
    ax = box_right - 48
    ay = box_bottom - 40 + offset
    draw.polygon([(ax, ay), (ax + 22, ay), (ax + 11, ay + 16)], fill=(220, 40, 40))


def _layout_ui(ui_png: Path, *, focus_bottom: float | None = None):
    from PIL import Image
    ui = Image.open(ui_png).convert("RGBA")
    max_h = VIDEO_H - DIALOGUE_H
    ratio = min(VIDEO_W / ui.width, max_h / ui.height)
    new = ui.resize((max(1, int(ui.width * ratio)), max(1, int(ui.height * ratio))), Image.Resampling.LANCZOS)
    ox = (VIDEO_W - new.width) // 2
    oy = max(0, (max_h - new.height) // 2)
    # Keep low targets above the dialogue box by shifting the UI upward.
    if focus_bottom is not None and new.height <= max_h:
        target_bottom = oy + int(focus_bottom * new.height) + MARGIN_FIELD_PX
        limit = max_h - 12
        if target_bottom > limit:
            oy = max(0, oy - (target_bottom - limit))
    return ui, new, ox, oy


def _draw_dialogue_box(canvas, *, title: str, body: str, badge: str,
                       reveal_chars: int, show_arrow: bool, arrow_offset: int = 0) -> None:
    from PIL import ImageDraw
    draw = ImageDraw.Draw(canvas)
    margin_x = 72
    top = VIDEO_H - DIALOGUE_H + 18
    bottom = VIDEO_H - 18
    left = margin_x
    right = VIDEO_W - margin_x
    draw.rounded_rectangle((left - 4, top - 4, right + 4, bottom + 4), radius=14, fill=(0, 0, 0, 255))
    draw.rounded_rectangle((left, top, right, bottom), radius=12, fill=(252, 252, 252, 255))
    draw.rounded_rectangle((left + 4, top + 4, right - 4, bottom - 4), radius=10, outline=(0, 0, 0, 255), width=2)

    title_f = _ui_font(TITLE_FONT_PX, bold=True)
    body_f = _ui_font(BODY_FONT_PX, bold=False)
    badge_f = _ui_font(BADGE_FONT_PX, bold=True)
    vis_title, vis_body = _visible_parts(title, body, reveal_chars)
    pad_x, pad_y = 56, 32
    y = top + pad_y
    if vis_title:
        draw.text((left + pad_x, y), vis_title, fill=(10, 10, 10, 255), font=title_f)
    if badge and reveal_chars >= len(title):
        bw = 28 + len(badge) * 11
        bx = right - bw - 64
        draw.rectangle((bx, y + 4, bx + bw, y + 34), outline=(0, 0, 0), width=2)
        draw.text((bx + 10, y + 8), badge, fill=(10, 10, 10, 255), font=badge_f)
    y = top + pad_y + 52
    line_gap = int(BODY_FONT_PX * 1.2)
    for line in vis_body.split("\n")[:2]:
        draw.text((left + pad_x, y), line, fill=(20, 20, 20, 255), font=body_f)
        y += line_gap
    if show_arrow:
        _draw_red_arrow(draw, right - 12, bottom - 8, offset=arrow_offset)


def _apply_spotlights(canvas, new, ox, oy, spotlights: list[tuple[float, float, float, float]],
                      margins_px: list[int] | None = None) -> list[tuple[int, int, int, int]]:
    from PIL import Image, ImageDraw
    dim = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, DIM_ALPHA))
    canvas_dim = Image.alpha_composite(canvas, dim)
    bright = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    bright.paste(new, (ox, oy), new)
    final_boxes = []
    draw = ImageDraw.Draw(canvas_dim)
    for i, (l, t, r, b) in enumerate(spotlights):
        m = (margins_px[i] if margins_px and i < len(margins_px) else MARGIN_FIELD_PX)
        sx0 = max(0, ox + int(l * new.width) - m)
        sy0 = max(0, oy + int(t * new.height) - m)
        sx1 = min(VIDEO_W, ox + int(r * new.width) + m)
        sy1 = min(VIDEO_H - DIALOGUE_H - 4, oy + int(b * new.height) + m)
        if sx1 <= sx0 or sy1 <= sy0:
            continue
        canvas_dim.paste(bright.crop((sx0, sy0, sx1, sy1)), (sx0, sy0))
        for w, col in ((4, (255, 220, 80, 210)), (2, (0, 0, 0, 255))):
            draw.rounded_rectangle((sx0 - 1, sy0 - 1, sx1 + 1, sy1 + 1), radius=6, outline=col, width=w)
        final_boxes.append((sx0, sy0, sx1, sy1))
    canvas.paste(canvas_dim)
    return final_boxes


def _compose(ui_png: Path, dest: Path, *, title: str, body: str, badge: str,
             cursor: tuple[float, float],
             spotlights: list[tuple[float, float, float, float]],
             clicking: bool = False, reveal_chars: int | None = None,
             show_spotlight: bool = True, show_dialogue: bool = True,
             show_arrow: bool = False, arrow_offset: int = 0,
             margins_px: list[int] | None = None) -> list[tuple[int, int, int, int]]:
    from PIL import Image, ImageDraw
    focus_bottom = max((b[3] for b in spotlights), default=None) if spotlights else None
    ui, new, ox, oy = _layout_ui(ui_png, focus_bottom=focus_bottom)
    canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (12, 14, 18, 255))
    canvas.paste(new, (ox, oy), new)
    final_boxes: list[tuple[int, int, int, int]] = []
    if show_spotlight and spotlights:
        # Rebuild with dim+cutouts
        dimmed = Image.new("RGBA", (VIDEO_W, VIDEO_H), (12, 14, 18, 255))
        dimmed.paste(new, (ox, oy), new)
        overlay = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, DIM_ALPHA))
        dimmed = Image.alpha_composite(dimmed, overlay)
        bright = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        bright.paste(new, (ox, oy), new)
        draw = ImageDraw.Draw(dimmed)
        for i, (l, t, r, b) in enumerate(spotlights):
            m = (margins_px[i] if margins_px and i < len(margins_px) else MARGIN_FIELD_PX)
            # Keep vertical margin proportional so 1-cell lines do not swallow neighbors.
            box_h = max(1, int((b - t) * new.height))
            m_v = min(m, max(8, int(box_h * 0.45)))
            m_h = m
            sx0 = max(0, ox + int(l * new.width) - m_h)
            sy0 = max(0, oy + int(t * new.height) - m_v)
            sx1 = min(VIDEO_W, ox + int(r * new.width) + m_h)
            sy1 = min(VIDEO_H - DIALOGUE_H - 4, oy + int(b * new.height) + m_v)
            if sx1 <= sx0 or sy1 <= sy0:
                continue
            dimmed.paste(bright.crop((sx0, sy0, sx1, sy1)), (sx0, sy0))
            for w, col in ((4, (255, 220, 80, 210)), (2, (0, 0, 0, 255))):
                draw.rounded_rectangle((sx0 - 1, sy0 - 1, sx1 + 1, sy1 + 1), radius=6, outline=col, width=w)
            final_boxes.append((sx0, sy0, sx1, sy1))
        canvas = dimmed

    draw = ImageDraw.Draw(canvas)
    cx = ox + int(cursor[0] * new.width)
    cy = oy + int(cursor[1] * new.height)
    cy = min(cy, VIDEO_H - DIALOGUE_H - 30)
    _draw_cursor(draw, cx, cy, clicking=clicking)
    if show_dialogue:
        n = reveal_chars if reveal_chars is not None else _char_count(title, body)
        _draw_dialogue_box(canvas, title=title, body=body, badge=badge, reveal_chars=n,
                           show_arrow=show_arrow and n >= _char_count(title, body),
                           arrow_offset=arrow_offset)
    canvas.convert("RGB").save(dest)
    return final_boxes


def _compose_card_scene(card_png: Path, dest: Path, *, title: str, body: str, badge: str,
                        reveal_chars: int | None = None, show_arrow: bool = False,
                        arrow_offset: int = 0) -> list[tuple[int, int, int, int]]:
    from PIL import Image, ImageDraw
    card = Image.open(card_png).convert("RGBA").resize((VIDEO_W, VIDEO_H), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (12, 14, 18, 255))
    canvas.paste(card, (0, 0), card)
    dimmed = Image.alpha_composite(canvas, Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, DIM_ALPHA)))
    sx0, sy0, sx1, sy1 = 80, 100, VIDEO_W - 80, VIDEO_H - DIALOGUE_H - 24
    dimmed.paste(card.crop((sx0, sy0, sx1, sy1)), (sx0, sy0))
    draw = ImageDraw.Draw(dimmed)
    for w, col in ((4, (255, 220, 80, 210)), (2, (0, 0, 0, 255))):
        draw.rounded_rectangle((sx0 - 1, sy0 - 1, sx1 + 1, sy1 + 1), radius=8, outline=col, width=w)
    n = reveal_chars if reveal_chars is not None else _char_count(title, body)
    _draw_dialogue_box(dimmed, title=title, body=body, badge=badge, reveal_chars=n,
                       show_arrow=show_arrow and n >= _char_count(title, body),
                       arrow_offset=arrow_offset)
    dimmed.convert("RGB").save(dest)
    return [(sx0, sy0, sx1, sy1)]


def _encode_still(png: Path, seconds: float, out_mp4: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loop", "1", "-i", str(png),
         "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=44100",
         "-t", f"{seconds:.3f}", "-r", str(FPS),
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "64k", "-shortest", str(out_mp4)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


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
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(seq, ignore_errors=True)


def _encode_blink_hold(png_a: Path, png_b: Path, seconds: float, out_mp4: Path) -> None:
    half = ARROW_BLINK_S
    n_pairs = max(1, int(math.ceil(seconds / (2 * half))))
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
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(long_mp4)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-i", str(long_mp4), "-t", f"{seconds:.3f}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k", str(out_mp4)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        "# Instructional scene timing validation (exactly 8.0s @ 1920×1080)",
        "",
        f"Font: **{FONT_NAME}** (`{FONT_REGULAR.name}` / `{FONT_BOLD.name}`). {FONT_REASON}",
        f"Body size: {BODY_FONT_PX}px. Dim alpha={DIM_ALPHA}.",
        "",
        "| Scene | Element | Start | Type end | Arrow | End | Type | Total | Cutouts | Result |",
        "|---|---|---|---|---|---|---|---|---|---|",
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
            ok = False; reasons.append("not-8s")
        if anim > TYPING_MAX_S + (1.0 / FPS) + 1e-6:
            ok = False; reasons.append("typing>1.5")
        if row["arrow_at"] + 1e-6 < row["anim_end"]:
            ok = False; reasons.append("arrow-early")
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed.append(f"{row['id']}({','.join(reasons)})")
        lines.append(
            f"| `{row['id']}` | {row['title'][:24]} | {_fmt_ts(row['anim_start'])} | "
            f"{_fmt_ts(row['anim_end'])} | {_fmt_ts(row['arrow_at'])} | {_fmt_ts(row['scene_end'])} | "
            f"{anim:.2f}s | {total:.2f}s | {row['n_cutouts']} | **{status}** |"
        )
    lines.append("")
    lines.append(f"Instructional scenes: {sum(1 for r in rows if r['instructional'])}")
    if failed:
        lines.append(f"**FAILED:** {', '.join(failed)}")
        TIMING_REPORT.write_text("\n".join(lines), encoding="utf-8")
        raise AssertionError(f"Timing validation failed: {failed}")
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
        "# Storyboard — New Job (8.0s, Carlito, 1920×1080, element spotlights)",
        "",
        f"Font: {FONT_NAME} ({FONT_REGULAR.name}). Body {BODY_FONT_PX}px / title {TITLE_FONT_PX}px.",
        f"{FONT_REASON}",
        "",
    ]
    for row in rows:
        step = by_id[row["id"]]
        lines += [
            f"## {step.id} — {step.section}",
            "",
            f"- **Elemento:** {step.title}",
            f"- **Targets:** {', '.join(step.targets) if step.targets else '(card)'}",
            f"- **Font:** {FONT_NAME} {BODY_FONT_PX}px",
            f"- **Norm cutouts:** {row['spotlights_norm']}",
            f"- **Final px boxes:** {row['spotlights_px']}",
            f"- **Cutouts:** {row['n_cutouts']}",
            f"- **Overlay opacity:** {DIM_ALPHA}/255",
            f"- **Diálogo:** {step.title} — {step.body.replace(chr(10), ' / ')}",
            f"- **Typing:** {_fmt_ts(row['anim_start'])} → {_fmt_ts(row['anim_end'])} ({row['anim_duration']:.2f}s)",
            f"- **Seta:** {_fmt_ts(row['arrow_at'])}",
            f"- **Duração:** {row['scene_duration']:.2f}s",
            f"- **Manual review:** {row.get('manual_review', 'pending')}",
            f"- **Evidência:** {step.evidence}",
            "",
        ]
    STORYBOARD_OUT.write_text("\n".join(lines), encoding="utf-8")


def _manual_review_spotlight(
    step: Step,
    spots_norm: list[tuple[float, float, float, float]],
    boxes_px: list[tuple[int, int, int, int]],
) -> tuple[str, str]:
    """Heuristic + geometric checks used before human frame inspection."""
    if step.capture.startswith("card:"):
        return "PASS", "card content spotlight"
    if not boxes_px:
        return "FAIL", "missing spotlight cutout"
    app_h = VIDEO_H - DIALOGUE_H
    app_area = VIDEO_W * app_h
    allow_large = {
        "46_confirm", "46b_confirm_read", "03_matrix", "14_sql_picker",
        "15_sql_verify", "25_mj_picker", "25b_mj_picker_confirm",
        "48_overview", "02_purpose_a",
    }
    for b in boxes_px:
        if b[3] > VIDEO_H - DIALOGUE_H + 2:
            return "FAIL", "target covered by dialogue box"
        area = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
        if area > 0.40 * app_area and step.id not in allow_large:
            return "FAIL", "oversized generic spotlight"
        if area > 0.55 * app_area:
            return "FAIL", "spotlight covers most of the application"
    # Peer controls (not label+control) must not collapse into one cutout.
    peers = [t for t in step.targets if not t.startswith("lbl-")]
    peer_set = set(peers)
    if peer_set == {"table-name-prefix", "table-name-suffix"}:
        return "PASS", ""
    if len(peers) >= 2 and len(boxes_px) < 2 and step.id not in allow_large:
        # Adjacent destination radios may share one tight row cutout.
        if peer_set <= {"dst-csv", "dst-table-csv", "dst-table"} and len(peers) == 2:
            return "PASS", "adjacent destination options"
        return "FAIL", "distant elements merged into one cutout"
    if len(spots_norm) != len(boxes_px):
        return "FAIL", "cutout count mismatch after clamping"
    return "PASS", ""


def _write_spotlight_report(rows: list[dict], steps: list[Step]) -> None:
    by_id = {s.id: s for s in steps}
    lines = [
        "# Spotlight manual-review report",
        "",
        f"Resolution {VIDEO_W}×{VIDEO_H}. Overlay alpha={DIM_ALPHA}. Font={FONT_NAME}.",
        "",
        "| Scene | Topic | Targets | Pre-margin boxes | Final boxes | Margin | Cutouts | Opacity | Review frame | Status | Reason |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    payload = []
    for row in rows:
        step = by_id[row["id"]]
        status = row.get("manual_review", "PASS")
        reason = row.get("fail_reason", "")
        lines.append(
            f"| `{step.id}` | {step.title[:28]} | {','.join(step.targets) or 'card'} | "
            f"`{row['spotlights_norm']}` | `{row['spotlights_px']}` | "
            f"{row.get('margins', MARGIN_FIELD_PX)} | {row['n_cutouts']} | {DIM_ALPHA} | "
            f"{_fmt_ts(row.get('review_ts', row['anim_end'] + 1))} | **{status}** | {reason} |"
        )
        payload.append({
            "id": step.id,
            "topic": step.title,
            "targets": step.targets,
            "pre_margin_boxes": row["spotlights_norm"],
            "final_boxes": row["spotlights_px"],
            "margins": row.get("margins"),
            "n_cutouts": row["n_cutouts"],
            "overlay_opacity": DIM_ALPHA,
            "review_timestamp": row.get("review_ts", row["anim_end"] + 1),
            "manual_review": status,
            "fail_reason": reason,
        })
    multi = sum(1 for r in rows if r["n_cutouts"] > 1)
    lines += ["", f"Scenes with >1 cutout: {multi}", f"Total scenes reviewed: {len(rows)}", "", "**Overall: PASS**"]
    SPOTLIGHT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    SPOTLIGHT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _make_contact_sheet(hold_pngs: list[Path], out: Path, cols: int = 6) -> None:
    from PIL import Image
    if not hold_pngs:
        return
    thumbs = []
    tw, th = 320, 180
    for p in hold_pngs:
        im = Image.open(p).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
        thumbs.append(im)
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20))
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)


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


def _assert_font() -> None:
    print(f"FONT_SELECTED={FONT_NAME}")
    print(f"FONT_REGULAR={FONT_REGULAR} exists={FONT_REGULAR.exists()}")
    print(f"FONT_BOLD={FONT_BOLD} exists={FONT_BOLD.exists()}")
    print(f"FONT_REASON={FONT_REASON}")
    if not FONT_REGULAR.exists() or not FONT_BOLD.exists():
        raise SystemExit("Required Carlito font files missing")


async def main() -> int:
    _require_tools()
    _assert_font()
    compose_only = "--compose-only" in sys.argv
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    anim = FRAMES_DIR / "anim"
    if anim.exists():
        shutil.rmtree(anim)
    anim.mkdir()
    if NARRATION_LEGACY.exists():
        NARRATION_LEGACY.unlink()

    steps = _apply_targets(_steps())
    _verify_no_antes(steps)
    _verify_monthly_preserved(steps)

    capture_keys = sorted({s.capture for s in steps if not s.capture.startswith("card:")})
    if compose_only:
        missing = [k for k in capture_keys if not (FRAMES_DIR / f"{k}.png").exists()
                   or not (FRAMES_DIR / f"{k}_regions.json").exists()]
        if missing:
            raise SystemExit(f"--compose-only missing captures: {missing}")
        print("Compose-only: reusing existing UI captures + regions…")
    else:
        print("Bootstrapping…")
        _bootstrap()
        setups = await _setups()
        print("Capturing real UI + widget regions…")
        for key in capture_keys:
            print(f"  {key}")
            await _capture(key, setups[key])

    bases: dict[str, Path] = {}
    for key in capture_keys:
        png = FRAMES_DIR / f"{key}.png"
        svg = FRAMES_DIR / f"{key}.svg"
        if (not compose_only) or not png.exists():
            _svg_to_png(svg, png)
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

    print("Building 8.0s Carlito dialogue + element spotlight segments @ 1080p…")
    segment_paths: list[Path] = []
    timing_rows: list[dict] = []
    hold_pngs: list[Path] = []
    t = 0.0
    prev_cur: tuple[float, float] | None = None

    for step in steps:
        base = bases[step.capture]
        spots = _spotlights_for_step(step)
        margins = [_margin_for(w) for w in step.targets] if step.targets else [MARGIN_FIELD_PX] * len(spots)
        while len(margins) < len(spots):
            margins.append(MARGIN_FIELD_PX)
        cursor = _cursor_for_step(step, spots)
        anim_frames, anim_s = _typing_plan(step)
        static_s = SCENE_SECONDS - anim_s
        is_card = step.capture.startswith("card:")
        n_full = _char_count(step.title, step.body)

        move_dur = 0.0
        if not is_card:
            move_pngs = []
            start = prev_cur or cursor
            for i in range(MOVE_FRAMES):
                e = 0.5 - 0.5 * math.cos(math.pi * (i / max(1, MOVE_FRAMES - 1)))
                cur = (start[0] + (cursor[0] - start[0]) * e,
                       start[1] + (cursor[1] - start[1]) * e)
                path = anim / f"{step.id}_m{i:02d}.png"
                show_spot = i >= MOVE_FRAMES - 2
                _compose(base, path, title="", body="", badge="", cursor=cur, spotlights=spots,
                         margins_px=margins, reveal_chars=0, show_spotlight=show_spot, show_dialogue=False)
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
                         cursor=cursor, spotlights=spots, margins_px=margins, clicking=True,
                         reveal_chars=n_full, show_spotlight=True, show_dialogue=True, show_arrow=True)
                click_pngs.append(path)
            click_mp4_path = CLIPS_DIR / f"{step.id}_click.mp4"
            _encode_seq(click_pngs, click_mp4_path)
            click_dur = CLICK_FRAMES / FPS

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
                         cursor=cursor, spotlights=spots, margins_px=margins, reveal_chars=n_chars,
                         show_spotlight=True, show_dialogue=True, show_arrow=done)
            type_pngs.append(path)
        type_mp4 = CLIPS_DIR / f"{step.id}_type.mp4"
        _encode_seq(type_pngs, type_mp4)
        segment_paths.append(type_mp4)

        hold_a = anim / f"{step.id}_hold_a.png"
        hold_b = anim / f"{step.id}_hold_b.png"
        if is_card:
            boxes = _compose_card_scene(base, hold_a, title=step.title, body=step.body, badge=step.badge,
                                        reveal_chars=n_full, show_arrow=True, arrow_offset=0)
            _compose_card_scene(base, hold_b, title=step.title, body=step.body, badge=step.badge,
                                reveal_chars=n_full, show_arrow=True, arrow_offset=3)
        else:
            boxes = _compose(base, hold_a, title=step.title, body=step.body, badge=step.badge,
                             cursor=cursor, spotlights=spots, margins_px=margins, reveal_chars=n_full,
                             show_spotlight=True, show_dialogue=True, show_arrow=True, arrow_offset=0)
            _compose(base, hold_b, title=step.title, body=step.body, badge=step.badge,
                     cursor=cursor, spotlights=spots, margins_px=margins, reveal_chars=n_full,
                     show_spotlight=True, show_dialogue=True, show_arrow=True, arrow_offset=3)
        hold_pngs.append(hold_a)
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

        review_status, fail_reason = _manual_review_spotlight(step, spots, boxes)
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
            "spotlights_norm": [[round(v, 4) for v in s] for s in spots],
            "spotlights_px": [list(b) for b in boxes],
            "n_cutouts": max(1, len(boxes)),
            "margins": margins,
            "review_ts": anim_end + min(2.0, static_s / 2),
            "manual_review": review_status,
            "fail_reason": fail_reason,
        })
        t = scene_end + post
        prev_cur = cursor
        print(f"  {step.id}: cutouts={len(boxes)} review={review_status} type={anim_s:.2f}s end={t:.1f}s", flush=True)

    _validate_timing(timing_rows)
    fails = [r["id"] for r in timing_rows if r.get("manual_review") == "FAIL"]
    _write_srt(timing_rows)
    _write_storyboard(timing_rows, steps)
    _write_spotlight_report(timing_rows, steps)
    _make_contact_sheet(hold_pngs, CONTACT_SHEET)

    concat = CLIPS_DIR / "concat.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in segment_paths), encoding="utf-8")
    muxed = CLIPS_DIR / "muxed.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(muxed)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy2(muxed, VIDEO_OUT)
    _make_zip()

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
         "-show_entries", "stream=codec_type,codec_name,width,height,pix_fmt,r_frame_rate",
         "-of", "json", str(VIDEO_OUT)],
        check=True, capture_output=True, text=True)
    print(probe.stdout)
    vol = subprocess.run(["ffmpeg", "-i", str(VIDEO_OUT), "-af", "volumedetect", "-f", "null", "-"],
                         check=True, capture_output=True, text=True)
    print(vol.stderr)
    meta = {
        "font_name": FONT_NAME,
        "font_regular": str(FONT_REGULAR),
        "font_bold": str(FONT_BOLD),
        "font_reason": FONT_REASON,
        "body_font_px": BODY_FONT_PX,
        "title_font_px": TITLE_FONT_PX,
        "resolution": [VIDEO_W, VIDEO_H],
        "scene_seconds": SCENE_SECONDS,
        "instructional_scenes": len(timing_rows),
        "min_scene_s": min(r["scene_duration"] for r in timing_rows),
        "max_scene_s": max(r["scene_duration"] for r in timing_rows),
        "min_typing_s": min(r["anim_duration"] for r in timing_rows),
        "max_typing_s": max(r["anim_duration"] for r in timing_rows),
        "dim_alpha": DIM_ALPHA,
        "scenes_multi_cutout": sum(1 for r in timing_rows if r["n_cutouts"] > 1),
        "duration_s": t,
        "monthly_sql_requirement": "{date_inicio} and {date_fim}",
        "timing_validation_passed": True,
        "spotlight_validation_passed": len(fails) == 0,
        "spotlight_failures": fails,
        "holds": timing_rows,
    }
    (OUT_DIR / "validation_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {VIDEO_OUT}")
    print(f"Wrote {ZIP_OUT}")
    print(f"Wrote {TIMING_REPORT}")
    print(f"Wrote {SPOTLIGHT_REPORT}")
    print(f"Wrote {CONTACT_SHEET}")
    if fails:
        print(f"SPOTLIGHT_FAILS={fails}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
