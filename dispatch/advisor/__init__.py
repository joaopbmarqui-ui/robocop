"""Query Optimization Advisor — static Impala SQL analysis.

Flag-only: never mutates user SQL, never serializes the SQLGlot AST into
launchable or user-visible SQL. See docs/query-optimization-advisor-spec.md
and ADR-0006.
"""

from __future__ import annotations

from .analyze import analyze
from .models import AnalysisResult, Finding, badge_markup, finding_markup

__all__ = [
    "AnalysisResult",
    "Finding",
    "analyze",
    "badge_markup",
    "finding_markup",
]
