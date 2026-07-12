"""Severity-striped Advisor finding blocks shared by Preview and the launch gate."""

from __future__ import annotations

from textual.widgets import Static

from dispatch.advisor.models import Finding, finding_markup


class FindingBlock(Static):
    """One Advisor finding rendered as a bordered block with a severity strip."""

    def __init__(self, finding: Finding) -> None:
        super().__init__(
            finding_markup(finding),
            classes=f"finding-block severity-{finding.severity}",
        )
