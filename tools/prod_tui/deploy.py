"""Public deploy and rollback command for the Dispatch Edge-node harness."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from tools.prod_tui.drift import runtime_critical_paths
from tools.prod_tui.reporting import OperationReport, ReportCheck, write_report
from tools.prod_tui.robocop_tmux import DEFAULT_CONFIG_PATH, ProdTuiConfig, TmuxDriver, load_config

ROOT = Path(__file__).resolve().parents[2]
_INSTALL_TRIGGER_PATHS = {
    "bin/dispatch",
    "install.sh",
    "pyproject.toml",
    "requirements.txt",
    "shared_runtime.py",
    "VERSION",
    "dispatch/__main__.py",
    "dispatch/__init__.py",
    "dispatch/version.py",
}


@dataclass(frozen=True)
class InstallDecision:
    action: str
    reason: str


def decide_install_action(*, mode: str, changed_paths: list[str]) -> InstallDecision:
    if mode == "always":
        return InstallDecision("run", "Install forced by --install always")
    if mode == "never":
        return InstallDecision("skip", "Install skipped by --install never")
    sensitive = sorted(
        path
        for path in changed_paths
        if path in _INSTALL_TRIGGER_PATHS or path.startswith("dispatch/")
    )
    if sensitive:
        return InstallDecision(
            "run", f"Install-sensitive files changed: {', '.join(sensitive[:6])}"
        )
    return InstallDecision(
        "skip", "No install-sensitive files changed between the deployed and target commits"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update one Edge node to an exact deployment commit"
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--commit", required=True)
    parser.add_argument("--install", choices=["auto", "always", "never"], default="auto")
    parser.add_argument("--json-report")
    parser.add_argument("--reuse-session", action="store_true")
    parser.add_argument("--rollback-from")
    return parser


def _node_name(config: ProdTuiConfig) -> str:
    host = config.host.rsplit("@", 1)[-1]
    if host.endswith("0004.mastercard.int"):
        return "node04"
    if host.endswith("0003.mastercard.int"):
        return "node03"
    return host.split(".", 1)[0]


def _extract_payload(screen: str, start: str, end: str) -> str:
    start_index = screen.find(start)
    end_index = screen.find(end)
    if start_index == -1 or end_index == -1 or end_index <= start_index:
        raise RuntimeError(f"Could not find payload markers {start!r} / {end!r}")
    return screen[start_index + len(start) : end_index].strip()


def _ensure_session(config: ProdTuiConfig, driver: TmuxDriver, reuse_session: bool) -> None:
    if driver.session_exists():
        return
    if reuse_session:
        raise RuntimeError(
            f"--reuse-session was set but no live tmux session {config.session_name!r} exists. "
            "Authenticate one first with py -m tools.prod_tui tmux start --config <CONFIG> --passcode <CODE>."
        )
    ready = driver.start_session(passcode=None)
    if not ready:
        raise RuntimeError(
            "Started a tmux session but it still needs human authentication. "
            "Enter the PASSCODE in that pane, then rerun with --reuse-session."
        )


def _run_remote_python(
    driver: TmuxDriver, script: str, *, timeout: float = 60.0
) -> tuple[str, int]:
    encoded = base64.b64encode(script.encode("utf-8")).decode("ascii")
    py = "$(command -v python3.11 || command -v python3.10 || command -v python3)"
    command = f"printf %s {encoded} | base64 -d | {py} -"
    return driver.run_remote(command, timeout=timeout)


def _remote_git_output(
    driver: TmuxDriver, repo_path: str, command: str, *, timeout: float = 60.0
) -> str:
    screen, code = driver.run_remote(f"cd {repo_path} && {command}", timeout=timeout)
    if code != 0:
        raise RuntimeError(f"Remote command failed ({code}): {command}")
    return screen


def _remote_rev_parse(driver: TmuxDriver, repo_path: str, ref: str) -> str:
    screen = _remote_git_output(driver, repo_path, f"git rev-parse --verify {ref}", timeout=30)
    return screen.strip().splitlines()[-2 if "__RC_" in screen else -1].strip()


def _remote_changed_paths(
    driver: TmuxDriver, repo_path: str, previous: str, target: str
) -> list[str]:
    screen = _remote_git_output(
        driver,
        repo_path,
        (
            "git fetch --prune bitbucket main:refs/remotes/bitbucket/main >/dev/null 2>&1 && "
            f"git diff --name-only {previous} {target}"
        ),
        timeout=90,
    )
    lines = [line.strip() for line in screen.splitlines() if line.strip()]
    return [line for line in lines if not line.startswith("git ") and "__RC_" not in line]


def _permission_evidence(driver: TmuxDriver, repo_path: str) -> dict[str, object]:
    script = f"""
import json
import os
from pathlib import Path

root = Path({repo_path!r})
files = {runtime_critical_paths()!r}
missing = []
unreadable = []
for rel in files:
    path = root / rel
    if not path.exists():
        missing.append(rel)
    elif not os.access(path, os.R_OK):
        unreadable.append(rel)
payload = {{
    "root_traversable": root.is_dir() and os.access(root, os.X_OK),
    "update_executable": os.access(root / "update.sh", os.X_OK),
    "install_executable": os.access(root / "install.sh", os.X_OK),
    "onboard_executable": os.access(root / "onboard.sh", os.X_OK),
    "shared_launcher_executable": os.access(root / "bin" / "dispatch", os.X_OK),
    "runtime_files_checked": len(files),
    "missing_runtime_files": missing,
    "unreadable_runtime_files": unreadable,
}}
print("PERMISSION_PAYLOAD_START")
print(json.dumps(payload, sort_keys=True))
print("PERMISSION_PAYLOAD_END")
"""
    screen, code = _run_remote_python(driver, script, timeout=120)
    if code != 0:
        raise RuntimeError(f"Permission verification failed with exit code {code}")
    payload = _extract_payload(screen, "PERMISSION_PAYLOAD_START", "PERMISSION_PAYLOAD_END")
    return json.loads(payload)


def _install_command(config: ProdTuiConfig) -> str:
    py = "$(command -v python3.11 || command -v python3.10)"
    return f"DISPATCH_PYTHON_BIN={py} ./install.sh"


def _runtime_evidence(driver: TmuxDriver, repo_path: str) -> dict[str, object]:
    script = f"""
import json
import os
import stat
import subprocess
from pathlib import Path

root = Path({repo_path!r})
current = root / ".venv" / "current"
runtime = current.resolve(strict=True)
metadata = json.loads((runtime / ".complete.json").read_text(encoding="utf-8"))
bundle_manifest = json.loads(
    (Path.home() / ".edge-deploy" / "bundles" / "robocop" / "current" / "manifest.json")
    .read_text(encoding="utf-8")
)
help_result = subprocess.run(
    [str(root / "bin" / "dispatch"), "--help"],
    cwd=root,
    text=True,
    capture_output=True,
    check=False,
)
import_result = subprocess.run(
    [str(runtime / "bin" / "python"), "-c", "import sqlglot; print(sqlglot.__file__)"],
    text=True,
    capture_output=True,
    check=False,
)
publicly_writable = []
for path in [runtime, *runtime.rglob("*")]:
    if stat.S_IMODE(path.stat().st_mode) & 0o022:
        publicly_writable.append(str(path.relative_to(runtime)))
payload = {{
    "active_runtime": str(runtime),
    "runtime_digest": metadata.get("bundle_digest"),
    "bundle_digest": bundle_manifest.get("bundle_digest"),
    "pip_check": metadata.get("pip_check"),
    "help_exit_code": help_result.returncode,
    "sqlglot_exit_code": import_result.returncode,
    "sqlglot_path": import_result.stdout.strip(),
    "publicly_writable": publicly_writable,
}}
print("RUNTIME_PAYLOAD_START")
print(json.dumps(payload, sort_keys=True))
print("RUNTIME_PAYLOAD_END")
"""
    screen, code = _run_remote_python(driver, script, timeout=120)
    if code != 0:
        raise RuntimeError(f"Shared runtime verification failed with exit code {code}")
    payload = _extract_payload(screen, "RUNTIME_PAYLOAD_START", "RUNTIME_PAYLOAD_END")
    return json.loads(payload)


def _local_rev_parse(commit: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", commit],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.rollback_from and args.rollback_from == args.commit:
        print("Rollback requires different --rollback-from and --commit values.", file=sys.stderr)
        return 2

    config = load_config(args.config)
    driver = TmuxDriver.from_config(config, retries=2)
    try:
        target_commit = _local_rev_parse(args.commit)
    except subprocess.CalledProcessError:
        print(f"Deploy failed: local commit {args.commit!r} does not resolve.", file=sys.stderr)
        return 2

    try:
        _ensure_session(config, driver, args.reuse_session)
        previous_commit = _remote_rev_parse(driver, config.repo_path, "HEAD")
        changed_paths = _remote_changed_paths(
            driver, config.repo_path, previous_commit, target_commit
        )
        install = decide_install_action(mode=args.install, changed_paths=changed_paths)
        operation = "rollback" if args.rollback_from else "deploy"
        checks: list[ReportCheck] = []

        if args.rollback_from and previous_commit != _local_rev_parse(args.rollback_from):
            checks.append(
                ReportCheck(
                    name="rollback_source_commit",
                    passed=False,
                    message=(
                        f"Node is at {previous_commit}, expected rollback source "
                        f"{_local_rev_parse(args.rollback_from)}"
                    ),
                )
            )
            report = OperationReport(
                operation=operation,
                status="blocked",
                node=_node_name(config),
                host=config.host,
                repo_path=config.repo_path,
                deployment_commit=target_commit,
                previous_remote_commit=previous_commit,
                install_decision=install.action,
                checks=checks,
            )
            if args.json_report:
                write_report(args.json_report, report)
                print(f"JSON report: {args.json_report}")
            return 2

        update_command = (
            f"cd {config.repo_path} && "
            "DISPATCH_UPDATE_REMOTE=bitbucket DISPATCH_UPDATE_BRANCH=main "
            f"./update.sh {target_commit}"
        )
        update_screen, update_code = driver.run_remote(update_command, timeout=180)
        checks.append(ReportCheck("update", update_code == 0, f"update.sh exit {update_code}"))

        final_commit = _remote_rev_parse(driver, config.repo_path, "HEAD")
        checks.append(
            ReportCheck(
                "final_commit",
                final_commit == target_commit,
                f"Remote HEAD is {final_commit}",
                {"expected_commit": target_commit},
            )
        )

        if install.action == "run":
            install_screen, install_code = driver.run_remote(
                f"cd {config.repo_path} && {_install_command(config)}",
                timeout=240,
            )
            checks.append(
                ReportCheck(
                    "install",
                    install_code == 0,
                    install.reason,
                    {"exit_code": install_code},
                )
            )
        else:
            checks.append(ReportCheck("install", True, install.reason))

        permissions = _permission_evidence(driver, config.repo_path)
        permissions_ok = (
            bool(permissions["root_traversable"])
            and bool(permissions["update_executable"])
            and bool(permissions["install_executable"])
            and bool(permissions["onboard_executable"])
            and bool(permissions["shared_launcher_executable"])
            and not permissions["missing_runtime_files"]
            and not permissions["unreadable_runtime_files"]
        )
        checks.append(
            ReportCheck(
                "permissions",
                permissions_ok,
                "Permission evidence collected",
                permissions,
            )
        )

        runtime = _runtime_evidence(driver, config.repo_path)
        runtime_ok = (
            runtime["runtime_digest"] == runtime["bundle_digest"]
            and runtime["pip_check"] == "passed"
            and runtime["help_exit_code"] == 0
            and runtime["sqlglot_exit_code"] == 0
            and not runtime["publicly_writable"]
        )
        checks.append(
            ReportCheck(
                "shared_runtime",
                runtime_ok,
                "Active runtime, bundle metadata, launcher, and sqlglot verified",
                runtime,
            )
        )

        status = "passed" if all(check.passed for check in checks) else "failed"
        report = OperationReport(
            operation=operation,
            status=status,
            node=_node_name(config),
            host=config.host,
            repo_path=config.repo_path,
            deployment_commit=target_commit,
            previous_remote_commit=previous_commit,
            install_decision=install.action,
            checks=checks,
            extra={"changed_paths": changed_paths},
        )
        if args.json_report:
            write_report(args.json_report, report)
            print(f"JSON report: {args.json_report}")
        for check in checks:
            outcome = "PASS" if check.passed else "FAIL"
            print(f"[{outcome}] {check.name}: {check.message}")
        return 0 if status == "passed" else 1
    except Exception as exc:  # noqa: BLE001
        print(f"Deploy failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
