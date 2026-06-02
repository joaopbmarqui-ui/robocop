"""Level 1 and 2 production smoke runner for the Dispatch TUI harness."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence

try:  # pragma: no cover - exercised when run as a script
    from .robocop_tmux import DEFAULT_CONFIG_PATH, ProdTuiConfig, TmuxDriver, load_config
except ImportError:  # pragma: no cover
    from robocop_tmux import DEFAULT_CONFIG_PATH, ProdTuiConfig, TmuxDriver, load_config

HARNESS_DIR = Path(__file__).resolve().parent
REPORTS_DIR = HARNESS_DIR / "reports"
SCREENS_DIR = HARNESS_DIR / "screens"


@dataclass
class SmokeResult:
    name: str
    passed: bool
    message: str
    screen_capture: str = ""
    level: int = 0
    elapsed_ms: int = 0


@dataclass
class RunContext:
    config: ProdTuiConfig
    driver: TmuxDriver
    run_timestamp: str
    save_screens: bool = False
    verbose: bool = False
    screens_dir: Path | None = None
    results: list[SmokeResult] = field(default_factory=list)

    def capture(self, name: str, history_lines: int = 200) -> str:
        screen = self.driver.capture_screen(history_lines=history_lines)
        if self.save_screens:
            if self.screens_dir is None:
                self.screens_dir = SCREENS_DIR / f"run_{self.run_timestamp}"
            self.screens_dir.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")
            (self.screens_dir / f"{len(self.results):02d}_{safe_name}.txt").write_text(
                screen + "\n",
                encoding="utf-8",
            )
        return screen


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _ok(name: str, message: str, screen: str = "") -> SmokeResult:
    return SmokeResult(name=name, passed=True, message=message, screen_capture=screen)


def _fail(name: str, message: str, screen: str = "") -> SmokeResult:
    return SmokeResult(name=name, passed=False, message=message, screen_capture=screen)


def _run_shell_and_wait(ctx: RunContext, command: str, pattern: str, timeout: float = 20.0) -> str:
    ctx.driver.send_keys(command)
    return ctx.driver.wait_for(pattern, timeout=timeout, poll_interval=1.0)


def _ensure_prompt(ctx: RunContext) -> None:
    for key in ("Escape", "q"):
        ctx.driver.send_key(key)
        time.sleep(0.2)
    ctx.driver.send_keys(f"cd {ctx.config.repo_path}")
    time.sleep(0.5)


def check_ssh_connectivity(ctx: RunContext) -> SmokeResult:
    ctx.driver.start_session(passcode=getattr(ctx, "passcode", None))
    screen = ctx.capture("ssh_connectivity")
    return _ok("ssh_connectivity", "Remote tmux session started", screen)


def check_tmux_geometry(ctx: RunContext) -> SmokeResult:
    result = ctx.driver._tmux([
        "display-message",
        "-p",
        "-t",
        ctx.config.session_name,
        "#{window_width} #{window_height}"
    ])
    assert isinstance(result, subprocess.CompletedProcess)
    output = result.stdout.strip()
    expected = f"{ctx.config.terminal_width} {ctx.config.terminal_height}"
    screen = ctx.capture("tmux_geometry")
    if output != expected:
        return _fail("tmux_geometry", f"Expected {expected}, got {output!r}", screen)
    return _ok("tmux_geometry", f"tmux geometry is {output}", screen)


def check_compileall(ctx: RunContext) -> SmokeResult:
    py = "$(command -v python3.11 || command -v python3.10 || echo /sys_apps_01/python/python310/bin/python3.10)"
    screen = _run_shell_and_wait(
        ctx,
        f"{py} -m compileall dispatch scr && echo COMPILEALL_\"\"OK",
        "COMPILEALL_OK",
        timeout=60,
    )
    return _ok("compileall", "compileall dispatch scr passed", screen)


def check_dispatch_opens(ctx: RunContext) -> SmokeResult:
    _ensure_prompt(ctx)
    ctx.driver.send_keys("dispatch")
    screen = ctx.driver.wait_for(r"RUNNING|KERBEROS|Active Jobs", timeout=20, poll_interval=1.0)
    return _ok("dispatch_opens", "Dispatch dashboard became visible", screen)


def check_dashboard_renders(ctx: RunContext) -> SmokeResult:
    screen = ctx.capture("dashboard_renders")
    required = ["Active Jobs", "RUNNING"]
    missing = [text for text in required if text not in screen]
    if missing:
        return _fail("dashboard_renders", f"Missing dashboard text: {', '.join(missing)}", screen)
    return _ok("dashboard_renders", "Dashboard contains active job/stat card text", screen)


def check_kerberos_status(ctx: RunContext) -> SmokeResult:
    screen = ctx.capture("kerberos_status")
    if re.search(r"KERBEROS[\s\S]{1,100}?(N/A|MISSING|\d|[0-9]+[hm])", screen, flags=re.IGNORECASE):
        return _ok("kerberos_status", "Kerberos status is visible", screen)
    return _fail("kerberos_status", "Kerberos status was not visible", screen)


def _press_and_wait(ctx: RunContext, name: str, key: str, pattern: str, timeout: float = 10.0) -> SmokeResult:
    ctx.driver.send_key(key)
    screen = ctx.driver.wait_for(pattern, timeout=timeout, poll_interval=0.5)
    return _ok(name, f"Pressed {key} and observed {pattern}", screen)


def check_new_job_navigation(ctx: RunContext) -> SmokeResult:
    return _press_and_wait(ctx, "navigation_new_job", "n", r"New Job|Source.*Destination")


def check_back_to_dashboard_from_new_job(ctx: RunContext) -> SmokeResult:
    ctx.driver.send_key("Escape")
    try:
        screen = ctx.driver.wait_for("Active Jobs", timeout=5)
    except TimeoutError:
        ctx.driver.send_key("b")
        screen = ctx.driver.wait_for("Active Jobs", timeout=5)
    return _ok("navigation_back_dashboard", "Returned to dashboard from New Job", screen)


def check_browser_opens(ctx: RunContext) -> SmokeResult:
    return _press_and_wait(ctx, "browser_opens", "b", "Browse Impala")


def check_back_from_browser(ctx: RunContext) -> SmokeResult:
    ctx.driver.send_key("Escape")
    return _press_and_wait(ctx, "browser_back_dashboard", "Escape", "Active Jobs")


def check_history_opens(ctx: RunContext) -> SmokeResult:
    return _press_and_wait(ctx, "history_opens", "h", "History")


def check_back_from_history(ctx: RunContext) -> SmokeResult:
    ctx.driver.send_key("Escape")
    return _press_and_wait(ctx, "history_back_dashboard", "Escape", "Active Jobs")


def check_preview_opens(ctx: RunContext) -> SmokeResult:
    ctx.driver.send_key("n")
    ctx.driver.wait_for(r"New Job|Source.*Destination", timeout=10)
    ctx.driver.send_key("Escape")
    ctx.driver.send_key("p")
    screen = ctx.driver.wait_for(r"Preview|SQL Preview", timeout=10)
    return _ok("preview_opens", "Preview screen opened", screen)


def check_quit_cleanly(ctx: RunContext) -> SmokeResult:
    ctx.driver.send_key("Escape")
    ctx.driver.send_key("Escape")
    ctx.driver.send_key("Escape")
    ctx.driver.send_key("q")
    screen = ctx.driver.wait_for(r"[\$#>]\s*$", timeout=10)
    return _ok("quit_cleanly", "Dispatch exited and tmux session stayed alive", screen)


def check_install_runs(ctx: RunContext) -> SmokeResult:
    email = ctx.config.operator_email or "dispatch-smoke@example.com"
    screen = _run_shell_and_wait(
        ctx,
        f"DISPATCH_EMAIL={email} ./install.sh && echo RESULT_INSTALL_OK",
        r"Dispatch installed|^RESULT_INSTALL_OK$",
        timeout=120,
    )
    return _ok("install_runs", "install.sh completed", screen)


def check_dispatch_shortcut(ctx: RunContext) -> SmokeResult:
    screen = _run_shell_and_wait(ctx, "which dispatch", r"\.local/bin/dispatch|/dispatch", timeout=10)
    return _ok("dispatch_shortcut", "dispatch shortcut resolved", screen)


def check_klist_detected(ctx: RunContext) -> SmokeResult:
    ctx.driver.send_keys("klist -s && echo RESULT_KRB_OK || echo RESULT_KRB_MISSING")
    screen = ctx.driver.wait_for(r"^RESULT_KRB_OK$|^RESULT_KRB_MISSING$", timeout=10)
    if re.search(r"^RESULT_KRB_MISSING$", screen, flags=re.MULTILINE):
        return _fail("klist_detected", "klist did not find a valid Kerberos ticket", screen)
    return _ok("klist_detected", "Kerberos ticket detected", screen)


def check_impala_shell_path(ctx: RunContext) -> SmokeResult:
    ctx.driver.send_keys("which impala-shell >/dev/null 2>&1 && echo RESULT_IMPALA_OK || echo RESULT_IMPALA_MISSING")
    screen = ctx.driver.wait_for(r"^RESULT_IMPALA_OK$|^RESULT_IMPALA_MISSING$", timeout=10)
    if re.search(r"^RESULT_IMPALA_MISSING$", screen, flags=re.MULTILINE):
        return _fail("impala_shell_path", "impala-shell was not on PATH", screen)
    return _ok("impala_shell_path", "impala-shell was found on PATH", screen)


def check_python_version(ctx: RunContext) -> SmokeResult:
    py = "$(command -v python3.11 || command -v python3.10 || echo /sys_apps_01/python/python310/bin/python3.10)"
    screen = _run_shell_and_wait(ctx, f"{py} --version", r"Python 3\.(10|11)", timeout=10)
    return _ok("python_version", "Supported Python is available", screen)


def check_cwd_captured(ctx: RunContext) -> SmokeResult:
    ctx.driver.send_keys("cd /tmp && dispatch")
    ctx.driver.wait_for("Active Jobs", timeout=20)
    ctx.driver.send_key("n")
    ctx.driver.wait_for(r"New Job", timeout=10)
    screen = ctx.capture("cwd_captured")
    ctx.driver.send_key("Escape")
    ctx.driver.send_key("Escape")
    ctx.driver.wait_for("Active Jobs", timeout=10)
    ctx.driver.send_key("q")
    ctx.driver.wait_for(r"[\$#>]\s*$", timeout=10)
    if "/tmp" not in screen:
        return _fail("cwd_captured", "New Job screen did not show launch directory /tmp", screen)
    return _ok("cwd_captured", "Launch-time cwd is visible in New Job", screen)


def check_ads_storage_writable(ctx: RunContext) -> SmokeResult:
    command = "mkdir -p /ads_storage/$USER/.dispatch && touch /ads_storage/$USER/.dispatch/.smoke_test && echo RESULT_WRITE_OK"
    screen = _run_shell_and_wait(ctx, command, r"^RESULT_WRITE_OK$", timeout=15)
    return _ok("ads_storage_writable", "/ads_storage/$USER/.dispatch is writable", screen)


def check_textual_rendering(ctx: RunContext) -> SmokeResult:
    ctx.driver.send_keys("dispatch")
    screen = ctx.driver.wait_for("Active Jobs", timeout=20)
    ctx.driver.send_key("q")
    ctx.driver.wait_for(r"[\$#>]\s*$", timeout=10)
    if any(ch in screen for ch in ("┌", "┐", "│", "─")) and "\x1b[" not in screen:
        return _ok("textual_rendering", "Textual box drawing rendered cleanly", screen)
    return _fail("textual_rendering", "Box drawing was missing or ANSI escapes were visible", screen)


def check_version_matches(ctx: RunContext) -> SmokeResult:
    command = "test -f VERSION && test -f /ads_storage/$USER/.dispatch/installed_version && diff -u VERSION /ads_storage/$USER/.dispatch/installed_version >/dev/null && echo RESULT_VERSION_OK || echo RESULT_VERSION_FAIL"
    ctx.driver.send_keys(command)
    screen = ctx.driver.wait_for(r"^RESULT_VERSION_OK$|^RESULT_VERSION_FAIL$", timeout=15)
    if re.search(r"^RESULT_VERSION_FAIL$", screen, flags=re.MULTILINE):
        return _fail("version_matches", "Installed version did not match repo VERSION", screen)
    return _ok("version_matches", "Installed version matches repo VERSION", screen)


LEVEL_1_CHECKS: list[Callable[[RunContext], SmokeResult]] = [
    check_ssh_connectivity,
    check_tmux_geometry,
    check_compileall,
    check_dispatch_opens,
    check_dashboard_renders,
    check_kerberos_status,
    check_new_job_navigation,
    check_back_to_dashboard_from_new_job,
    check_browser_opens,
    check_back_from_browser,
    check_history_opens,
    check_back_from_history,
    check_preview_opens,
    check_quit_cleanly,
]

LEVEL_2_CHECKS: list[Callable[[RunContext], SmokeResult]] = [
    check_install_runs,
    check_dispatch_shortcut,
    check_klist_detected,
    check_impala_shell_path,
    check_python_version,
    check_cwd_captured,
    check_ads_storage_writable,
    check_textual_rendering,
    check_version_matches,
]


def run_check(ctx: RunContext, level: int, check: Callable[[RunContext], SmokeResult]) -> SmokeResult:
    started = time.monotonic()
    try:
        result = check(ctx)
    except Exception as exc:  # noqa: BLE001 - the runner must continue by default.
        try:
            screen = ctx.capture(check.__name__)
        except Exception:  # noqa: BLE001
            screen = ""
        result = _fail(check.__name__.removeprefix("check_"), f"{type(exc).__name__}: {exc}", screen)
    result.level = level
    result.elapsed_ms = int((time.monotonic() - started) * 1000)
    ctx.results.append(result)
    print_result(result)
    return result


def print_result(result: SmokeResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    try:
        print(f"[{status}] L{result.level} {result.name}: {result.message}")
    except Exception:
        safe_msg = str(result.message).encode("ascii", "replace").decode("ascii")
        print(f"[{status}] L{result.level} {result.name}: {safe_msg}")
    
    if not result.passed and result.screen_capture:
        print("--- last screen ---")
        try:
            print(result.screen_capture)
        except Exception:
            print(result.screen_capture.encode(sys.stdout.encoding or 'ascii', 'replace').decode(sys.stdout.encoding or 'ascii'))
        print("--- end screen ---")


def selected_levels(level: str) -> list[int]:
    if level == "all":
        return [1, 2]
    return [int(level)]


def checks_for_level(level: int) -> Iterable[Callable[[RunContext], SmokeResult]]:
    return LEVEL_1_CHECKS if level == 1 else LEVEL_2_CHECKS


def write_json_report(
    ctx: RunContext,
    levels: list[int],
    started: float,
    path: str | Path | None = None,
) -> Path:
    report_path = Path(path) if path else REPORTS_DIR / f"smoke_{ctx.run_timestamp}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "host": ctx.config.host,
        "levels_run": levels,
        "duration_seconds": round(time.monotonic() - started, 3),
        "results": [asdict(result) for result in ctx.results],
        "summary": {
            "total": len(ctx.results),
            "passed": sum(1 for result in ctx.results if result.passed),
            "failed": sum(1 for result in ctx.results if not result.passed),
        },
        "screen_captures": str(ctx.screens_dir) if ctx.screens_dir else None,
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report_path


def print_summary(results: Sequence[SmokeResult], report_path: Path) -> None:
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    print(f"\nSummary: {passed}/{len(results)} passed, {failed} failed")
    print(f"JSON report: {report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run production smoke checks against Dispatch over SSH/tmux")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--level", choices=["1", "2", "all"], default="1")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--save-screens", action="store_true")
    parser.add_argument("--json-report", help="Write JSON report to this path")
    parser.add_argument("--fail-fast", action="store_true", help="Stop after the first failed check")
    parser.add_argument("--passcode", help="Passcode for SSH authentication")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    started = time.monotonic()
    run_timestamp = utc_stamp()
    try:
        config = load_config(args.config)
        driver = TmuxDriver.from_config(config, retries=2)
        ctx = RunContext(
            config=config,
            driver=driver,
            run_timestamp=run_timestamp,
            save_screens=args.save_screens,
            verbose=args.verbose,
        )
        ctx.passcode = args.passcode
        levels = selected_levels(args.level)
        for level in levels:
            for check in checks_for_level(level):
                result = run_check(ctx, level, check)
                if args.fail_fast and not result.passed:
                    raise SystemExit(1)
        report_path = write_json_report(ctx, levels, started, args.json_report)
        print_summary(ctx.results, report_path)
        return 0 if all(result.passed for result in ctx.results) else 1
    except SystemExit as exc:
        code = int(exc.code or 0)
        try:
            report_path = write_json_report(ctx, levels, started, args.json_report)  # type: ignore[name-defined]
            print_summary(ctx.results, report_path)  # type: ignore[name-defined]
        except Exception:
            pass
        return code
    except Exception as exc:  # noqa: BLE001
        print(f"Harness error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
