from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

from tools.prod_tui import controlled_job, levels, smoke_test
from tools.prod_tui.robocop_tmux import ProdTuiConfig


def test_smoke_json_report_includes_shared_contract_fields(tmp_path: Path) -> None:
    ctx = smoke_test.RunContext(
        config=ProdTuiConfig(host="user@hde2stl020003.mastercard.int", repo_path="/ads_storage/dispatch"),
        driver=SimpleNamespace(),
        run_timestamp="20260625_000000",
    )
    ctx.results.append(smoke_test.SmokeResult(name="compileall", passed=True, message="ok"))

    report_path = smoke_test.write_json_report(ctx, [1], time.monotonic(), tmp_path / "smoke.json")
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["operation"] == "smoke"
    assert payload["status"] == "passed"
    assert payload["node"] == "node03"
    assert payload["host"] == "user@hde2stl020003.mastercard.int"
    assert payload["repo_path"] == "/ads_storage/dispatch"
    assert "deployment_commit" in payload
    assert payload["install_decision"] == "not_applicable"
    assert payload["checks"][0]["name"] == "compileall"


def test_controlled_job_report_includes_shared_contract_fields(tmp_path: Path) -> None:
    config = ProdTuiConfig(host="user@hde2stl020004.mastercard.int", repo_path="/ads_storage/dispatch")
    run = controlled_job.ControlledRun(
        config=config,
        driver=SimpleNamespace(),
        table_name="dispatch_smoke_example",
    )
    run.steps.append(controlled_job.ControlledStep(name="launch", passed=True, message="ok"))

    report_path = controlled_job.write_json_report(run, [], time.monotonic(), tmp_path / "job.json")
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["operation"] == "smoke"
    assert payload["status"] == "passed"
    assert payload["node"] == "node04"
    assert payload["host"] == "user@hde2stl020004.mastercard.int"
    assert payload["repo_path"] == "/ads_storage/dispatch"
    assert "deployment_commit" in payload
    assert payload["install_decision"] == "not_applicable"
    assert payload["checks"][0]["name"] == "launch"


def test_levels_report_includes_shared_contract_fields(tmp_path: Path) -> None:
    config = ProdTuiConfig(host="user@hde2stl020003.mastercard.int", repo_path="/ads_storage/dispatch")
    run = controlled_job.ControlledRun(
        config=config,
        driver=SimpleNamespace(),
        table_name="dispatch_smoke_example",
    )
    run.steps.append(controlled_job.ControlledStep(name="level4", passed=False, message="drift"))

    report_path = levels.write_report(4, [run], time.monotonic(), tmp_path / "level.json")
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["operation"] == "smoke"
    assert payload["status"] == "failed"
    assert payload["node"] == "node03"
    assert payload["host"] == "user@hde2stl020003.mastercard.int"
    assert payload["repo_path"] == "/ads_storage/dispatch"
    assert "deployment_commit" in payload
    assert payload["install_decision"] == "not_applicable"
    assert payload["checks"][0]["name"] == "level4"
