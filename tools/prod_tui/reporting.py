"""Shared reporting helpers for production Dispatch harness commands."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def node_name_from_host(host: str) -> str:
    hostname = host.rsplit("@", 1)[-1]
    if hostname.endswith("0004.mastercard.int"):
        return "node04"
    if hostname.endswith("0003.mastercard.int"):
        return "node03"
    return hostname.split(".", 1)[0]


@dataclass(frozen=True)
class ReportCheck:
    name: str
    passed: bool
    message: str
    evidence: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
        }
        if self.evidence:
            payload["evidence"] = self.evidence
        return payload


@dataclass
class OperationReport:
    operation: str
    status: str
    node: str
    host: str
    repo_path: str
    deployment_commit: str
    timestamp: str = field(default_factory=utc_iso_timestamp)
    reviewed_commit: str | None = None
    previous_remote_commit: str | None = None
    install_decision: str = "not_applicable"
    checks: list[ReportCheck] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "timestamp": self.timestamp,
            "node": self.node,
            "host": self.host,
            "repo_path": self.repo_path,
            "operation": self.operation,
            "deployment_commit": self.deployment_commit,
            "install_decision": self.install_decision,
            "status": self.status,
            "checks": [check.to_payload() for check in self.checks],
        }
        if self.reviewed_commit is not None:
            payload["reviewed_commit"] = self.reviewed_commit
        if self.previous_remote_commit is not None:
            payload["previous_remote_commit"] = self.previous_remote_commit
        payload.update(self.extra)
        return payload


def write_report(path: str | Path, report: OperationReport) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report.to_payload(), indent=2) + "\n", encoding="utf-8")
    return report_path
