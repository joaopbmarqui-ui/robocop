"""Tests for the TUI subprocess gateway."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

from dispatch import process


def test_windows_resolver_prefers_exact_python_script_before_pathext_wrapper(
    tmp_path: Path, monkeypatch
) -> None:
    script = tmp_path / "kinit"
    script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    (tmp_path / "kinit.exe").write_bytes(b"legacy wrapper")
    monkeypatch.setenv("PATH", str(tmp_path))

    resolved = process._resolve_exec_argv(("kinit", "user@REALM"), windows=True)

    assert resolved == (sys.executable, str(script), "user@REALM")


@pytest.mark.asyncio
async def test_launch_runner_uses_detached_nohup_setsid_contract(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[tuple[tuple[str, ...], dict]] = []

    class FakeProc:
        pid = 4242

    async def fake_create_subprocess_exec(*argv: str, **kwargs):
        calls.append((argv, kwargs))
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    pid = await process.launch_runner(tmp_path / "job1")

    assert pid == 4242
    assert calls
    argv, kwargs = calls[0]
    assert argv[:5] == ("nohup", "setsid", process.sys.executable, "-m", "dispatch.runner")
    assert argv[-2:] == ("--job-dir", str(tmp_path / "job1"))
    assert kwargs["stdin"] is asyncio.subprocess.DEVNULL
    assert kwargs["stdout"] is asyncio.subprocess.DEVNULL
    assert kwargs["stderr"] is asyncio.subprocess.DEVNULL


def test_cancel_process_group_sends_sigterm_to_group(monkeypatch) -> None:
    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(
        process.os,
        "killpg",
        lambda pid, sig: calls.append((pid, sig)),
        raising=False,
    )

    process.cancel_process_group(4242)

    assert calls == [(4242, process.signal.SIGTERM)]
