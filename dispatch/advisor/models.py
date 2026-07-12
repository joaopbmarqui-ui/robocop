"""Finding and analysis-result shapes for the Query Optimization Advisor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rich.markup import escape

Severity = Literal["error", "warning", "info"]
BadgeSeverity = Literal["error", "warning", "info", "clean"]

SEVERITY_ORDER: tuple[Severity, ...] = ("error", "warning", "info")

SEVERITY_MARKUP = {
    "error": "[bold red]ERROR[/]",
    "warning": "[bold yellow]WARN[/]",
    "info": "[bold cyan]INFO[/]",
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
    location: str = ""

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
    worst = next(sev for sev in SEVERITY_ORDER if counts[sev])
    color = {"error": "red", "warning": "yellow", "info": "cyan"}[worst]
    suffix = " [dim]· SQL analysis unavailable[/]" if not result.available else ""
    return f"[{color}]Advisor: {worst}[/] [dim]({counts_label(result)})[/]{suffix}"


def counts_label(result: AnalysisResult) -> str:
    """Compact severity tally, e.g. ``2 err, 1 warn, 3 info``."""
    counts = result.severity_counts()
    nouns = {"error": "err", "warning": "warn", "info": "info"}
    return ", ".join(f"{count} {nouns[severity]}" for severity, count in counts.items() if count)


def finding_markup(finding: Finding) -> str:
    """Three-line finding block: identity, detection, remediation.

    Finding text is escaped because detections quote SQL fragments such as
    ``[BROADCAST]`` that Rich would otherwise swallow as markup tags.
    """
    meta = finding.ref
    if finding.location:
        meta += f" · {finding.location}"
    head = f"{SEVERITY_MARKUP[finding.severity]} [bold]{finding.rule_id}[/]  [dim]{escape(meta)}[/]"
    return f"{head}\n{escape(finding.detection)}\n[dim]→ {escape(finding.remediation)}[/]"
