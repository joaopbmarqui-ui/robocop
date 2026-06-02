"""Controlled Level 3 production smoke job runner."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

try:  # pragma: no cover - exercised when run as a script
    from . import safety
    from .agent_loop import parse_screen
    from .robocop_tmux import DEFAULT_CONFIG_PATH, ProdTuiConfig, TmuxDriver, load_config
    from .smoke_test import RunContext, SmokeResult, selected_levels, checks_for_level, run_check, utc_stamp
except ImportError:  # pragma: no cover
    import safety
    from agent_loop import parse_screen
    from robocop_tmux import DEFAULT_CONFIG_PATH, ProdTuiConfig, TmuxDriver, load_config
    from smoke_test import RunContext, SmokeResult, selected_levels, checks_for_level, run_check, utc_stamp

HARNESS_DIR = Path(__file__).resolve().parent
REPORTS_DIR = HARNESS_DIR / "reports"
SCREENS_DIR = HARNESS_DIR / "screens"


@dataclass
class ControlledStep:
    name: str
    passed: bool
    message: str
    elapsed_ms: int = 0
    screen_capture: str = ""


@dataclass
class ControlledRun:
    config: ProdTuiConfig
    driver: TmuxDriver
    table_name: str
    sql_path: str = "/tmp/dispatch_smoke_test.sql"
    run_timestamp: str = field(default_factory=utc_stamp)
    save_screens: bool = True
    screens_dir: Path | None = None
    steps: list[ControlledStep] = field(default_factory=list)

    def capture(self, name: str) -> str:
        screen = self.driver.capture_screen()
        if self.save_screens:
            if self.screens_dir is None:
                self.screens_dir = SCREENS_DIR / f"controlled_{self.run_timestamp}"
            self.screens_dir.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")
            (self.screens_dir / f"{len(self.steps):02d}_{safe_name}.txt").write_text(
                screen + "\n",
                encoding="utf-8",
            )
        return screen

    def record(self, name: str, passed: bool, message: str, started: float, screen: str = "") -> ControlledStep:
        step = ControlledStep(
            name=name,
            passed=passed,
            message=message,
            elapsed_ms=int((time.monotonic() - started) * 1000),
            screen_capture=screen,
        )
        self.steps.append(step)
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}: {message}")
        if not passed and screen:
            print("--- last screen ---")
            print(screen)
            print("--- end screen ---")
        return step


def generate_smoke_table_name(config: ProdTuiConfig, now: datetime | None = None) -> str:
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d_%H%M%S")
    user = re.sub(r"[^A-Za-z0-9_]+", "_", config.current_user()).strip("_") or "dispatch"
    return f"{config.table_prefix.rstrip('_')}_{user}_{timestamp}"


def create_smoke_sql_file(run: ControlledRun) -> None:
    quoted_sql = shlex.quote(run.config.smoke_query_sql + "\n")
    run.driver._ssh(f"printf %s {quoted_sql} > {shlex.quote(run.sql_path)}")


def cleanup_smoke_files(run: ControlledRun) -> None:
    run.driver._ssh(f"rm -f {shlex.quote(run.sql_path)}", check=False)


def cleanup_smoke_table(run: ControlledRun) -> None:
    # Cleanup is intentionally explicit and limited to the generated smoke table.
    if not safety.is_safe_table_name(run.table_name, table_prefix=run.config.table_prefix):
        raise ValueError(f"Refusing to cleanup unsafe table name: {run.table_name}")
    sql = f"DROP TABLE IF EXISTS {run.config.scratch_schema}.{run.table_name};"
    run.driver._ssh(f"impala-shell -q {shlex.quote(sql)}", check=False)


def navigate_to_new_job(run: ControlledRun) -> str:
    run.driver.send_key("n")
    return run.driver.wait_for(r"New Job|Source.*Destination", timeout=15)


def clear_input(run: ControlledRun) -> None:
    for key in ("Home", "S-End", "Delete"):
        run.driver.send_key(key)
        time.sleep(0.1)


def type_into_field(run: ControlledRun, text: str) -> None:
    clear_input(run)
    run.driver.send_keys(text, literal=True)


def tab_to_field(run: ControlledRun, n: int) -> None:
    for _ in range(n):
        run.driver.send_key("Tab")
        time.sleep(0.1)


def select_radio(run: ControlledRun, option: str) -> None:
    # Textual radio sets are keyboard driven; callers place focus on the group.
    key = "Down" if option.lower() in {"table", "csv", "table + csv", "sqltemplate", "existingtable"} else "Up"
    run.driver.send_key(key)
    run.driver.send_key("Space")


def press_button(run: ControlledRun, label: str) -> None:
    shortcuts = {"preview": "p", "launch": "l", "back": "b"}
    run.driver.send_key(shortcuts.get(label.lower(), "Enter"))


def verify_field_value(run: ControlledRun, expected: str) -> bool:
    return expected in run.capture(f"verify_{expected[:20]}")


def fill_job_form(run: ControlledRun) -> str:
    # Field order follows the production New Job screen: source, destination,
    # SQL file, schema/table/email. Keystrokes are intentionally conservative.
    tab_to_field(run, 2)
    type_into_field(run, run.sql_path)
    tab_to_field(run, 1)
    type_into_field(run, run.config.scratch_schema)
    tab_to_field(run, 1)
    type_into_field(run, run.table_name)
    if run.config.operator_email:
        tab_to_field(run, 1)
        type_into_field(run, run.config.operator_email)
    screen = run.capture("filled_form")
    expected = [run.sql_path, run.config.scratch_schema, run.table_name]
    missing = [value for value in expected if value not in screen]
    if missing:
        raise RuntimeError(f"Filled form did not show expected values: {missing}")
    return screen


def preview_and_verify(run: ControlledRun) -> str:
    press_button(run, "preview")
    screen = run.driver.wait_for(r"Preview|SQL Preview", timeout=15)
    if run.config.smoke_query_sql not in screen or run.table_name not in screen:
        raise RuntimeError("Preview did not contain the smoke SQL and table name")
    run.driver.send_key("b")
    run.driver.wait_for(r"New Job|Source.*Destination", timeout=10)
    return screen


def launch_and_confirm(run: ControlledRun) -> str:
    press_button(run, "launch")
    screen = run.driver.wait_for(r"confirm|Launch|Are you sure", timeout=15)
    run.driver.send_key("y")
    return run.driver.wait_for(r"Launched Job|Active Jobs|Running", timeout=20)


def wait_for_job_completion(run: ControlledRun) -> str:
    deadline = time.monotonic() + run.config.max_smoke_job_wait_seconds
    last_screen = ""
    while time.monotonic() < deadline:
        last_screen = run.capture("job_poll")
        if run.table_name in last_screen and re.search(r"Succeeded|Failed|Cancelled", last_screen):
            if "Succeeded" in last_screen:
                return "Succeeded"
            if "Failed" in last_screen:
                return "Failed"
            return "Cancelled"
        time.sleep(5)
    raise TimeoutError(f"Timed out waiting for smoke job completion. Last screen:\n{last_screen}")


def verify_table_exists(run: ControlledRun) -> str:
    sql = f"SHOW TABLES IN {run.config.scratch_schema} LIKE '{run.table_name}';"
    result = run.driver._ssh(f"impala-shell -q {shlex.quote(sql)}")
    stdout = getattr(result, "stdout", "")
    if run.table_name not in stdout:
        raise RuntimeError(f"Smoke table was not found in Impala output: {stdout}")
    return stdout


def parse_klist_ttl_seconds(screen: str) -> int | None:
    match = re.search(r"KRB_TTL=(\d+)", screen)
    return int(match.group(1)) if match else None


def collect_preconditions(run: ControlledRun) -> list[str]:
    ttl_command = (
        "python -c \"import subprocess; "
        "from dispatch.kerberos import parse_ttl_seconds; "
        "p=subprocess.run(['klist'], capture_output=True, text=True); "
        "ttl=parse_ttl_seconds(p.stdout) if p.returncode==0 else None; "
        "print('KRB_TTL=' + (str(ttl) if ttl is not None else 'MISSING'))\""
    )
    run.driver.send_keys(ttl_command)
    try:
        screen = run.driver.wait_for(r"KRB_TTL=(\d+|MISSING)", timeout=10)
    except TimeoutError:
        screen = run.capture("preconditions")
    ttl = parse_klist_ttl_seconds(screen)
    run.driver.send_keys("cd /tmp && dispatch")
    dashboard = run.driver.wait_for("Active Jobs", timeout=20)
    state = parse_screen(dashboard)
    running_jobs = state.running_jobs
    violations = []
    if run.config.scratch_schema != "dw_settle":
        violations.append("Configured scratch_schema must be the approved scratch schema dw_settle")
    violations.extend(
        safety.check_launch_preconditions(
            ttl,
            running_jobs,
            run.table_name,
            run.config.smoke_query_sql,
            table_prefix=run.config.table_prefix,
            smoke_query_sql=run.config.smoke_query_sql,
        )
    )
    return violations


def run_level_1_and_2(config: ProdTuiConfig, driver: TmuxDriver, run_timestamp: str, fail_fast: bool, passcode: str | None = None) -> list[SmokeResult]:
    ctx = RunContext(
        config=config,
        driver=driver,
        run_timestamp=run_timestamp,
        save_screens=True,
        screens_dir=SCREENS_DIR / f"controlled_prereq_{run_timestamp}",
    )
    ctx.passcode = passcode
    for level in selected_levels("all"):
        for check in checks_for_level(level):
            result = run_check(ctx, level, check)
            if fail_fast and not result.passed:
                return ctx.results
    return ctx.results


def write_json_report(run: ControlledRun, prereq_results: list[SmokeResult], started: float, path: str | None = None) -> Path:
    report_path = Path(path) if path else REPORTS_DIR / f"controlled_{run.run_timestamp}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "host": run.config.host,
        "levels_run": [1, 2, 3],
        "duration_seconds": round(time.monotonic() - started, 3),
        "table_name": run.table_name,
        "dry_run_supported": True,
        "results": [asdict(result) for result in prereq_results] + [asdict(step) for step in run.steps],
        "summary": {
            "total": len(prereq_results) + len(run.steps),
            "passed": sum(1 for result in prereq_results if result.passed) + sum(1 for step in run.steps if step.passed),
            "failed": sum(1 for result in prereq_results if not result.passed) + sum(1 for step in run.steps if not step.passed),
        },
        "screen_captures": str(run.screens_dir) if run.screens_dir else None,
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report_path


def controlled_lifecycle(run: ControlledRun, *, dry_run: bool) -> None:
    started = time.monotonic()
    run.driver.start_session(passcode=getattr(run, "passcode", None))
    run.record("start_session", True, "Remote tmux session started", started, run.capture("start_session"))

    started = time.monotonic()
    create_smoke_sql_file(run)
    run.record("create_smoke_sql_file", True, f"Wrote {run.sql_path}", started)

    started = time.monotonic()
    violations = collect_preconditions(run)
    if violations:
        run.record("preconditions", False, "; ".join(violations), started, run.capture("preconditions_failed"))
        raise RuntimeError("Launch preconditions failed")
    run.record("preconditions", True, "Launch preconditions satisfied", started, run.capture("preconditions"))

    started = time.monotonic()
    screen = navigate_to_new_job(run)
    run.record("navigate_to_new_job", True, "New Job screen opened", started, screen)

    started = time.monotonic()
    screen = fill_job_form(run)
    run.record("fill_job_form", True, "Smoke form values are visible", started, screen)

    started = time.monotonic()
    screen = preview_and_verify(run)
    run.record("preview_and_verify", True, "Preview contains smoke SQL and table", started, screen)

    if dry_run:
        started = time.monotonic()
        run.driver.send_key("q")
        run.record("dry_run_exit", True, "Stopped before Launch as requested", started, run.capture("dry_run_exit"))
        return

    started = time.monotonic()
    screen = launch_and_confirm(run)
    run.record("launch_and_confirm", True, "Launch confirmed", started, screen)

    started = time.monotonic()
    state = wait_for_job_completion(run)
    if state != "Succeeded":
        run.record("wait_for_job_completion", False, f"Job ended as {state}", started, run.capture("job_failed"))
        raise RuntimeError(f"Smoke job ended as {state}")
    run.record("wait_for_job_completion", True, "Smoke job succeeded", started, run.capture("job_succeeded"))

    started = time.monotonic()
    output = verify_table_exists(run)
    run.record("verify_table_exists", True, "Smoke table exists in Impala", started, output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a controlled production Dispatch smoke job")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--dry-run", action="store_true", help="Fill and preview the form, then exit before Launch")
    parser.add_argument("--json-report", help="Write JSON report to this path")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--skip-level12", action="store_true", help="Skip Level 1/2 prerequisite smoke checks")
    parser.add_argument("--passcode", help="Passcode for SSH authentication")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    started = time.monotonic()
    prereq_results: list[SmokeResult] = []
    config = load_config(args.config)
    driver = TmuxDriver.from_config(config, retries=2)
    run = ControlledRun(config=config, driver=driver, table_name=generate_smoke_table_name(config))
    run.passcode = args.passcode
    exit_code = 0
    try:
        if not args.skip_level12:
            prereq_results = run_level_1_and_2(config, driver, run.run_timestamp, args.fail_fast, passcode=args.passcode)
            if any(not result.passed for result in prereq_results):
                exit_code = 1
                raise RuntimeError("Level 1/2 prerequisite checks failed")
        controlled_lifecycle(run, dry_run=args.dry_run)
    except Exception as exc:  # noqa: BLE001
        exit_code = exit_code or 1
        print(f"Controlled run failed: {type(exc).__name__}: {exc}", file=sys.stderr)
    finally:
        cleanup_started = time.monotonic()
        try:
            cleanup_smoke_files(run)
            if not args.dry_run:
                cleanup_smoke_table(run)
            run.record("cleanup", True, "Cleanup attempted for smoke files/table", cleanup_started)
        except Exception as exc:  # noqa: BLE001
            exit_code = 2
            run.record("cleanup", False, f"Cleanup failed: {exc}", cleanup_started)
        try:
            driver.stop_session()
        except Exception:
            pass
        report_path = write_json_report(run, prereq_results, started, args.json_report)
        print(f"JSON report: {report_path}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
