"""Query Optimization Advisor — static Impala SQL analysis.

Flag-only: never mutates user SQL, never serializes the SQLGlot AST into
launchable or user-visible SQL. See docs/query-optimization-advisor-spec.md
and ADR-0006.
"""

from __future__ import annotations

from .analyze import analyze, analyze_form, analyze_sql, combine_analysis
from .models import AnalysisResult, Finding, badge_markup, counts_label, finding_markup

__all__ = [
    "AnalysisResult",
    "Finding",
    "analyze",
    "analyze_form",
    "analyze_sql",
    "badge_markup",
    "combine_analysis",
    "counts_label",
    "finding_markup",
]
