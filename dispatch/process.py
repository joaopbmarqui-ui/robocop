"""Single subprocess gateway for the Dispatch TUI."""

from __future__ import annotations

import asyncio
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Literal


async def run_exec(
    *argv: str, timeout: float | None = None, stdin_data: bytes | None = None
) -> tuple[int, str, str]:
    # Resolve bare names against PATH ourselves: Windows CreateProcess searches
    # System32 before PATH, so e.g. `klist` would hit the OS tool instead of a
    # PATH-injected mock. shutil.which honors PATH order on every platform; an
    # unresolvable name keeps its FileNotFoundError from create_subprocess_exec.
    executable = shutil.which(argv[0]) or argv[0]
    proc = await asyncio.create_subprocess_exec(
        executable,
        *argv[1:],
        stdin=asyncio.subprocess.PIPE if stdin_data is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(input=stdin_data), timeout=timeout)
    except asyncio.TimeoutError:
        proc.terminate()
        await proc.wait()
        raise
    return proc.returncode or 0, stdout.decode(errors="replace"), stderr.decode(errors="replace")


async def launch_runner(job_dir: Path) -> int:
    proc = await asyncio.create_subprocess_exec(
        "nohup",
        "setsid",
        sys.executable,
        "-m",
        "dispatch.runner",
        "--job-dir",
        str(job_dir),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    return proc.pid


CancelProcessResult = Literal["signaled", "missing"]


def cancel_process_group(pid: int) -> CancelProcessResult:
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return "missing"
    return "signaled"


def run_interactive(*argv: str) -> int:
    with subprocess.Popen(argv) as proc:
        return proc.wait()
