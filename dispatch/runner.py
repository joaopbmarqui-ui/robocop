"""Stdlib runner that owns Dispatch Job lifecycle."""
# pylint: disable=global-statement

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import FrameType

from . import manifest as manifest_io

CURRENT_PROC: subprocess.Popen[bytes] | None = None
MANIFEST_PATH: Path | None = None
LOG = None


def _log(message: str) -> None:
    if LOG is not None:
        LOG.write(f"{message}\n".encode("utf-8"))
        LOG.flush()


def _write_error(job_dir: Path, error: Exception) -> None:
    payload = {"error": str(error), "type": type(error).__name__}
    (job_dir / "manifest.error.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _set_terminal_state(state: manifest_io.JobState, exit_code: int) -> None:
    if MANIFEST_PATH is None:
        return
    manifest_io.update(
        MANIFEST_PATH,
        state=state,
        exit_code=exit_code,
        finished_at=manifest_io.now_utc(),
    )


def _handle_sigterm(_signum: int, _frame: FrameType | None) -> None:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    _log("[runner] SIGTERM received; cancelling current orchestrator")
    _set_terminal_state("Cancelled", -signal.SIGTERM)
    if CURRENT_PROC is not None and CURRENT_PROC.poll() is None:
        CURRENT_PROC.terminate()
        deadline = time.monotonic() + 10
        while CURRENT_PROC.poll() is None and time.monotonic() < deadline:
            time.sleep(0.1)
        if CURRENT_PROC.poll() is None:
            CURRENT_PROC.kill()
            CURRENT_PROC.wait()
    raise SystemExit(0)


def _install_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def run(job_dir: Path) -> int:
    global CURRENT_PROC, LOG, MANIFEST_PATH
    manifest_path = job_dir / "manifest.json"
    MANIFEST_PATH = manifest_path

    try:
        manifest = manifest_io.load(manifest_path)
    except Exception as exc:
        _write_error(job_dir, exc)
        return 3

    if manifest["state"] != "Pending":
        return 4

    run_log = job_dir / "run.log"
    job_dir.mkdir(parents=True, exist_ok=True)
    with run_log.open("ab", buffering=0) as log:
        LOG = log
        (job_dir / "run.pid").write_text(str(os.getpid()), encoding="utf-8")
        _install_signal_handlers()
        manifest_io.update(
            manifest_path,
            state="Running",
            started_at=manifest_io.now_utc(),
            pid=os.getpid(),
        )

        try:
            for call in manifest["orchestrator_calls"]:
                _log(f"[runner] starting {call['script']}: {' '.join(call['argv'])}")
                with subprocess.Popen(call["argv"], stdout=log, stderr=log) as proc:
                    CURRENT_PROC = proc
                    rc = proc.wait()
                _log(f"[runner] finished {call['script']} exit={rc}")
                if rc != 0:
                    _set_terminal_state("Failed", rc)
                    return rc
            _set_terminal_state("Succeeded", 0)
            return 0
        except Exception as exc:
            _log(f"[runner] Unhandled error: {exc}")
            _set_terminal_state("Failed", -1)
            return 1
        finally:
            CURRENT_PROC = None
            LOG = None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a Dispatch Job manifest.")
    parser.add_argument("--job-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    return run(args.job_dir.resolve())


if __name__ == "__main__":
    sys.exit(main())
