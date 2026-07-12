"""Finding and analysis-result shapes for the Query Optimization Advisor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["error", "warning", "info"]
BadgeSeverity = Literal["error", "warning", "info", "clean"]

SEVERITY_ORDER: tuple[Severity, ...] = ("error", "warning", "info")

SEVERITY_MARKUP = {
    "error": "[bold red]error[/]",
    "warning": "[yellow]warning[/]",
    "info": "[cyan]info[/]",
}


@dataclass(frozen=True)
class Finding:
    """One Advisor detection in the locked two-part shape."""

    rule_id: str
    rule_name: str
    guideline: str
    severity: Severity
    detection: str
    remediation: str

    @property
    def ref(self) -> str:
        return self.guideline


@dataclass(frozen=True)
class AnalysisResult:
    """Outcome of a static analysis pass.

    ``available`` is False when the adapter cannot produce a trustworthy AST
    (parse failure, unquoted template token, unmaskable hint). Unavailable
    analysis yields zero findings and never gates launch.
    """

    available: bool
    findings: tuple[Finding, ...]

    @property
    def badge(self) -> BadgeSeverity:
        # Form-field findings (R16) survive SQL-analysis unavailability, so
        # the badge reflects findings whenever any exist.
        if not self.findings:
            return "clean"
        counts = self.severity_counts()
        for severity in SEVERITY_ORDER:
            if counts[severity]:
                return severity
        return "clean"

    def severity_counts(self) -> dict[Severity, int]:
        return {
            severity: sum(1 for f in self.findings if f.severity == severity)
            for severity in SEVERITY_ORDER
        }

    def errors(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity == "error")


def badge_markup(result: AnalysisResult) -> str:
    """Worst-severity badge with counts; label-first so color is never the only cue."""
    if not result.findings:
        if not result.available:
            return "[dim]Advisor: unavailable[/]"
        return "[green]Advisor: clean[/]"
    counts = result.severity_counts()
    parts = " · ".join(_count_label(severity, count) for severity, count in counts.items() if count)
    worst = next(sev for sev in SEVERITY_ORDER if counts[sev])
    color = {"error": "red", "warning": "yellow", "info": "cyan"}[worst]
    suffix = " [dim]· SQL analysis unavailable[/]" if not result.available else ""
    return f"[{color}]Advisor: {worst}[/] [dim]({parts})[/]{suffix}"


def _count_label(severity: Severity, count: int) -> str:
    if severity == "info":
        noun = "info" if count == 1 else "infos"
    else:
        noun = severity if count == 1 else f"{severity}s"
    return f"{count} {noun}"


def finding_markup(finding: Finding) -> str:
    """Two-part finding line for Preview and the launch-gate modal."""
    head = (
        f"{SEVERITY_MARKUP[finding.severity]} [bold]{finding.rule_id}[/]"
        f" [dim]· {finding.ref}[/]  {finding.detection}"
    )
    return f"{head}\n      [dim]-> {finding.remediation}[/]"
