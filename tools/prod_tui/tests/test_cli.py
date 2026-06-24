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
    tracker = Path("docs/dispatch_user_story_tracker.csv").read_text(encoding="utf-8")

    assert "**Dashboard renders:** status strip shows Running/Finished/Failed/Kerberos summary" in smoke
    assert "stat cards (Running/Finished/Failed/Kerberos)" not in smoke
    assert "No jobs in the last 7 days" in smoke
    assert "press N to launch one" in smoke
    assert "No active Jobs" not in smoke
    assert "**Event trail:** dashboard bottom shows startup event with timestamp" in smoke
    assert "**dispatch.log exists:** `cat ~/.dispatch/dispatch.log` shows startup entry" in smoke
    assert "APP-004,App shell" in tracker
    assert "DASH-006,Dashboard" in tracker


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

    assert "`tools.prod_tui tmux send` or `tools.prod_tui tmux keys`" in workflow
    assert "robocop_tmux.py send" not in workflow


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


def test_implementation_plans_are_marked_historical_not_canonical() -> None:
    offenders: list[str] = []

    for plan in [
        *Path("docs").glob("implementation-plan*.md"),
        *Path("docs/archive").rglob("implementation-plan*.md"),
    ]:
        text = plan.read_text(encoding="utf-8")
        header = "\n".join(text.splitlines()[:12])
        if "Historical" not in header:
            offenders.append(f"{plan}: missing Historical marker")
        if "docs/dispatch_user_story_tracker.csv" not in header:
            offenders.append(f"{plan}: missing canonical tracker pointer")
        if "docs/dispatch_user_story_completion_audit.md" not in header:
            offenders.append(f"{plan}: missing completion audit pointer")
        if re.search(r"\*\*Status:\*\*\s*Active", header):
            offenders.append(f"{plan}: still marked Active")

    assert offenders == []


def test_docs_root_keeps_superseded_plans_archived() -> None:
    stale_root_names = {
        "goal-phase-1-safety.md",
        "goal-phase-2-correctness.md",
        "goal-phase-3-resilience-observability.md",
        "goal-phase-4-polish-feedback.md",
        "goal-phase-5-test-hardening.md",
        "goal-ui-ux-closure-loop.md",
        "handoff-ui-ux-closure-2026-05-17.md",
        "implementation-plan-production-testing.md",
        "implementation-plan-sidebar-navigation-2026-05-20.md",
        "implementation-plan-v2.md",
        "plan.md",
        "prototype-to-production-plan.md",
        "task-list-sidebar-navigation-2026-05-20.md",
        "ui-ux-report-2026-05-10.md",
        "ui-ux-report-2026-05-19.md",
        "ui-ux-screenshot-review-2026-05-16.md",
        "ui-visual-exploration-plan-2026-05-19.md",
    }
    root_docs = {path.name for path in Path("docs").glob("*.md")}
    archive_docs = {path.name for path in Path("docs/archive").rglob("*.md")}

    assert root_docs.isdisjoint(stale_root_names)
    assert stale_root_names <= archive_docs
