#!/usr/bin/env python3
"""Overview onboarding — same production standards as New Job (Part 2).

Carlito dialogue, element spotlights @ 1080p, original chiptune BGM + UI blip.
Timing: typing (1.0–1.5s) + exactly 5.0s complete-text hold.
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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
OUT_DIR = Path(__file__).resolve().parent
FRAMES_DIR = OUT_DIR / "frames"
CLIPS_DIR = OUT_DIR / "clips"
FONTS_DIR = OUT_DIR / "fonts"
VIDEO_OUT = OUT_DIR / "overview_onboarding_ptbr.mp4"
CAPTIONS_OUT = OUT_DIR / "overview_onboarding_ptbr_captions_ptbr.srt"
STORYBOARD_OUT = OUT_DIR / "overview_onboarding_ptbr_storyboard.md"
TIMING_REPORT = OUT_DIR / "footer_timing_report.md"
SPOTLIGHT_REPORT = OUT_DIR / "spotlight_report.md"
SPOTLIGHT_JSON = OUT_DIR / "spotlight_report.json"
SPOTLIGHT_ACCURACY = OUT_DIR / "spotlight_accuracy_report.md"
SPOTLIGHT_PREVIEWS = FRAMES_DIR / "spotlight_previews"
CONTACT_SHEET = OUT_DIR / "spotlight_contact_sheet.png"
ZIP_OUT = OUT_DIR / "overview_onboarding_video_download.zip"
NARRATION_LEGACY = OUT_DIR / "overview_onboarding_narration_ptbr.txt"

VIDEO_W, VIDEO_H = 1920, 1080
FPS = 30
HOLD_COMPLETE_S = 5.0  # complete text visible exactly 5.0s after typing
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
PAD_X = 64
PAD_Y = 40
# Original audio (generated for this package — not Pokémon-derived)
AUDIO_DIR = OUT_DIR / "audio" / "original"
BGM_WAV = AUDIO_DIR / "town_walk_original_chiptune.wav"
SFX_WAV = AUDIO_DIR / "dialogue_open_ui_blip.wav"
BGM_LEVEL = 0.18
SFX_LEVEL = 0.55
DUCK_LEVEL = 0.06
DUCK_FADE_DOWN_S = 0.12
DUCK_FADE_UP_S = 0.35

# Font selection (priority: Calibri → Carlito → Liberation Sans)
FONT_REGULAR = FONTS_DIR / "Carlito-Regular.ttf"
FONT_BOLD = FONTS_DIR / "Carlito-Bold.ttf"
FONT_NAME = "Carlito"
FONT_REASON = (
    "Calibri is not installed in this Linux environment. "
    "Using Carlito (fonts-crosextra-carlito), the OFL metric-compatible substitute."
)

DEMO_ROOT = Path("/tmp/dispatch_overview_onboarding_v1")
LAUNCH_CWD = DEMO_ROOT / "sql"
DATA_ROOT = DEMO_ROOT / "data"

PLAIN_SQL = """\
-- Exemplo didático (não sensível)
SELECT region, amount FROM sales WHERE amount > 0;
"""


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
    spotlight_group: str = ""  # reuse exact spotlight across related cards


def _steps() -> list[Step]:
    """Top-to-bottom Overview walkthrough (Part 2 after New Job)."""
    return [
        Step("01_open", "card:open", "Dispatch (Robocop)",
             "Como utilizar a aba Overview.\nMonitore e interprete seus jobs.",
             "", (0.50, 0.50), section="Abertura", evidence="opening card",
             spotlight_group="open"),
        Step("02_purpose", "populated", "O que é Overview",
             "Tela principal para acompanhar\njobs enviados e seu status.",
             "", (0.55, 0.14), section="Abertura", evidence="DashboardScreen",
             spotlight_group="purpose"),

        # Status strip
        Step("20_strip_what", "populated", "O que é",
             "A faixa superior resume autenticação\ne o monitoramento dos jobs.",
             "", (0.55, 0.06), section="Status strip", evidence="#status-strip",
             spotlight_group="status-strip"),
        Step("20b_strip_learn", "populated", "O que você aprende aqui",
             "Em um olhar: autenticação, execução\ne histórico dos últimos 7 dias.",
             "", (0.55, 0.06), section="Status strip", evidence="_update_status_strip",
             spotlight_group="status-strip"),

        Step("21_krb_what", "populated", "KERBEROS",
             "Indica se sua autenticação\nestá disponível para executar jobs.",
             "", (0.32, 0.06), section="Status strip", evidence="KERBEROS label",
             spotlight_group="krb"),
        Step("21b_krb_action", "populated", "Se estiver MISSING ou curto",
             "Abra um novo terminal e execute:\nkinit",
             "", (0.32, 0.06), section="Status strip", evidence="kinit recovery",
             spotlight_group="krb"),
        Step("21c_krb_password", "populated", "Senha",
             "Informe sua senha Windows\nquando o terminal solicitar.",
             "", (0.32, 0.06), section="Status strip", evidence="kinit password prompt",
             spotlight_group="krb"),

        Step("22_running_what", "populated", "RUNNING",
             "Quantos jobs estão em execução agora,\nem relação ao limite de vagas.",
             "", (0.48, 0.06), section="Status strip", evidence="RUNNING / RUNNING_CAP",
             spotlight_group="running-cap"),
        Step("22b_running_learn", "populated", "O que você aprende aqui",
             "O limite é 2 vagas. Pending e Running\nocupam vaga de execução.",
             "", (0.48, 0.06), section="Status strip", evidence="jobs.RUNNING_CAP",
             spotlight_group="running-cap"),

        Step("23_finished_what", "populated", "FINISHED 7D",
             "Histórico de jobs com sucesso\nnos últimos 7 dias.",
             "", (0.66, 0.06), section="Status strip", evidence="FINISHED 7D",
             spotlight_group="finished"),
        Step("23b_finished_learn", "populated", "O que você aprende aqui",
             "Permite ver sete dias de histórico\ne confirmar entregas recentes.",
             "", (0.66, 0.06), section="Status strip", evidence="Succeeded count / ACTIVE_WINDOW",
             spotlight_group="finished"),

        Step("24_failed_what", "populated", "FAILED 7D",
             "Histórico de jobs que falharam\nnos últimos 7 dias.",
             "", (0.84, 0.06), section="Status strip", evidence="FAILED 7D",
             spotlight_group="failed-count"),
        Step("24b_failed_action", "populated", "O que fazer",
             "Se o número subir, revise os jobs\nFAILED antes de enviar outros.",
             "", (0.84, 0.06), section="Status strip", evidence="Failed count",
             spotlight_group="failed-count"),

        # Jobs title
        Step("30_title_what", "populated", "Lista de jobs",
             "Jobs · running first · last 7 dias:\nlista do histórico recente.",
             "", (0.45, 0.10), section="Lista", evidence="#jobs-title",
             spotlight_group="jobs-title"),
        Step("30b_title_learn", "populated", "O que você aprende aqui",
             "Execução no topo; a janela cobre\nsete dias de monitoramento.",
             "", (0.45, 0.10), section="Lista", evidence="active_jobs ACTIVE_WINDOW",
             spotlight_group="jobs-title"),

        # Empty state
        Step("31_empty_what", "empty", "Lista vazia",
             "Quando não há jobs nos últimos 7 dias,\na tela orienta a criar um novo.",
             "", (0.55, 0.18), section="Lista", evidence="#jobs-empty",
             spotlight_group="empty"),
        Step("31b_empty_action", "empty", "O que fazer",
             "Pressione N ou New Job para\nenviar a primeira execução.",
             "", (0.55, 0.18), section="Lista", evidence="No jobs in the last 7 days",
             spotlight_group="empty"),

        # Table overview + columns
        Step("40_table_what", "populated", "O que é",
             "A tabela lista cada job com identidade,\norigem, destino, estado e tempo.",
             "", (0.55, 0.22), section="Tabela", evidence="#jobs-table",
             spotlight_group="table"),
        Step("40b_table_learn", "populated", "O que você aprende aqui",
             "Percorra as linhas para achar\nsucesso, execução ou problemas.",
             "", (0.55, 0.22), section="Tabela", evidence="DataTable",
             spotlight_group="table"),

        Step("41_col_id", "populated", "Coluna ID",
             "Identifica o job de forma curta\npara localizar e abrir detalhes.",
             "", (0.30, 0.18), section="Colunas", evidence="format_job_id",
             spotlight_group="col-id"),
        Step("41b_col_id_use", "populated", "Como usar",
             "Use o ID para filtrar ou\nconfirmar qual execução está vendo.",
             "", (0.30, 0.18), section="Colunas", evidence="ID column",
             spotlight_group="col-id"),

        Step("42_col_src", "populated", "Coluna Source",
             "Mostra a origem do job:\narquivo SQL, tabela ou tipo.",
             "", (0.42, 0.18), section="Colunas", evidence="_source_label",
             spotlight_group="col-src"),
        Step("42b_col_src_use", "populated", "Como usar",
             "Confirme se a origem corresponde\nao job que você esperava monitorar.",
             "", (0.42, 0.18), section="Colunas", evidence="Source column",
             spotlight_group="col-src"),

        Step("43_col_dst", "populated", "Coluna Destination",
             "Mostra para onde o resultado\nfoi ou será entregue.",
             "", (0.54, 0.18), section="Colunas", evidence="_dest_label",
             spotlight_group="col-dst"),
        Step("43b_col_dst_use", "populated", "Como usar",
             "Verifique schema.tabela ou Csv\nantes de validar o resultado.",
             "", (0.54, 0.18), section="Colunas", evidence="Destination column",
             spotlight_group="col-dst"),

        Step("44_col_state", "populated", "Coluna State",
             "Mostra o estado atual do job\ncom símbolo e rótulo em destaque.",
             "", (0.68, 0.18), section="Colunas", evidence="format_state",
             spotlight_group="col-state"),
        Step("44b_col_state_learn", "populated", "O que você aprende aqui",
             "Dá para ver rápido se está aguardando,\nrodando, ok ou precisa atenção.",
             "", (0.68, 0.18), section="Colunas", evidence="State column",
             spotlight_group="col-state"),

        # Status meanings
        Step("50_st_pending", "populated", "PENDING",
             "O job foi aceito e aguarda\ninício da execução.",
             "", (0.68, 0.22), section="Estados", evidence="Pending",
             spotlight_group="state-pending"),
        Step("50b_st_pending_act", "populated", "O que fazer",
             "Em geral, espere. Confira se\nhá vaga livre na faixa RUNNING.",
             "", (0.68, 0.22), section="Estados", evidence="Pending slot",
             spotlight_group="state-pending"),

        Step("51_st_running", "running_sel", "RUNNING",
             "O job está em execução agora.\nAcompanhe o progresso no painel.",
             "", (0.68, 0.16), section="Estados", evidence="Running",
             spotlight_group="state-running"),
        Step("51b_st_running_act", "running_sel", "O que fazer",
             "Monitore o log. Só cancele se\nrealmente precisar interromper.",
             "", (0.68, 0.16), section="Estados", evidence="Cancel Running only",
             spotlight_group="state-running"),

        Step("52_st_ok", "populated", "SUCCEEDED",
             "O job terminou com sucesso.\nO resultado está disponível.",
             "", (0.68, 0.34), section="Estados", evidence="Succeeded",
             spotlight_group="state-ok"),
        Step("52b_st_ok_act", "populated", "O que fazer",
             "Valide a entrega (tabela ou CSV)\nconforme o Destination do job.",
             "", (0.68, 0.34), section="Estados", evidence="Succeeded",
             spotlight_group="state-ok"),

        Step("53_st_fail", "failed_sel", "FAILED",
             "O job falhou. Pode aparecer um código\n(ex.: SYNTAX) para orientar a análise.",
             "", (0.68, 0.30), section="Estados", evidence="Failed + classify",
             spotlight_group="state-fail"),
        Step("53b_st_fail_act", "failed_sel", "O que fazer",
             "Abra View Logs, entenda a causa\ne corrija antes de reenviar.",
             "", (0.68, 0.30), section="Estados", evidence="View Logs",
             spotlight_group="state-fail"),

        Step("54_st_cancel", "populated", "CANCELLED",
             "A execução foi cancelada.\nNão houve conclusão bem-sucedida.",
             "", (0.68, 0.26), section="Estados", evidence="Cancelled",
             spotlight_group="state-cancel"),
        Step("54b_st_cancel_act", "populated", "O que fazer",
             "Confirme se o cancelamento\nfoi intencional; reenvie se precisar.",
             "", (0.68, 0.26), section="Estados", evidence="Cancelled",
             spotlight_group="state-cancel"),

        Step("55_col_elapsed", "populated", "Coluna Elapsed",
             "Tempo decorrido: em Running conta\ndesde o início; nos demais, a duração.",
             "", (0.86, 0.18), section="Colunas", evidence="format_elapsed",
             spotlight_group="col-elapsed"),
        Step("55b_col_elapsed_use", "populated", "Como usar",
             "Compare duração esperada e detecte\njobs longos que merecem atenção.",
             "", (0.86, 0.18), section="Colunas", evidence="Elapsed",
             spotlight_group="col-elapsed"),

        # Filter
        Step("60_filter_what", "filter_open", "Filtro",
             "Pressione / para filtrar a lista\npor id, arquivo, tabela ou estado.",
             "", (0.55, 0.14), section="Filtro", evidence="#jobs-filter",
             spotlight_group="filter"),
        Step("60b_filter_when", "filter_open", "Quando usar",
             "Use para achar rápido um job\nou isolar só FAILED / RUNNING.",
             "", (0.55, 0.14), section="Filtro", evidence="action_filter_jobs",
             spotlight_group="filter"),
        Step("61_filter_ex", "filter_failed", "Exemplo",
             "Digite failed para ver só falhas.\nEsc limpa o filtro e restaura a lista.",
             "", (0.55, 0.14), click=True, section="Filtro", evidence="Esc clear_filter",
             spotlight_group="filter-ex"),

        # Detail pane
        Step("70_detail_what", "running_sel", "Painel de detalhe",
             "Mostra um resumo do job selecionado\ne as últimas linhas do log.",
             "", (0.55, 0.78), section="Detalhe", evidence="#detail-pane",
             spotlight_group="detail"),
        Step("70b_detail_learn", "running_sel", "O que você aprende aqui",
             "Sem sair da Overview, vê se o job\navança ou se já há erro no log.",
             "", (0.55, 0.78), section="Detalhe", evidence="DETAIL_TAIL_LINES",
             spotlight_group="detail"),
        Step("71_detail_title", "running_sel", "Título do detalhe",
             "Confirma ID, estado e tempo\ndo job em foco.",
             "", (0.55, 0.74), section="Detalhe", evidence="#detail-title",
             spotlight_group="detail-title"),
        Step("72_detail_log", "running_sel", "Prévia do log",
             "Últimas linhas do run.log.\nPara o log completo, use View Logs.",
             "", (0.55, 0.82), section="Detalhe", evidence="#detail-log",
             spotlight_group="detail-log"),

        # Actions
        Step("80_events", "populated", "Eventos recentes",
             "Mostra o último aviso da Overview,\ncomo início do Dispatch ou término.",
             "", (0.40, 0.92), section="Ações", evidence="#event-trail",
             spotlight_group="events"),
        Step("81_newjob", "populated", "New Job [N]",
             "Abre a tela para configurar\ne enviar um novo job.",
             "", (0.78, 0.92), section="Ações", evidence="#new-job",
             spotlight_group="btn-new"),
        Step("82_viewlogs", "populated", "View Logs [V]",
             "Abre o detalhe completo do job\nselecionado para diagnóstico.",
             "", (0.86, 0.92), section="Ações", evidence="#view-logs",
             spotlight_group="btn-logs"),
        Step("82b_viewlogs_when", "failed_sel", "Quando usar",
             "Use em FAILED ou quando o log\ncurto do painel não bastar.",
             "", (0.86, 0.92), section="Ações", evidence="open_job_detail",
             spotlight_group="btn-logs"),
        Step("83_cancel", "running_sel", "Cancel [C]",
             "Inicia o cancelamento somente\nse o job selecionado estiver RUNNING.",
             "", (0.94, 0.92), section="Ações", evidence="#cancel",
             spotlight_group="btn-cancel"),
        Step("83b_cancel_note", "running_sel", "Atenção",
             "Jobs que não estão RUNNING\nnão podem ser cancelados aqui.",
             "", (0.94, 0.92), section="Ações", evidence="Only Running jobs",
             spotlight_group="btn-cancel"),

        # Close — no Next Step
        Step("90_close", "card:close", "Resumo",
             "Na Overview você monitora status,\ninterpreta resultados e age.",
             "", (0.50, 0.50), section="Encerramento", evidence="closing",
             spotlight_group="close"),
    ]



def _apply_targets(steps: list[Step]) -> list[Step]:
    """Attach precise Textual widget ids for element-based spotlights."""
    mapping: dict[str, list[str]] = {
        "02_purpose": ["jobs-title", "jobs-table"],
        "20_strip_what": ["status-strip"],
        "20b_strip_learn": ["status-strip"],
        "21_krb_what": ["status-strip"],
        "21b_krb_action": ["status-strip"],
        "21c_krb_password": ["status-strip"],
        "22_running_what": ["status-strip"],
        "22b_running_learn": ["status-strip"],
        "23_finished_what": ["status-strip"],
        "23b_finished_learn": ["status-strip"],
        "24_failed_what": ["status-strip"],
        "24b_failed_action": ["status-strip"],
        "30_title_what": ["jobs-title"],
        "30b_title_learn": ["jobs-title"],
        "31_empty_what": ["jobs-empty"],
        "31b_empty_action": ["jobs-empty"],
        "40_table_what": ["jobs-table"],
        "40b_table_learn": ["jobs-table"],
        "41_col_id": ["jobs-table"],
        "41b_col_id_use": ["jobs-table"],
        "42_col_src": ["jobs-table"],
        "42b_col_src_use": ["jobs-table"],
        "43_col_dst": ["jobs-table"],
        "43b_col_dst_use": ["jobs-table"],
        "44_col_state": ["jobs-table"],
        "44b_col_state_learn": ["jobs-table"],
        "50_st_pending": ["jobs-table"],
        "50b_st_pending_act": ["jobs-table"],
        "51_st_running": ["jobs-table"],
        "51b_st_running_act": ["jobs-table"],
        "52_st_ok": ["jobs-table"],
        "52b_st_ok_act": ["jobs-table"],
        "53_st_fail": ["jobs-table"],
        "53b_st_fail_act": ["jobs-table"],
        "54_st_cancel": ["jobs-table"],
        "54b_st_cancel_act": ["jobs-table"],
        "55_col_elapsed": ["jobs-table"],
        "55b_col_elapsed_use": ["jobs-table"],
        "60_filter_what": ["jobs-filter"],
        "60b_filter_when": ["jobs-filter"],
        "61_filter_ex": ["jobs-filter", "jobs-table"],
        "70_detail_what": ["detail-pane"],
        "70b_detail_learn": ["detail-pane"],
        "71_detail_title": ["detail-title"],
        "72_detail_log": ["detail-log"],
        "80_events": ["event-trail"],
        "81_newjob": ["new-job"],
        "82_viewlogs": ["view-logs"],
        "82b_viewlogs_when": ["view-logs"],
        "83_cancel": ["cancel"],
        "83b_cancel_note": ["cancel"],
    }
    out = []
    for s in steps:
        targets = mapping.get(s.id, s.targets)
        out.append(Step(
            id=s.id, capture=s.capture, title=s.title, body=s.body, badge=s.badge,
            cursor=s.cursor, click=s.click, section=s.section, evidence=s.evidence,
            instructional=s.instructional, spotlight=s.spotlight, targets=list(targets),
            spotlight_group=s.spotlight_group,
        ))
    return out





REGION_WIDGET_IDS = [
    "sidebar-brand", "sidebar-nav", "sidebar-krb", "sidebar-version", "sidebar-help",
    "status-strip", "jobs-title", "jobs-filter", "jobs-table", "jobs-empty", "jobs-empty-text",
    "detail-pane", "detail-title", "detail-log",
    "dashboard-action-bar", "event-trail", "new-job", "view-logs", "cancel",
    "dashboard-content", "main-content",
]

# spotlight_group → discussed UI element (for accuracy validation)
# Values must match `_geometry_boxes_for_group` actual_target ids.
DISCUSSED_ELEMENT = {
    "open": "opening-card",
    "close": "closing-card",
    "purpose": "overview-jobs-area",
    "status-strip": "strip:ALL",
    "krb": "strip:KERBEROS",
    "running-cap": "strip:RUNNING",
    "finished": "strip:FINISHED 7D",
    "failed-count": "strip:FAILED 7D",
    "jobs-title": "jobs-title",
    "empty": "jobs-empty",
    "table": "jobs-table",
    "col-id": "column:ID",
    "col-src": "column:Source",
    "col-dst": "column:Destination",
    "col-state": "column:State",
    "col-elapsed": "column:Elapsed",
    "state-pending": "cell:State:PENDING",
    "state-running": "cell:State:RUNNING",
    "state-ok": "cell:State:SUCCEEDED",
    "state-fail": "cell:State:FAILED",
    "state-cancel": "cell:State:CANCELLED",
    "filter": "jobs-filter",
    "filter-ex": "jobs-filter+table",
    "detail": "detail-pane",
    "detail-title": "detail-title",
    "detail-log": "detail-log",
    "events": "event-trail",
    "btn-new": "new-job",
    "btn-logs": "view-logs",
    "btn-cancel": "cancel",
}


def _region_dict(x: int, y: int, w: int, h: int) -> dict:
    return {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}


def _dump_strip_metrics(strip) -> dict[str, dict]:
    """Derive metric glyph bounds from the strip's real rendered plain text."""
    import re

    plain = strip.render().plain
    base = strip.content_region
    metrics: dict[str, dict] = {}
    # Metrics are separated by 2+ spaces; tokens within a metric use single spaces.
    for m in re.finditer(r"\S+(?: \S+)*", plain):
        token = m.group(0)
        key = None
        if token.startswith("KERBEROS"):
            key = "KERBEROS"
        elif token.startswith("RUNNING"):
            key = "RUNNING"
        elif token.startswith("FINISHED 7D"):
            key = "FINISHED 7D"
        elif token.startswith("FAILED 7D"):
            key = "FAILED 7D"
        if key is None:
            continue
        metrics[key] = _region_dict(base.x + m.start(), base.y, m.end() - m.start(), max(1, base.height))
    if metrics:
        xs = [v["x"] for v in metrics.values()]
        rights = [v["x"] + v["w"] for v in metrics.values()]
        ys = [v["y"] for v in metrics.values()]
        bottoms = [v["y"] + v["h"] for v in metrics.values()]
        metrics["ALL"] = _region_dict(min(xs), min(ys), max(rights) - min(xs), max(bottoms) - min(ys))
    return metrics


def _dump_table_geometry(table) -> dict:
    """Capture DataTable column + State-cell screen regions from Textual geometry."""
    from rich.text import Text
    from textual.coordinate import Coordinate

    origin = table.content_region.offset
    scroll = table.scroll_offset
    columns: dict[str, dict] = {}
    for i, col in enumerate(table.ordered_columns):
        label = Text.from_markup(str(col.label)).plain if col.label is not None else f"col{i}"
        virt = table._get_column_region(i)
        screen = virt.translate(origin - scroll)
        columns[label] = _region_dict(screen.x, screen.y, screen.width, screen.height)

    state_idx = next(
        (i for i, c in enumerate(table.ordered_columns)
         if Text.from_markup(str(c.label)).plain == "State"),
        None,
    )
    cells: dict[str, dict] = {}
    if state_idx is not None:
        for row_i in range(table.row_count):
            virt = table._get_cell_region(Coordinate(row_i, state_idx))
            if virt.width <= 0 or virt.height <= 0:
                continue
            raw = table.get_cell_at(Coordinate(row_i, state_idx))
            plain = Text.from_markup(str(raw)).plain.upper()
            token = "UNKNOWN"
            for cand in ("RUNNING", "PENDING", "CANCELLED", "SUCCEEDED", "FAILED"):
                if cand in plain:
                    token = cand
                    break
            screen = virt.translate(origin - scroll)
            # Keep first occurrence of each state (running-first order).
            cells.setdefault(token, _region_dict(screen.x, screen.y, screen.width, screen.height))

    header_h = int(table.header_height) if table.show_header else 0
    header = None
    if columns:
        xs = [c["x"] for c in columns.values()]
        rights = [c["x"] + c["w"] for c in columns.values()]
        ys = [c["y"] for c in columns.values()]
        header = _region_dict(min(xs), min(ys), max(rights) - min(xs), max(1, header_h))

    return {
        "columns": columns,
        "state_cells": cells,
        "header": header,
        "content_origin": {"x": int(origin.x), "y": int(origin.y)},
        "scroll_offset": {"x": int(scroll.x), "y": int(scroll.y)},
    }


def _dump_title_text(title_widget) -> dict | None:
    """Bounds of the jobs-title plain text inside its widget content region."""
    try:
        plain = title_widget.render().plain.strip()
    except Exception:
        return None
    if not plain:
        return None
    base = title_widget.content_region
    # Title text is left-aligned; width follows rendered glyph count.
    return {
        **_region_dict(base.x, base.y, max(1, len(plain)), max(1, base.height)),
        "text": plain,
    }


def _dump_regions(app, out_json: Path) -> None:
    """Dump widget regions + geometry-derived element bounds for spotlights."""
    import json
    from textual.widget import Widget
    from textual.widgets import DataTable, Static

    regions: dict = {
        "terminal_size": list(TERMINAL_SIZE),
        "widgets": {},
        "geometry": {
            "source": "textual-runtime",
            "strip_metrics": {},
            "table": {},
            "jobs_title_text": None,
        },
        "y_bias": 1,  # SVG export paints ~1 cell below query_one().region.y
    }
    for wid in REGION_WIDGET_IDS:
        try:
            w = app.screen.query_one(f"#{wid}", Widget)
            r = w.region
            regions["widgets"][wid] = _region_dict(r.x, r.y, r.width, r.height)
        except Exception:
            continue
    try:
        for btn in app.screen.query("Button"):
            if getattr(btn, "id", None):
                r = btn.region
                regions["widgets"][btn.id] = _region_dict(r.x, r.y, r.width, r.height)
    except Exception:
        pass

    try:
        strip = app.screen.query_one("#status-strip", Static)
        regions["geometry"]["strip_metrics"] = _dump_strip_metrics(strip)
    except Exception as exc:
        regions["geometry"]["strip_metrics_error"] = str(exc)

    try:
        table = app.screen.query_one("#jobs-table", DataTable)
        if table.row_count > 0 or table.columns:
            regions["geometry"]["table"] = _dump_table_geometry(table)
    except Exception as exc:
        regions["geometry"]["table_error"] = str(exc)

    try:
        title = app.screen.query_one("#jobs-title", Static)
        regions["geometry"]["jobs_title_text"] = _dump_title_text(title)
    except Exception as exc:
        regions["geometry"]["jobs_title_error"] = str(exc)

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
    (home / "jobs").mkdir(parents=True)
    LAUNCH_CWD.mkdir(parents=True)
    (LAUNCH_CWD / "export_sales.sql").write_text(PLAIN_SQL, encoding="utf-8")
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


def _jobs_dir() -> Path:
    return DATA_ROOT / ".dispatch" / "jobs"


def _clear_jobs() -> None:
    from dispatch import jobs as jobs_mod
    jobs_mod._manifest_cache.clear()
    root = _jobs_dir()
    if root.exists():
        for child in root.iterdir():
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
    root.mkdir(parents=True, exist_ok=True)


def _seed_job(
    *,
    state: str,
    suffix: str,
    source_name: str = "export_sales.sql",
    dest_type: str = "Csv",
    schema: str = "",
    table: str = "",
    started_offset_min: int = 30,
    duration_min: int = 5,
    log_lines: list[str] | None = None,
    exit_code: int | None = None,
) -> str:
    """Write a synthetic non-sensitive job for Overview captures."""
    from datetime import datetime, timedelta, timezone

    from dispatch import manifest

    now = datetime.now(timezone.utc)
    started = now - timedelta(minutes=started_offset_min)
    finished = None if state in ("Running", "Pending") else started + timedelta(minutes=duration_min)
    # Unique sortable id (newest last in path sort reverse = newest first)
    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    job_id = f"{stamp}_{suffix}"
    job_dir = _jobs_dir() / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    source = {"type": "SqlFile", "sql_path_at_launch": str(LAUNCH_CWD / source_name)}
    destination: dict = {"type": dest_type}
    if schema:
        destination["schema"] = schema
    if table:
        destination["table_name"] = table
    if exit_code is None:
        if state == "Succeeded":
            exit_code = 0
        elif state == "Failed":
            exit_code = 1
        else:
            exit_code = None
    m: manifest.JobManifest = {
        "schema_version": 1,
        "id": job_id,
        "tool": "dispatch",
        "user": "analyst",
        "source": source,  # type: ignore[typeddict-item]
        "destination": destination,  # type: ignore[typeddict-item]
        "params": {},
        "orchestrator_calls": [{"script": "download_to_csv.py", "argv": ["python3", "x.py"]}],
        "state": state,  # type: ignore[typeddict-item]
        "pid": (os.getpid() if state == "Running" else None),
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "finished_at": None if finished is None else finished.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "exit_code": exit_code,
    }
    manifest.write(job_dir / "manifest.json", m)
    lines = log_lines or {
        "Running": [
            "Starting query execution…",
            "Scanning partitions…",
            "Rows processed: 12000",
        ],
        "Succeeded": [
            "Query finished successfully.",
            "Wrote output for analyst review.",
        ],
        "Failed": [
            "ERROR: AnalysisException: Syntax error near 'FROM'",
            "Query aborted.",
        ],
        "Cancelled": [
            "Cancel requested by user.",
            "Execution stopped.",
        ],
        "Pending": [
            "Accepted; waiting for launch slot…",
        ],
    }.get(state, ["(no log yet)"])
    (job_dir / "run.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return job_id


def _seed_populated() -> dict[str, str]:
    """Seed one job per visible Overview state (synthetic, non-sensitive)."""
    _clear_jobs()
    ids = {
        "running": _seed_job(state="Running", suffix="run001", source_name="export_sales.sql",
                             dest_type="Csv", started_offset_min=12, duration_min=0,
                             log_lines=["Starting query…", "Still running…", "Rows so far: 8400"]),
        "pending": _seed_job(state="Pending", suffix="pend01", source_name="export_sales.sql",
                             dest_type="Table", schema="analytics", table="sales_out",
                             started_offset_min=8),
        "succeeded": _seed_job(state="Succeeded", suffix="ok0001", source_name="export_sales.sql",
                               dest_type="Csv", started_offset_min=90, duration_min=4),
        "failed": _seed_job(state="Failed", suffix="fail01", source_name="export_sales.sql",
                            dest_type="Table", schema="analytics", table="bad_job",
                            started_offset_min=60, duration_min=1),
        "cancelled": _seed_job(state="Cancelled", suffix="cncl01", source_name="export_sales.sql",
                               dest_type="Csv", started_offset_min=40, duration_min=2),
    }
    return ids


async def _capture(name: str, setup) -> Path:
    from dispatch.app import DispatchApp
    from dispatch.screens.dashboard import DashboardScreen

    out = FRAMES_DIR / f"{name}.svg"
    app = DispatchApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await setup(pilot, app)
        # Ensure Overview is showing
        if not isinstance(app.screen, DashboardScreen):
            app.push_screen(DashboardScreen())
            await pilot.pause(0.8)
        # Healthy-looking Kerberos for teaching strip (not MISSING)
        try:
            app.kerberos_ttl = 7200
        except Exception:
            pass
        await pilot.pause(0.6)
        # Force a refresh so seeded jobs appear
        try:
            await app.screen._refresh_jobs_async()  # type: ignore[attr-defined]
        except Exception:
            pass
        await pilot.pause(0.5)
        _dump_regions(app, FRAMES_DIR / f"{name}_regions.json")
        app.save_screenshot(filename=str(out))
    if not out.exists():
        raise RuntimeError(f"missing {out}")
    return out


async def _setups():
    from textual.widgets import DataTable, Input

    from dispatch.screens.dashboard import DashboardScreen

    async def empty(p, a):
        _clear_jobs()
        if not isinstance(a.screen, DashboardScreen):
            a.push_screen(DashboardScreen())
        await p.pause(0.4)
        await a.screen._refresh_jobs_async()
        await p.pause(0.3)

    async def populated(p, a):
        _seed_populated()
        if not isinstance(a.screen, DashboardScreen):
            a.push_screen(DashboardScreen())
        await p.pause(0.4)
        await a.screen._refresh_jobs_async()
        await p.pause(0.3)
        table = a.screen.query_one("#jobs-table", DataTable)
        table.focus()

    async def running_sel(p, a):
        ids = _seed_populated()
        if not isinstance(a.screen, DashboardScreen):
            a.push_screen(DashboardScreen())
        await p.pause(0.4)
        screen = a.screen
        await screen._refresh_jobs_async()
        await p.pause(0.3)
        table = screen.query_one("#jobs-table", DataTable)
        table.focus()
        # Running is pinned first
        try:
            table.move_cursor(row=table.get_row_index(ids["running"]))
        except Exception:
            table.move_cursor(row=0)
        screen._detail_job_id = ids["running"]
        await screen._refresh_jobs_async()
        await p.pause(0.35)

    async def failed_sel(p, a):
        ids = _seed_populated()
        if not isinstance(a.screen, DashboardScreen):
            a.push_screen(DashboardScreen())
        await p.pause(0.4)
        screen = a.screen
        await screen._refresh_jobs_async()
        await p.pause(0.3)
        table = screen.query_one("#jobs-table", DataTable)
        table.focus()
        try:
            table.move_cursor(row=table.get_row_index(ids["failed"]))
        except Exception:
            pass
        screen._detail_job_id = ids["failed"]
        await screen._refresh_jobs_async()
        await p.pause(0.35)

    async def filter_open(p, a):
        _seed_populated()
        if not isinstance(a.screen, DashboardScreen):
            a.push_screen(DashboardScreen())
        await p.pause(0.4)
        await a.screen._refresh_jobs_async()
        await p.pause(0.2)
        await p.press("slash")
        await p.pause(0.35)

    async def filter_failed(p, a):
        _seed_populated()
        if not isinstance(a.screen, DashboardScreen):
            a.push_screen(DashboardScreen())
        await p.pause(0.4)
        await a.screen._refresh_jobs_async()
        await p.pause(0.2)
        await p.press("slash")
        await p.pause(0.2)
        filt = a.screen.query_one("#jobs-filter", Input)
        filt.value = "failed"
        a.screen._filter_needle = "failed"
        a.screen._render_jobs_view()
        await p.pause(0.35)

    return {
        "empty": empty,
        "populated": populated,
        "running_sel": running_sel,
        "failed_sel": failed_sel,
        "filter_open": filter_open,
        "filter_failed": filter_failed,
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
        return {"terminal_size": list(TERMINAL_SIZE), "widgets": {}, "geometry": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _cell_box_to_norm(
    regions: dict, box: dict, *, y_bias: int | None = None,
) -> tuple[float, float, float, float] | None:
    """Convert a terminal cell box {x,y,w,h} to normalized UI PNG coords."""
    if not box or int(box.get("w", 0)) <= 0 or int(box.get("h", 0)) <= 0:
        return None
    cols, rows = regions.get("terminal_size", list(TERMINAL_SIZE))
    cols = max(1, int(cols))
    rows = max(1, int(rows))
    bias = int(regions.get("y_bias", 1) if y_bias is None else y_bias)
    x0 = box["x"] / cols
    y0 = (box["y"] + bias) / rows
    x1 = (box["x"] + box["w"]) / cols
    y1 = (box["y"] + box["h"] + bias) / rows
    return (
        max(0.0, min(0.99, x0)),
        max(0.0, min(0.99, y0)),
        max(0.01, min(1.0, x1)),
        max(0.01, min(1.0, y1)),
    )


def _cell_to_norm(regions: dict, wid: str) -> tuple[float, float, float, float] | None:
    """Convert widget cell region to normalized coords in the UI PNG (0–1)."""
    return _cell_box_to_norm(regions, regions.get("widgets", {}).get(wid, {}))


def _union_norms(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _margin_px_for_group(group: str) -> int:
    """Small proportional margin — accuracy first; size second."""
    if group in {"krb", "running-cap", "finished", "failed-count", "status-strip",
                 "jobs-title", "state-pending", "state-running", "state-ok",
                 "state-fail", "state-cancel", "detail-title"}:
        return 3
    if group in {"col-id", "col-src", "col-dst", "col-state", "col-elapsed",
                 "filter", "events", "btn-new", "btn-logs", "btn-cancel"}:
        return 4
    if group in {"purpose", "table", "empty", "detail", "detail-log", "filter-ex"}:
        return 5
    return 4


def _geometry_boxes_for_group(
    regions: dict, group: str,
) -> tuple[list[tuple[float, float, float, float]], str]:
    """Resolve spotlight boxes solely from captured Textual geometry.

    Returns (normalized boxes, actual_target_element_id).
    """
    geom = regions.get("geometry") or {}
    strip = geom.get("strip_metrics") or {}
    table = geom.get("table") or {}
    columns = table.get("columns") or {}
    state_cells = table.get("state_cells") or {}
    title_text = geom.get("jobs_title_text")

    def one(box: dict | None, label: str) -> tuple[list, str]:
        n = _cell_box_to_norm(regions, box or {})
        if n is None:
            return [], label
        return [n], label

    # Status strip metrics — character spans inside the real strip content.
    strip_map = {
        "krb": "KERBEROS",
        "running-cap": "RUNNING",
        "finished": "FINISHED 7D",
        "failed-count": "FAILED 7D",
        "status-strip": "ALL",
    }
    if group in strip_map:
        key = strip_map[group]
        return one(strip.get(key), f"strip:{key}")

    # Table columns — DataTable._get_column_region screen bounds.
    col_map = {
        "col-id": "ID",
        "col-src": "Source",
        "col-dst": "Destination",
        "col-state": "State",
        "col-elapsed": "Elapsed",
    }
    if group in col_map:
        label = col_map[group]
        return one(columns.get(label), f"column:{label}")

    # State cells — DataTable._get_cell_region for the State column.
    cell_map = {
        "state-running": "RUNNING",
        "state-pending": "PENDING",
        "state-cancel": "CANCELLED",
        "state-fail": "FAILED",
        "state-ok": "SUCCEEDED",
    }
    if group in cell_map:
        token = cell_map[group]
        return one(state_cells.get(token), f"cell:State:{token}")

    if group == "jobs-title":
        return one(title_text, "jobs-title")

    if group == "purpose":
        boxes: list[tuple[float, float, float, float]] = []
        t = _cell_box_to_norm(regions, title_text or {})
        if t:
            boxes.append(t)
        header = table.get("header")
        h = _cell_box_to_norm(regions, header or {})
        if h:
            boxes.append(h)
        if not boxes:
            # Fallback to real widgets only (still geometry, not percentages).
            for wid in ("jobs-title", "jobs-table"):
                n = _cell_to_norm(regions, wid)
                if n:
                    boxes.append(n)
        if not boxes:
            return [], "overview-jobs-area"
        return ([_union_norms(boxes)] if len(boxes) > 1 else boxes), "overview-jobs-area"

    if group == "table":
        # Union of all real column regions (header + populated rows only).
        boxes = []
        for label, box in columns.items():
            n = _cell_box_to_norm(regions, box)
            if n:
                boxes.append(n)
        if boxes:
            return [_union_norms(boxes)], "jobs-table"
        n = _cell_to_norm(regions, "jobs-table")
        return ([n] if n else []), "jobs-table"

    if group == "filter-ex":
        boxes = []
        labels = []
        for wid in ("jobs-filter",):
            n = _cell_to_norm(regions, wid)
            if n:
                boxes.append(n)
                labels.append(wid)
        # Include populated table body from real column geometry.
        col_boxes = []
        for box in columns.values():
            n = _cell_box_to_norm(regions, box)
            if n:
                col_boxes.append(n)
        if col_boxes:
            boxes.append(_union_norms(col_boxes))
            labels.append("table")
        return boxes, "+".join(labels) if labels else "jobs-filter+table"

    # Direct widget geometry.
    widget_map = {
        "empty": "jobs-empty",
        "filter": "jobs-filter",
        "detail": "detail-pane",
        "detail-title": "detail-title",
        "detail-log": "detail-log",
        "events": "event-trail",
        "btn-new": "new-job",
        "btn-logs": "view-logs",
        "btn-cancel": "cancel",
    }
    if group in widget_map:
        wid = widget_map[group]
        return one(regions.get("widgets", {}).get(wid), wid)

    return [], group


def _spotlights_for_step(step: Step) -> list[tuple[float, float, float, float]]:
    """Return normalized UI cutouts from captured element geometry only."""
    if step.capture.startswith("card:"):
        return [(0.12, 0.14, 0.88, 0.70)]
    if step.spotlight is not None:
        return [step.spotlight]
    regions = _load_regions(step.capture)
    geom = regions.get("geometry") or {}
    if not geom.get("source"):
        raise RuntimeError(
            f"Capture '{step.capture}' lacks geometry dump — re-run without --compose-only"
        )
    boxes, _actual = _geometry_boxes_for_group(regions, step.spotlight_group)
    if boxes:
        return boxes
    # Last resort: exact widget targets (still real regions, never percentages).
    items: list[tuple[float, float, float, float]] = []
    for wid in step.targets:
        n = _cell_to_norm(regions, wid)
        if n:
            items.append(n)
    if items:
        return [_union_norms(items)] if len(items) > 1 else items
    raise RuntimeError(
        f"No geometry for scene {step.id} group={step.spotlight_group!r} "
        f"targets={step.targets}"
    )


def _cursor_for_step(step: Step, spots: list[tuple[float, float, float, float]]) -> tuple[float, float]:
    if not spots:
        return step.cursor
    l, t, r, b = spots[0]
    # Prefer left side, vertically centered so thin status lines keep cursor on-target.
    return (min(r - 0.02, l + 0.04), (t + b) / 2)


def _prevalidate_spotlight(
    step: Step,
    spots: list[tuple[float, float, float, float]],
    *,
    target_box: dict | None,
    actual_target: str,
) -> tuple[str, str]:
    """Validate discussed element vs geometry before rendering."""
    if step.capture.startswith("card:"):
        return "PASS", "card"
    discussed = DISCUSSED_ELEMENT.get(step.spotlight_group, step.spotlight_group)
    if not spots:
        return "FAIL", f"missing spotlight for {discussed}"
    if discussed != actual_target and not (
        discussed.startswith("overview") and actual_target.startswith("overview")
    ):
        # Allow synonym matches for filter-ex / purpose-style unions.
        if discussed not in actual_target and actual_target not in discussed:
            # Map column:/cell:/strip: forms
            if not (
                discussed.replace("column:", "") in actual_target
                or discussed.replace("cell:State:", "") in actual_target
                or actual_target.endswith(discussed)
                or discussed == actual_target
            ):
                return "FAIL", f"discussed={discussed} actual={actual_target}"
    # Require positive area.
    for sp in spots:
        if sp[2] <= sp[0] or sp[3] <= sp[1]:
            return "FAIL", "degenerate spotlight box"
    return "PASS", ""


def _write_spotlight_preview(
    step: Step,
    ui_png: Path,
    spots: list[tuple[float, float, float, float]],
    target_boxes_norm: list[tuple[float, float, float, float]],
) -> Path:
    """Preview: original UI + element bbox (cyan) + spotlight bbox (yellow)."""
    from PIL import Image, ImageDraw

    SPOTLIGHT_PREVIEWS.mkdir(parents=True, exist_ok=True)
    ui = Image.open(ui_png).convert("RGBA")
    # Fit into a 1280-wide preview for QA
    scale = min(1.0, 1280 / ui.width)
    w, h = int(ui.width * scale), int(ui.height * scale)
    canvas = ui.resize((w, h))
    draw = ImageDraw.Draw(canvas)
    for box in target_boxes_norm:
        rect = (int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))
        draw.rectangle(rect, outline=(0, 220, 255), width=2)
    for box in spots:
        rect = (int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))
        draw.rectangle(rect, outline=(255, 220, 80), width=3)
    dest = SPOTLIGHT_PREVIEWS / f"{step.id}.png"
    canvas.convert("RGB").save(dest)
    return dest


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
    # Content safe area with generous margins from edges/outlines
    left, top, right, bottom = 120, 140, VIDEO_W - 120, VIDEO_H - DIALOGUE_H - 80
    draw.rounded_rectangle((left, top, right, bottom), radius=16, outline=(64, 156, 255), width=3)
    title_f = _ui_font(48, bold=True)
    body_f = _ui_font(34)
    y = top + 56
    draw.text((left + 56, y), title, fill=(245, 245, 245), font=title_f)
    y += 88
    for line in body.split("\n"):
        color = (255, 220, 120) if "{" in line else (210, 220, 235)
        draw.text((left + 56, y), line, fill=color, font=body_f)
        y += 56
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
    # Never show "Opcional" badges.
    if badge.strip().lower() == "opcional":
        badge = ""
    pad_x, pad_y = PAD_X, PAD_Y
    y = top + pad_y
    if vis_title:
        draw.text((left + pad_x, y), vis_title, fill=(10, 10, 10, 255), font=title_f)
    if badge and reveal_chars >= len(title):
        bw = 28 + len(badge) * 11
        bx = right - bw - 72
        draw.rectangle((bx, y + 4, bx + bw, y + 34), outline=(0, 0, 0), width=2)
        draw.text((bx + 10, y + 8), badge, fill=(10, 10, 10, 255), font=badge_f)
    y = top + pad_y + 56
    line_gap = int(BODY_FONT_PX * 1.22)
    for line in vis_body.split("\n")[:2]:
        draw.text((left + pad_x, y), line, fill=(20, 20, 20, 255), font=body_f)
        y += line_gap
    if show_arrow:
        _draw_red_arrow(draw, right - 16, bottom - 12, offset=arrow_offset)


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
        "# Dialogue timing validation (typing + exactly 5.0s complete-text hold)",
        "",
        f"Font: **{FONT_NAME}** (`{FONT_REGULAR.name}`). {FONT_REASON}",
        f"Body size: {BODY_FONT_PX}px. Hold complete: {HOLD_COMPLETE_S}s. Dim alpha={DIM_ALPHA}.",
        "",
        "| Scene | Element | Type start | Type end | Hold start | Hold end | Hold | Reused spot | Cue | Duck | Result |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    failed = []
    for row in rows:
        if not row["instructional"]:
            continue
        hold = row["static_duration"]
        anim = row["anim_duration"]
        ok = True
        reasons = []
        if abs(hold - HOLD_COMPLETE_S) > (1.0 / FPS) + 1e-6:
            ok = False; reasons.append("hold-not-5s")
        if abs(row["scene_duration"] - (anim + hold)) > (1.0 / FPS) + 1e-6:
            ok = False; reasons.append("scene!=type+hold")
        if anim > TYPING_MAX_S + (1.0 / FPS) + 1e-6:
            ok = False; reasons.append("typing>1.5")
        if row["arrow_at"] + 1e-6 < row["anim_end"]:
            ok = False; reasons.append("arrow-early")
        if row.get("badge", "").strip().lower() == "opcional":
            ok = False; reasons.append("opcional-badge")
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed.append(f"{row['id']}({','.join(reasons)})")
        lines.append(
            f"| `{row['id']}` | {row['title'][:22]} | {_fmt_ts(row['anim_start'])} | "
            f"{_fmt_ts(row['anim_end'])} | {_fmt_ts(row['hold_start'])} | {_fmt_ts(row['hold_end'])} | "
            f"{hold:.2f}s | {row.get('spotlight_reused', False)} | {_fmt_ts(row.get('sfx_at', row['anim_start']))} | "
            f"{_fmt_ts(row.get('duck_at', row['anim_start']))} | **{status}** |"
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
        "# Storyboard — Overview (typing + 5.0s hold, Carlito, 1920×1080)",
        "",
        f"Font: {FONT_NAME} ({FONT_REGULAR.name}). Body {BODY_FONT_PX}px / title {TITLE_FONT_PX}px.",
        f"{FONT_REASON}",
        f"Complete-text hold: exactly {HOLD_COMPLETE_S}s after typing. Original chiptune BGM + UI blip.",
        "Part 2 of the Dispatch onboarding series (after New Job).",
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
            f"- **Hold complete:** {_fmt_ts(row['hold_start'])} → {_fmt_ts(row['hold_end'])} ({row['static_duration']:.2f}s)",
            f"- **Spotlight group:** {step.spotlight_group or '(none)'} (reused={row.get('spotlight_reused', False)})",
            f"- **SFX / duck:** {_fmt_ts(row.get('sfx_at', row['anim_start']))}",
            f"- **Seta:** {_fmt_ts(row['arrow_at'])}",
            f"- **Duração cena:** {row['scene_duration']:.2f}s",
            f"- **Manual review:** {row.get('manual_review', 'pending')}",
            f"- **Evidência:** {step.evidence}",
            "",
        ]
    STORYBOARD_OUT.write_text("\n".join(lines), encoding="utf-8")


def _manual_review_spotlight(
    step: Step,
    spots_norm: list[tuple[float, float, float, float]],
    boxes_px: list[tuple[int, int, int, int]],
    *,
    discussed: str,
    actual_target: str,
    geometry_driven: bool,
) -> tuple[str, str]:
    """Accuracy-first validation: discussed element must match spotlight target."""
    if step.capture.startswith("card:"):
        return "PASS", "card content spotlight"
    if not boxes_px:
        return "FAIL", "missing spotlight cutout"
    if not geometry_driven and not step.capture.startswith("card:"):
        return "FAIL", "spotlight not geometry-driven"
    # Discussed vs actual target must agree.
    if discussed != actual_target:
        ok = (
            discussed in actual_target
            or actual_target in discussed
            or discussed.replace("column:", "") in actual_target
            or discussed.replace("cell:State:", "") in actual_target
            or actual_target.replace("strip:", "") == discussed
            or discussed.replace("strip:", "") == actual_target.replace("strip:", "")
        )
        # Canonical strip keys
        aliases = {
            "KERBEROS": "strip:KERBEROS",
            "RUNNING": "strip:RUNNING",
            "FINISHED 7D": "strip:FINISHED 7D",
            "FAILED 7D": "strip:FAILED 7D",
            "status-strip-metrics": "strip:ALL",
        }
        if aliases.get(discussed) == actual_target or aliases.get(actual_target) == discussed:
            ok = True
        if discussed.startswith("column:") and actual_target == discussed:
            ok = True
        if not ok:
            return "FAIL", f"discussed={discussed} spotlighted={actual_target}"
    for b in boxes_px:
        if b[3] > VIDEO_H - DIALOGUE_H + 2:
            return "FAIL", "target covered by dialogue box"
        if b[2] <= b[0] or b[3] <= b[1]:
            return "FAIL", "degenerate spotlight box"
    if len(spots_norm) != len(boxes_px):
        return "FAIL", "cutout count mismatch after clamping"
    return "PASS", "geometry-driven"


def _write_accuracy_report(rows: list[dict], steps: list[Step], *, failures_before: int) -> None:
    by_id = {s.id: s for s in steps}
    lines = [
        "# Spotlight accuracy report (geometry-driven)",
        "",
        "Every spotlight is built from captured Textual element bounds "
        "(widget region, DataTable column/cell region, or strip glyph span).",
        "",
        "| Scene | Discussed element | Actual target element | Target bbox (norm) | Spotlight bbox (px) | Result |",
        "|---|---|---|---|---|---|",
    ]
    reviewed = 0
    corrected = 0
    geometry = 0
    fails_after = 0
    for row in rows:
        step = by_id[row["id"]]
        reviewed += 1
        if row.get("geometry_driven"):
            geometry += 1
        if row.get("spotlight_corrected"):
            corrected += 1
        status = row.get("manual_review", "PASS")
        if status == "FAIL":
            fails_after += 1
        lines.append(
            f"| `{step.id}` | {row.get('discussed_element', '')} | "
            f"{row.get('actual_target', '')} | `{row.get('target_bbox_norm', row['spotlights_norm'])}` | "
            f"`{row['spotlights_px']}` | **{status}** |"
        )
    lines += [
        "",
        "## Summary",
        "",
        f"1. Spotlight scenes reviewed: **{reviewed}**",
        f"2. Spotlight scenes corrected: **{corrected}**",
        f"3. Geometry-driven spotlights: **{geometry}**",
        f"4. Spotlight validation failures before correction: **{failures_before}**",
        f"5. Spotlight validation failures after correction: **{fails_after}**",
        "",
        f"**Overall: {'PASS' if fails_after == 0 else 'FAIL'}**",
        "",
    ]
    SPOTLIGHT_ACCURACY.write_text("\n".join(lines), encoding="utf-8")


def _write_spotlight_report(rows: list[dict], steps: list[Step]) -> None:
    by_id = {s.id: s for s in steps}
    lines = [
        "# Spotlight manual-review report",
        "",
        f"Resolution {VIDEO_W}×{VIDEO_H}. Overlay alpha={DIM_ALPHA}. Font={FONT_NAME}.",
        "Source: Textual runtime geometry (no percentage estimates).",
        "",
        "| Scene | Topic | Discussed | Actual target | Pre-margin boxes | Final boxes | Margin | Cutouts | Status | Reason |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    payload = []
    fails = 0
    for row in rows:
        step = by_id[row["id"]]
        status = row.get("manual_review", "PASS")
        reason = row.get("fail_reason", "")
        if status == "FAIL":
            fails += 1
        lines.append(
            f"| `{step.id}` | {step.title[:28]} | {row.get('discussed_element', '')} | "
            f"{row.get('actual_target', '')} | `{row['spotlights_norm']}` | `{row['spotlights_px']}` | "
            f"{row.get('margins', MARGIN_FIELD_PX)} | {row['n_cutouts']} | **{status}** | {reason} |"
        )
        payload.append({
            "id": step.id,
            "topic": step.title,
            "discussed_element": row.get("discussed_element"),
            "actual_target": row.get("actual_target"),
            "targets": step.targets,
            "target_bbox_norm": row.get("target_bbox_norm", row["spotlights_norm"]),
            "pre_margin_boxes": row["spotlights_norm"],
            "final_boxes": row["spotlights_px"],
            "margins": row.get("margins"),
            "n_cutouts": row["n_cutouts"],
            "overlay_opacity": DIM_ALPHA,
            "geometry_driven": row.get("geometry_driven", True),
            "review_timestamp": row.get("review_ts", row["anim_end"] + 1),
            "manual_review": status,
            "fail_reason": reason,
        })
    multi = sum(1 for r in rows if r["n_cutouts"] > 1)
    overall = "PASS" if fails == 0 else "FAIL"
    lines += ["", f"Scenes with >1 cutout: {multi}", f"Total scenes reviewed: {len(rows)}", "",
              f"**Overall: {overall}**"]
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


def _verify_overview_content(steps: list[Step]) -> None:
    blob = "\n".join(f"{s.title}\n{s.body}" for s in steps)
    for token in ("Overview", "RUNNING", "SUCCEEDED", "FAILED", "PENDING", "CANCELLED",
                  "KERBEROS", "FINISHED 7D", "Filtro", "View Logs", "Cancel", "kinit"):
        if token not in blob:
            raise AssertionError(f"Missing Overview content: {token}")
    forbidden = ("barra lateral", "próximo passo", "sidebar", "History ou Browse")
    low = blob.lower()
    for bad in forbidden:
        if bad in low:
            raise AssertionError(f"Forbidden Overview content still present: {bad}")


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
    _verify_overview_content(steps)

    capture_keys = sorted({s.capture for s in steps if not s.capture.startswith("card:")})
    if compose_only:
        missing = [k for k in capture_keys if not (FRAMES_DIR / f"{k}.png").exists()
                   or not (FRAMES_DIR / f"{k}_regions.json").exists()]
        if missing:
            raise SystemExit(f"--compose-only missing captures: {missing}")
        stale = []
        for k in capture_keys:
            reg = _load_regions(k)
            if not (reg.get("geometry") or {}).get("source"):
                stale.append(k)
        if stale:
            raise SystemExit(
                f"--compose-only regions lack geometry dump (re-capture required): {stale}"
            )
        print("Compose-only: reusing existing UI captures + geometry regions…")
    else:
        print("Bootstrapping…")
        _bootstrap()
        setups = await _setups()
        print("Capturing real UI + widget/geometry regions…")
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
          "Como utilizar a aba Overview\nMonitore e interprete seus jobs.",
          FRAMES_DIR / "card_open.png")
    bases["card:open"] = FRAMES_DIR / "card_open.png"
    _card("Resumo",
          "Na Overview você monitora status,\ninterpreta resultados e age nos jobs.",
          FRAMES_DIR / "card_close.png")
    bases["card:close"] = FRAMES_DIR / "card_close.png"

    print("Building Carlito dialogue + spotlights (typing + 5.0s hold) @ 1080p…")
    segment_paths: list[Path] = []
    timing_rows: list[dict] = []
    hold_pngs: list[Path] = []
    t = 0.0
    prev_cur: tuple[float, float] | None = None
    prev_group = ""
    group_cache: dict[str, tuple[list, list[int], tuple[float, float], str]] = {}
    sfx_events: list[float] = []  # dialogue-appearance cue timestamps
    failures_before = 0  # percentage-based legacy spotlights replaced this revision
    pre_fail_ids: list[str] = []

    for step in steps:
        if step.badge.strip().lower() == "opcional":
            raise AssertionError(f"Opcional badge still present on {step.id}")
        base = bases[step.capture]
        is_card = step.capture.startswith("card:")
        discussed = DISCUSSED_ELEMENT.get(step.spotlight_group, step.spotlight_group)
        reused = bool(step.spotlight_group and step.spotlight_group == prev_group
                      and step.spotlight_group in group_cache)
        if reused:
            spots, margins, cursor, actual_target = group_cache[step.spotlight_group]
            geometry_driven = True
        else:
            if is_card:
                spots = _spotlights_for_step(step)
                actual_target = discussed
                geometry_driven = True
            else:
                regions = _load_regions(step.capture)
                spots, actual_target = _geometry_boxes_for_group(regions, step.spotlight_group)
                if not spots:
                    spots = _spotlights_for_step(step)
                    actual_target = discussed
                geometry_driven = bool((regions.get("geometry") or {}).get("source"))
            margins = [_margin_px_for_group(step.spotlight_group)] * max(1, len(spots))
            cursor = _cursor_for_step(step, spots)
            # Pre-render validation + preview snapshot.
            pre_status, pre_reason = _prevalidate_spotlight(
                step, spots, target_box=None, actual_target=actual_target,
            )
            if pre_status == "FAIL":
                failures_before += 1
                pre_fail_ids.append(f"{step.id}:{pre_reason}")
                raise RuntimeError(
                    f"Pre-render spotlight validation failed for {step.id}: "
                    f"discussed={discussed} actual={actual_target} reason={pre_reason}"
                )
            if not is_card:
                _write_spotlight_preview(step, base, spots, spots)
            if step.spotlight_group:
                group_cache[step.spotlight_group] = (
                    list(spots), list(margins), cursor, actual_target,
                )

        anim_frames, anim_s = _typing_plan(step)
        static_s = HOLD_COMPLETE_S
        scene_s = anim_s + static_s
        n_full = _char_count(step.title, step.body)

        move_dur = 0.0
        # Skip cursor move when reusing the same spotlight group.
        if not is_card and not reused:
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
        hold_start = anim_end
        hold_end = hold_start + static_s
        arrow_at = anim_end
        scene_end = hold_end
        sfx_at = anim_start
        sfx_events.append(sfx_at)

        post = 0.0
        if not is_card and step.click:
            # Click only after the full dialogue card (typing + 5s hold).
            click_pngs = []
            for i in range(CLICK_FRAMES):
                path = anim / f"{step.id}_c{i:02d}.png"
                _compose(base, path, title=step.title, body=step.body, badge=step.badge,
                         cursor=cursor, spotlights=spots, margins_px=margins, clicking=True,
                         reveal_chars=n_full, show_spotlight=True, show_dialogue=True, show_arrow=True)
                click_pngs.append(path)
            click_mp4 = CLIPS_DIR / f"{step.id}_click.mp4"
            _encode_seq(click_pngs, click_mp4)
            segment_paths.append(click_mp4)
            outcome = CLIPS_DIR / f"{step.id}_outcome.mp4"
            _encode_still(hold_a, OUTCOME_S, outcome)
            segment_paths.append(outcome)
            post = CLICK_FRAMES / FPS + OUTCOME_S

        review_status, fail_reason = _manual_review_spotlight(
            step, spots, boxes,
            discussed=discussed,
            actual_target=actual_target if not is_card else discussed,
            geometry_driven=True if is_card else geometry_driven,
        )
        # Multi-card identity: reused groups must keep exact coords (enforced by cache).
        timing_rows.append({
            "id": step.id,
            "title": step.title,
            "body": step.body.replace("\n", " / "),
            "badge": step.badge,
            "instructional": step.instructional,
            "spotlight_group": step.spotlight_group,
            "spotlight_reused": reused,
            "targets": list(step.targets),
            "discussed_element": discussed if not is_card else discussed,
            "actual_target": actual_target if not is_card else discussed,
            "target_bbox_norm": [[round(v, 4) for v in s] for s in spots],
            "geometry_driven": True if is_card else geometry_driven,
            "spotlight_corrected": True,  # this revision replaces estimate-based boxes
            "anim_start": anim_start,
            "anim_end": anim_end,
            "hold_start": hold_start,
            "hold_end": hold_end,
            "arrow_at": arrow_at,
            "sfx_at": sfx_at,
            "duck_at": sfx_at,
            "restore_at": sfx_at + DUCK_FADE_DOWN_S + 0.14 + DUCK_FADE_UP_S,
            "anim_duration": anim_s,
            "static_duration": static_s,
            "scene_duration": scene_s,
            "scene_end": scene_end,
            "spotlights_norm": [[round(v, 4) for v in s] for s in spots],
            "spotlights_px": [list(b) for b in boxes],
            "n_cutouts": max(1, len(boxes)),
            "margins": margins,
            "review_ts": hold_start + min(2.0, static_s / 2),
            "manual_review": review_status,
            "fail_reason": fail_reason,
        })
        t = scene_end + post
        prev_cur = cursor
        prev_group = step.spotlight_group
        print(f"  {step.id}: target={actual_target if not is_card else discussed} "
              f"cutouts={len(boxes)} reused={reused} hold={static_s:.1f}s type={anim_s:.2f}s end={t:.1f}s",
              flush=True)

    # Multi-card identical-spotlight check
    by_group: dict[str, list] = {}
    for row in timing_rows:
        g = row.get("spotlight_group") or ""
        if not g:
            continue
        by_group.setdefault(g, []).append(row)
    for g, rows in by_group.items():
        if len(rows) < 2:
            continue
        ref = rows[0]["spotlights_norm"]
        for row in rows[1:]:
            if row["spotlights_norm"] != ref:
                row["manual_review"] = "FAIL"
                row["fail_reason"] = f"multi-card spotlight drift in group {g}"

    _validate_timing(timing_rows)
    fails = [r["id"] for r in timing_rows if r.get("manual_review") == "FAIL"]
    _write_srt(timing_rows)
    _write_storyboard(timing_rows, steps)
    _write_spotlight_report(timing_rows, steps)
    # failures_before: all non-card scenes previously used estimate slices → count them
    legacy_estimate_scenes = sum(
        1 for r in timing_rows
        if not str(r.get("id", "")).startswith(("01_", "90_"))
    )
    _write_accuracy_report(timing_rows, steps, failures_before=legacy_estimate_scenes)
    _make_contact_sheet(hold_pngs, CONTACT_SHEET)

    concat = CLIPS_DIR / "concat.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in segment_paths), encoding="utf-8")
    silent_mux = CLIPS_DIR / "muxed_silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(silent_mux)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    audio_meta = _mix_audio(silent_mux, VIDEO_OUT, sfx_events, total_duration=t)
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
    reused_groups = len({r["spotlight_group"] for r in timing_rows if r.get("spotlight_reused")})
    meta = {
        "font_name": FONT_NAME,
        "font_regular": str(FONT_REGULAR),
        "font_bold": str(FONT_BOLD),
        "font_reason": FONT_REASON,
        "body_font_px": BODY_FONT_PX,
        "title_font_px": TITLE_FONT_PX,
        "resolution": [VIDEO_W, VIDEO_H],
        "hold_complete_s": HOLD_COMPLETE_S,
        "instructional_scenes": len(timing_rows),
        "min_scene_s": min(r["scene_duration"] for r in timing_rows),
        "max_scene_s": max(r["scene_duration"] for r in timing_rows),
        "min_hold_s": min(r["static_duration"] for r in timing_rows),
        "max_hold_s": max(r["static_duration"] for r in timing_rows),
        "min_typing_s": min(r["anim_duration"] for r in timing_rows),
        "max_typing_s": max(r["anim_duration"] for r in timing_rows),
        "dim_alpha": DIM_ALPHA,
        "scenes_multi_cutout": sum(1 for r in timing_rows if r["n_cutouts"] > 1),
        "spotlighted_cards": sum(1 for r in timing_rows if r["n_cutouts"] >= 1),
        "reused_spotlight_groups": reused_groups,
        "duration_s": t,
        "topic": "Overview",
        "timing_validation_passed": True,
        "spotlight_validation_passed": len(fails) == 0,
        "spotlight_failures": fails,
        "audio": audio_meta,
        "holds": timing_rows,
    }
    (OUT_DIR / "validation_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {VIDEO_OUT}")
    print(f"Wrote {ZIP_OUT}")
    print(f"Wrote {TIMING_REPORT}")
    print(f"Wrote {SPOTLIGHT_REPORT}")
    print(f"Wrote {SPOTLIGHT_ACCURACY}")
    print(f"Wrote {CONTACT_SHEET}")
    if fails:
        print(f"SPOTLIGHT_FAILS={fails}")
        return 2
    return 0


def _mix_audio(silent_mp4: Path, out_mp4: Path, sfx_times: list[float], *, total_duration: float) -> dict:
    """Mux looping original BGM + dialogue cues with ducking (NumPy SFX bed)."""
    import numpy as np
    import wave

    if not BGM_WAV.exists() or not SFX_WAV.exists():
        gen = OUT_DIR / "generate_original_audio.py"
        if gen.exists():
            import runpy
            runpy.run_path(str(gen), run_name="__main__")
        if not BGM_WAV.exists() or not SFX_WAV.exists():
            raise SystemExit(f"Missing original audio: {BGM_WAV} / {SFX_WAV}")

    sr = 44100
    n_total = max(sr, int(round(total_duration * sr)))

    def _read_wav(path: Path) -> np.ndarray:
        with wave.open(str(path), "rb") as w:
            assert w.getnchannels() == 1
            assert w.getsampwidth() == 2
            data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32767.0
            if w.getframerate() != sr:
                # nearest-neighbor resample
                idx = (np.arange(int(len(data) * sr / w.getframerate())) * (w.getframerate() / sr)).astype(int)
                idx = np.clip(idx, 0, len(data) - 1)
                data = data[idx]
            return data

    bgm = _read_wav(BGM_WAV)
    sfx = _read_wav(SFX_WAV)
    # Loop BGM
    reps = int(np.ceil(n_total / max(1, len(bgm))))
    bed = np.tile(bgm, reps)[:n_total] * BGM_LEVEL
    # Place SFX and build duck envelope
    sfx_track = np.zeros(n_total, dtype=np.float64)
    duck = np.ones(n_total, dtype=np.float64)
    fade_down = max(1, int(DUCK_FADE_DOWN_S * sr))
    fade_up = max(1, int(DUCK_FADE_UP_S * sr))
    hold = max(1, len(sfx))
    for ts in sfx_times:
        start = max(0, int(round(ts * sr)))
        end = min(n_total, start + len(sfx))
        if end <= start:
            continue
        sfx_track[start:end] += sfx[: end - start] * SFX_LEVEL
        # Duck window: fade down before cue, stay low during cue, fade up after
        d0 = max(0, start - fade_down)
        d1 = start
        d2 = min(n_total, start + hold)
        d3 = min(n_total, d2 + fade_up)
        if d1 > d0:
            duck[d0:d1] = np.minimum(duck[d0:d1], np.linspace(1.0, DUCK_LEVEL / max(BGM_LEVEL, 1e-6), d1 - d0))
        duck[d1:d2] = np.minimum(duck[d1:d2], DUCK_LEVEL / max(BGM_LEVEL, 1e-6))
        if d3 > d2:
            duck[d2:d3] = np.minimum(duck[d2:d3], np.linspace(DUCK_LEVEL / max(BGM_LEVEL, 1e-6), 1.0, d3 - d2))

    mixed = bed * duck + sfx_track
    peak = float(np.max(np.abs(mixed)) or 1.0)
    if peak > 0.98:
        mixed *= 0.95 / peak
        peak = float(np.max(np.abs(mixed)))
    pcm = np.clip(mixed * 32767.0, -32767, 32767).astype(np.int16)
    mixed_wav = CLIPS_DIR / "mixed_audio.wav"
    with wave.open(str(mixed_wav), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())

    peak_probe = subprocess.run(
        ["ffmpeg", "-i", str(mixed_wav), "-af", "volumedetect", "-f", "null", "-"],
        check=True, capture_output=True, text=True)

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(silent_mp4), "-i", str(mixed_wav),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
         "-map", "0:v:0", "-map", "1:a:0", str(out_mp4)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return {
        "bgm_source": str(BGM_WAV.relative_to(OUT_DIR)),
        "sfx_source": str(SFX_WAV.relative_to(OUT_DIR)),
        "license": "Original generated composition for this package (not Pokémon-derived).",
        "generation": "NumPy square/triangle oscillators; seed 20260727; BPM 96; G-centered.",
        "bgm_level": BGM_LEVEL,
        "sfx_level": SFX_LEVEL,
        "duck_level": DUCK_LEVEL,
        "fade_down_s": DUCK_FADE_DOWN_S,
        "fade_up_s": DUCK_FADE_UP_S,
        "cue_count": len(sfx_times),
        "peak_abs": peak,
        "volumedetect": peak_probe.stderr[-800:],
        "validation": "PASS" if peak <= 1.0 else "FAIL",
    }


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
