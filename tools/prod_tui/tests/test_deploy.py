from __future__ import annotations

import json
from pathlib import Path

from tools.prod_tui import deploy, reporting
from tools.prod_tui.robocop_tmux import ProdTuiConfig


def test_deploy_help_includes_commit_install_and_rollback_flags() -> None:
    help_text = deploy.build_parser().format_help()
    normalized = " ".join(help_text.split())

    assert "--commit COMMIT" in help_text
    assert "--install {auto,always,never}" in normalized
    assert "--reuse-session" in help_text
    assert "--rollback-from ROLLBACK_FROM" in help_text
    assert "--json-report JSON_REPORT" in help_text


def test_install_decision_auto_runs_for_runtime_changes() -> None:
    decision = deploy.decide_install_action(
        mode="auto",
        changed_paths=["dispatch/app.py", "requirements.txt"],
    )

    assert decision.action == "run"
    assert "requirements.txt" in decision.reason


def test_install_decision_auto_runs_for_shared_runtime_changes() -> None:
    decision = deploy.decide_install_action(
        mode="auto",
        changed_paths=["shared_runtime.py", "bin/dispatch"],
    )

    assert decision.action == "run"
    assert "shared_runtime.py" in decision.reason


def test_install_decision_auto_skips_for_docs_only_changes() -> None:
    decision = deploy.decide_install_action(
        mode="auto",
        changed_paths=["docs/release-workflow.md", "README.md"],
    )

    assert decision.action == "skip"
    assert "No install-sensitive files changed" in decision.reason


def test_shared_report_contract_contains_minimum_fields(tmp_path: Path) -> None:
    config = ProdTuiConfig(
        host="user@hde2stl020003.mastercard.int",
        repo_path="/ads_storage/dispatch",
    )
    report_path = tmp_path / "deploy-report.json"

    report = reporting.OperationReport(
        operation="deploy",
        status="passed",
        node="node03",
        host=config.host,
        repo_path=config.repo_path,
        deployment_commit="abc123",
        previous_remote_commit="def456",
        install_decision="run",
        checks=[
            reporting.ReportCheck(name="update", passed=True, message="update ok"),
        ],
    )
    reporting.write_report(report_path, report)

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["operation"] == "deploy"
    assert payload["status"] == "passed"
    assert payload["node"] == "node03"
    assert payload["host"] == "user@hde2stl020003.mastercard.int"
    assert payload["repo_path"] == "/ads_storage/dispatch"
    assert payload["deployment_commit"] == "abc123"
    assert payload["previous_remote_commit"] == "def456"
    assert payload["install_decision"] == "run"
    assert payload["checks"] == [{"name": "update", "passed": True, "message": "update ok"}]
