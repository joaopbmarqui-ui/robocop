from __future__ import annotations

import re
import sys
from pathlib import Path

from tools.prod_tui import __main__ as prod_tui_cli


def test_top_level_help_prints_usage_and_succeeds(capsys, monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["python -m tools.prod_tui", "--help"])

    assert prod_tui_cli.main() == 0

    out = capsys.readouterr().out
    assert "Usage: python -m tools.prod_tui <command> [args...]" in out
    assert "preflight" in out
    assert "tmux" in out
    assert "smoke" in out
    assert "job" in out
    assert "level" in out
    assert "deploy" in out
    assert "drift" in out


def test_top_level_preflight_command_dispatches(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_preflight_main(argv: list[str]) -> int:
        calls.append(argv)
        return 2

    import tools.prod_tui.preflight as preflight

    monkeypatch.setattr(preflight, "main", fake_preflight_main)
    monkeypatch.setattr(
        sys,
        "argv",
        ["python -m tools.prod_tui", "preflight", "--config", "config.yaml", "--timeout", "5"],
    )

    assert prod_tui_cli.main() == 2
    assert calls == [["--config", "config.yaml", "--timeout", "5"]]


def test_top_level_deploy_command_dispatches(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_deploy_main(argv: list[str]) -> int:
        calls.append(argv)
        return 3

    import tools.prod_tui.deploy as deploy

    monkeypatch.setattr(deploy, "main", fake_deploy_main)
    monkeypatch.setattr(
        sys,
        "argv",
        ["python -m tools.prod_tui", "deploy", "--config", "config.yaml", "--commit", "abc123"],
    )

    assert prod_tui_cli.main() == 3
    assert calls == [["--config", "config.yaml", "--commit", "abc123"]]


def test_top_level_drift_command_dispatches(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_drift_main(argv: list[str]) -> int:
        calls.append(argv)
        return 4

    import tools.prod_tui.drift as drift

    monkeypatch.setattr(drift, "main", fake_drift_main)
    monkeypatch.setattr(
        sys,
        "argv",
        ["python -m tools.prod_tui", "drift", "--config", "config.yaml", "--commit", "abc123"],
    )

    assert prod_tui_cli.main() == 4
    assert calls == [["--config", "config.yaml", "--commit", "abc123"]]


def test_readme_matches_current_tmux_cli_and_auth_model() -> None:
    readme = Path("tools/prod_tui/README.md").read_text(encoding="utf-8")

    assert "already-authenticated tmux pane" in readme
    assert "separate SSH connection" not in readme
    assert "python3.11 or python3.10" in readme
    assert "- `python3.10`, `klist`, and `impala-shell` are available." not in readme
    assert 'ssh_options: "-p 2222 -o StrictHostKeyChecking=no"' in readme
    assert "python -m tools.prod_tui tmux start --config tools/prod_tui/config.yaml" in readme
    assert "python -m tools.prod_tui preflight --config tools/prod_tui/config.yaml" in readme
    assert "--json-report tools/prod_tui/reports/preflight-node03.json" in readme


def test_production_docs_map_csv_contract_to_level4() -> None:
    smoke = Path("docs/edge-node-smoke-test.md").read_text(encoding="utf-8")
    production = Path("docs/production_testing.md").read_text(encoding="utf-8")

    assert "Level 3a" in smoke
    assert "py -m tools.prod_tui level --config tools/prod_tui/config.yaml --level 4" in smoke
    assert "Table+Csv" in smoke
    assert "Level 4 - job-type breadth" in production
    assert "SqlFile -> Csv" in production
    assert "SqlFile -> Table+Csv" in production


def test_production_docs_include_tcp_preflight_and_single_ssh_model() -> None:
    smoke = Path("docs/edge-node-smoke-test.md").read_text(encoding="utf-8")
    production = Path("docs/production_testing.md").read_text(encoding="utf-8")
    readme = Path("tools/prod_tui/README.md").read_text(encoding="utf-8")

    assert "Test-NetConnection" in smoke
    assert "python -m tools.prod_tui preflight --config tools/prod_tui/config.yaml" in smoke
    assert "python -m tools.prod_tui preflight --config tools/prod_tui/config-node04.yaml" in smoke
    assert "--json-report tools/prod_tui/reports/preflight-node03.json" in smoke
    assert "--json-report tools/prod_tui/reports/preflight-node04.json" in smoke
    assert "Stop here if the preflight report has `connected: false`" in smoke
    assert "TcpTestSucceeded" in smoke
    assert "Test-NetConnection" in production
    assert "python -m tools.prod_tui preflight --config tools/prod_tui/config.yaml" in production
    assert "--json-report tools/prod_tui/reports/preflight-node03.json" in production
    assert "py -m tools.prod_tui tmux start --config tools/prod_tui/config.yaml" in production
    assert "py -m tools.prod_tui smoke --config tools/prod_tui/config.yaml" in production
    assert "tools/prod_tui/config-node04.yaml` consistently" in production
    assert "Do not run `tmux start`, `smoke`, `job`, or `level`" in production
    assert "already-authenticated tmux pane" in production
    assert "separate direct `ssh`" not in production
    assert "TCP 2222" in readme
    assert "python -m tools.prod_tui preflight --config tools/prod_tui/config.yaml" in readme
    assert "preflight JSON report shows `connected: true`" in readme


def test_edge_smoke_checklist_matches_dashboard_empty_state_and_diagnostics() -> None:
    smoke = Path("docs/edge-node-smoke-test.md").read_text(encoding="utf-8")

    assert "**Dashboard renders:** status strip shows Running/Finished/Failed/Kerberos summary" in smoke
    assert "stat cards (Running/Finished/Failed/Kerberos)" not in smoke
    assert "No jobs in the last 7 days" in smoke
    assert "press N to launch one" in smoke
    assert "No active Jobs" not in smoke
    assert "**Event trail:** dashboard bottom shows startup event with timestamp" in smoke
    assert "**dispatch.log exists:** `cat ~/.dispatch/dispatch.log` shows startup entry" in smoke


def test_operator_docs_keep_harness_commands_config_explicit() -> None:
    docs = [
        Path("docs/edge-node-smoke-test.md"),
        Path("docs/production_testing.md"),
        Path("tools/prod_tui/README.md"),
    ]
    command_pattern = re.compile(r"\b(?:py|python) -m tools\.prod_tui (?:tmux|smoke|job|level)\b")
    offenders: list[str] = []

    for doc in docs:
        for line_number, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), start=1):
            if command_pattern.search(line) and "--config" not in line:
                offenders.append(f"{doc}:{line_number}:{line}")

    assert offenders == []


def test_development_workflow_uses_current_tmux_module_cli() -> None:
    workflow = Path("docs/development-workflow.md").read_text(encoding="utf-8")

    assert "py -m edge_deploy release --tool robocop --smoke standard" in workflow
    assert "Manual tmux attachment and node-side commands are not part of the default path." in workflow
    assert "robocop_tmux.py send" not in workflow


def test_active_operator_docs_cover_publish_deploy_drift_and_exact_sha_rollback() -> None:
    workflow = Path("docs/development-workflow.md").read_text(encoding="utf-8")
    production = Path("docs/production_testing.md").read_text(encoding="utf-8")
    setup = Path("docs/edge-node-first-time-setup.md").read_text(encoding="utf-8")
    readme = Path("tools/prod_tui/README.md").read_text(encoding="utf-8")

    assert "py -m edge_deploy release --tool robocop --smoke standard" in workflow
    assert ".\\tools\\dev\\publish_dispatch_snapshot.ps1 -ReviewedCommit <sha> -RunLocalCheck" in workflow
    assert "py -m tools.prod_tui deploy --config tools/prod_tui/config.yaml --commit <deployment-sha> --install auto" in workflow
    assert "py -m tools.prod_tui drift --config tools/prod_tui/config.yaml --commit <deployment-sha>" in workflow
    assert "repo-local commands such as these are valid only in that recovery/bootstrap" in workflow.lower()
    assert "failed preflight is the validation artifact" in production
    assert "config-node04.yaml" in production
    assert "py -m tools.prod_tui deploy --config tools/prod_tui/config.yaml --commit <deployment-sha>" in production
    assert "py -m tools.prod_tui drift --config tools/prod_tui/config.yaml --commit <deployment-sha>" in production
    assert "exact-SHA" in setup
    assert "py -m tools.prod_tui deploy --config tools/prod_tui/config.yaml --commit <previous-good-sha> --rollback-from <current-bad-sha>" in readme
    assert "Generated Artifacts" in readme


def test_active_harness_surfaces_do_not_reference_old_tmux_script_cli() -> None:
    active_artifacts = [
        Path("docs/development-workflow.md"),
        Path("docs/edge-node-smoke-test.md"),
        Path("docs/production_testing.md"),
        Path("tools/prod_tui/README.md"),
        *Path("tools/prod_tui").glob("*.py"),
    ]
    stale_patterns = [
        "py tools/prod_tui/robocop_tmux.py",
        "python tools/prod_tui/robocop_tmux.py",
        "robocop_tmux.py start",
        "robocop_tmux.py send",
    ]
    offenders: list[str] = []

    for artifact in active_artifacts:
        text = artifact.read_text(encoding="utf-8")
        for pattern in stale_patterns:
            if pattern in text:
                offenders.append(f"{artifact}:{pattern}")

    assert offenders == []
