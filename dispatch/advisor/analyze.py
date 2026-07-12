"""Top-level Advisor analysis entry point."""

from __future__ import annotations

from dispatch import sql as sql_mod

from .adapter import adapt
from .models import AnalysisResult, Finding
from .rules import run_ddl_rules, run_form_rules, run_sql_rules


def analyze(
    sql_text: str,
    *,
    source_type: str,
    destination_type: str = "",
    destination_table: str = "",
    user_id: str = "",
) -> AnalysisResult:
    """Statically analyze Job SQL and form fields for catalog findings.

    ``ExistingTable`` Jobs are not analyzed. ``SqlTemplate`` is analyzed once
    on the template text. ``SqlFile`` is analyzed as it sits on disk (before
    ``table_wrapper``). Parse failure or unquoted template tokens yield
    analysis-unavailable with zero findings and no launch friction.
    """
    form_result = analyze_form(
        source_type=source_type,
        destination_type=destination_type,
        destination_table=destination_table,
        user_id=user_id,
    )
    sql_result = analyze_sql(
        sql_text,
        source_type=source_type,
        user_id=user_id,
    )
    return combine_analysis(sql_result, form_result)


def analyze_form(
    *,
    source_type: str,
    destination_type: str = "",
    destination_table: str = "",
    user_id: str = "",
) -> AnalysisResult:
    """Analyze form-only rules without parsing or reading SQL."""
    findings = run_form_rules(
        source_type=source_type,
        destination_type=destination_type,
        destination_table=destination_table,
        user_id=user_id,
    )
    return AnalysisResult(available=True, findings=tuple(findings))


def analyze_sql(
    sql_text: str,
    *,
    source_type: str,
    user_id: str = "",
) -> AnalysisResult:
    """Analyze SQL-only rules so callers may cache parsing independently."""
    if source_type == "ExistingTable":
        return AnalysisResult(available=True, findings=())

    adapted = adapt(sql_text)
    if not adapted.available:
        return AnalysisResult(available=False, findings=())

    findings: list[Finding] = run_sql_rules(adapted)

    self_contained = source_type == "SqlFile" and sql_mod.is_self_contained_ddl(sql_text)
    findings.extend(
        run_ddl_rules(
            adapted,
            user_id=user_id,
            self_contained_ddl=self_contained,
        )
    )
    return AnalysisResult(available=True, findings=tuple(findings))


def combine_analysis(
    sql_result: AnalysisResult,
    form_result: AnalysisResult,
) -> AnalysisResult:
    """Combine independently computed SQL and form findings."""
    return AnalysisResult(
        available=sql_result.available,
        findings=form_result.findings + sql_result.findings,
    )
