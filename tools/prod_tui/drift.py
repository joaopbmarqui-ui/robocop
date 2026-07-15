"""Public drift verification for runtime-critical Dispatch files."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from tools.prod_tui.reporting import OperationReport, ReportCheck, write_report
from tools.prod_tui.robocop_tmux import DEFAULT_CONFIG_PATH, ProdTuiConfig, TmuxDriver, load_config

ROOT = Path(__file__).resolve().parents[2]


def _runtime_path_filter(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.startswith("dispatch/") and normalized.endswith((".py", ".tcss")):
        return True
    if normalized.startswith("scr/") and normalized.endswith(".py"):
        return True
    return normalized in {
        "bin/dispatch",
        "install.sh",
        "onboard.sh",
        "shared_runtime.py",
        "update.sh",
        "pyproject.toml",
        "requirements.txt",
        "VERSION",
    }


def runtime_critical_paths() -> list[str]:
    paths: list[str] = []
    for root in ("dispatch", "scr"):
        root_path = ROOT / root
        if not root_path.exists():
            continue
        for path in root_path.rglob("*"):
            if path.is_file() and _runtime_path_filter(path.relative_to(ROOT).as_posix()):
                paths.append(path.relative_to(ROOT).as_posix())
    for name in (
        "bin/dispatch",
        "install.sh",
        "onboard.sh",
        "shared_runtime.py",
        "update.sh",
        "pyproject.toml",
        "requirements.txt",
        "VERSION",
    ):
        if (ROOT / name).exists():
            paths.append(name)
    return sorted(set(paths))


def summarize_drift(local: dict[str, str], remote: dict[str, str]) -> dict[str, int]:
    summary = {"MATCH": 0, "DRIFT": 0, "MISSING": 0, "EXTRA_RUNTIME": 0}
    for path, local_md5 in local.items():
        remote_md5 = remote.get(path)
        if remote_md5 is None:
            summary["MISSING"] += 1
        elif remote_md5 == local_md5:
            summary["MATCH"] += 1
        else:
            summary["DRIFT"] += 1
    for path in remote:
        if path not in local:
            summary["EXTRA_RUNTIME"] += 1
    return summary


def _git_output(args: list[str], *, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=text)


def local_runtime_map(commit: str) -> dict[str, str]:
    _git_output(["git", "rev-parse", "--verify", commit])
    mapping: dict[str, str] = {}
    for path in runtime_critical_paths():
        blob = subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        mapping[path] = hashlib.md5(blob).hexdigest()
    return mapping


def _extract_payload(screen: str, start: str, end: str) -> str:
    start_index = screen.find(start)
    end_index = screen.find(end)
    if start_index == -1 or end_index == -1 or end_index <= start_index:
        raise RuntimeError(f"Could not find payload markers {start!r} / {end!r}")
    return screen[start_index + len(start) : end_index].strip()


def _remote_python(driver: TmuxDriver, script: str, *, timeout: float = 60.0) -> tuple[str, int]:
    encoded = base64.b64encode(script.encode("utf-8")).decode("ascii")
    py = "$(command -v python3.11 || command -v python3.10 || command -v python3)"
    command = f"printf %s {encoded} | base64 -d | {py} -"
    return driver.run_remote(command, timeout=timeout)


def remote_runtime_map(driver: TmuxDriver, repo_path: str) -> dict[str, str]:
    script = f"""
import hashlib
import json
from pathlib import Path

root = Path({repo_path!r})
files = {runtime_critical_paths()!r}
payload = {{}}
for rel in files:
    path = root / rel
    if path.is_file():
        payload[rel] = hashlib.md5(path.read_bytes()).hexdigest()
for rel_root, suffixes in ((root / "dispatch", (".py", ".tcss")), (root / "scr", (".py",))):
    if not rel_root.exists():
        continue
    for path in rel_root.rglob("*"):
        if path.is_file() and path.suffix in suffixes:
            rel = path.relative_to(root).as_posix()
            payload.setdefault(rel, hashlib.md5(path.read_bytes()).hexdigest())
print("DRIFT_PAYLOAD_START")
print(json.dumps(payload, sort_keys=True))
print("DRIFT_PAYLOAD_END")
"""
    screen, code = _remote_python(driver, script, timeout=120)
    if code != 0:
        raise RuntimeError(f"Remote runtime scan failed with exit code {code}")
    payload = _extract_payload(screen, "DRIFT_PAYLOAD_START", "DRIFT_PAYLOAD_END")
    return json.loads(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare runtime-critical files against an expected commit"
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--commit", required=True)
    parser.add_argument("--json-report")
    parser.add_argument("--reuse-session", action="store_true")
    return parser


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


def _node_name(config: ProdTuiConfig) -> str:
    host = config.host.rsplit("@", 1)[-1]
    if host.endswith("0004.mastercard.int"):
        return "node04"
    if host.endswith("0003.mastercard.int"):
        return "node03"
    return host.split(".", 1)[0]


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    driver = TmuxDriver.from_config(config, retries=2)
    try:
        _ensure_session(config, driver, args.reuse_session)
        local = local_runtime_map(args.commit)
        remote = remote_runtime_map(driver, config.repo_path)
        summary = summarize_drift(local, remote)
        checks = [
            ReportCheck(
                name="runtime_drift",
                passed=summary["DRIFT"] == 0 and summary["MISSING"] == 0,
                message=(
                    f"MATCH={summary['MATCH']} DRIFT={summary['DRIFT']} "
                    f"MISSING={summary['MISSING']} EXTRA_RUNTIME={summary['EXTRA_RUNTIME']}"
                ),
                evidence=summary,
            )
        ]
        report = OperationReport(
            operation="drift",
            status="passed" if checks[0].passed else "failed",
            node=_node_name(config),
            host=config.host,
            repo_path=config.repo_path,
            deployment_commit=args.commit,
            install_decision="not_applicable",
            checks=checks,
        )
        if args.json_report:
            write_report(args.json_report, report)
            print(f"JSON report: {args.json_report}")
        print(checks[0].message)
        return 0 if report.status == "passed" else 1
    except Exception as exc:  # noqa: BLE001
        print(f"Drift failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
