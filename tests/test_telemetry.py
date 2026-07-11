"""Tests for offline usage telemetry (emit + aggregation + CLI)."""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

import pytest

from dispatch import telemetry


@pytest.fixture()
def telemetry_env(tmp_path, monkeypatch):
    """Isolate private + shared telemetry under tmp_path."""
    data_root = tmp_path / "data"
    shared = tmp_path / "shared_telemetry"
    data_root.mkdir()
    shared.mkdir()
    monkeypatch.setenv("DISPATCH_DATA_ROOT", str(data_root))
    monkeypatch.setenv("DISPATCH_TELEMETRY_DIR", str(shared))
    monkeypatch.delenv("DISPATCH_TELEMETRY", raising=False)
    monkeypatch.setenv("USER", "telemetry_user")
    telemetry.reset_session_for_tests()
    return {"data_root": data_root, "shared": shared}


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            lines.append(json.loads(line))
    return lines


def test_emit_writes_private_and_shared_jsonl(telemetry_env):
    telemetry.emit("session_start", {"cwd_basename": "queries"})

    private = telemetry.private_events_path()
    shared = telemetry.shared_user_events_path()
    private_events = _read_jsonl(private)
    shared_events = _read_jsonl(shared)

    assert len(private_events) == 1
    assert private_events[0]["event"] == "session_start"
    assert private_events[0]["user"] == "telemetry_user"
    assert private_events[0]["props"]["cwd_basename"] == "queries"
    assert "session_id" in private_events[0]
    assert private_events == shared_events


def test_emit_disabled_when_opted_out(telemetry_env, monkeypatch):
    monkeypatch.setenv("DISPATCH_TELEMETRY", "0")
    telemetry.emit("session_start", {})
    assert not telemetry.private_events_path().exists()
    assert not telemetry.shared_user_events_path().exists()


def test_emit_still_writes_private_when_shared_unwritable(telemetry_env, monkeypatch):
    # Point shared root at a file so mkdir/open fails for the shared path.
    blocker = telemetry_env["shared"] / "not_a_dir"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("DISPATCH_TELEMETRY_DIR", str(blocker))
    telemetry.emit("screen_view", {"screen": "overview"})
    assert len(_read_jsonl(telemetry.private_events_path())) == 1


def test_emit_does_not_follow_shared_user_symlink(telemetry_env):
    users_dir = telemetry_env["shared"] / "users"
    users_dir.mkdir()
    target = telemetry_env["shared"] / "not-telemetry.txt"
    target.write_text("unchanged\n", encoding="utf-8")
    telemetry.shared_user_events_path().symlink_to(target)

    telemetry.emit("screen_view", {"screen": "overview"})

    assert target.read_text(encoding="utf-8") == "unchanged\n"
    assert len(_read_jsonl(telemetry.private_events_path())) == 1


def test_emit_makes_shared_file_analyst_readable_under_restrictive_umask(telemetry_env):
    users_dir = telemetry_env["shared"] / "users"
    users_dir.mkdir()
    users_dir.chmod(0o1777)
    previous_umask = os.umask(0o077)
    try:
        telemetry.emit("session_start", {})
    finally:
        os.umask(previous_umask)

    mode = stat.S_IMODE(telemetry.shared_user_events_path().stat().st_mode)
    assert mode == 0o644


def test_emit_skips_shared_file_not_owned_by_current_user(telemetry_env, monkeypatch):
    users_dir = telemetry_env["shared"] / "users"
    users_dir.mkdir()
    shared_path = telemetry.shared_user_events_path()
    shared_path.write_text("preexisting\n", encoding="utf-8")
    expected_euid = os.geteuid() + 1
    monkeypatch.setattr(telemetry.os, "geteuid", lambda: expected_euid)

    telemetry.emit("screen_view", {"screen": "overview"})

    assert shared_path.read_text(encoding="utf-8") == "preexisting\n"
    assert len(_read_jsonl(telemetry.private_events_path())) == 1


def test_who_and_summary_aggregate_events(telemetry_env):
    telemetry.emit("session_start", {"cwd_basename": "a"})
    telemetry.emit("screen_view", {"screen": "overview"})
    telemetry.emit("screen_view", {"screen": "new_job"})
    telemetry.emit(
        "job_launched",
        {"job_id": "job1", "source": "SqlFile", "destination": "Csv"},
    )
    telemetry.emit("launch_refused", {"reason": "slot_cap"})
    telemetry.emit("session_end", {"duration_s": 12})

    who = telemetry.who(days=30, root=telemetry.shared_telemetry_dir())
    assert who["users"][0]["user"] == "telemetry_user"
    assert who["users"][0]["sessions"] == 1
    assert who["users"][0]["jobs_launched"] == 1

    summary = telemetry.summary(days=30, root=telemetry.shared_telemetry_dir())
    assert summary["screens"]["overview"] == 1
    assert summary["screens"]["new_job"] == 1
    assert summary["launches"]["SqlFile|Csv"] == 1
    assert summary["refusals"]["slot_cap"] == 1


def test_cli_telemetry_who_prints_users(telemetry_env, capsys, monkeypatch):
    telemetry.emit("session_start", {})
    monkeypatch.setattr(sys, "argv", ["dispatch", "telemetry", "who", "--days", "7"])
    from dispatch.__main__ import main

    main()
    out = capsys.readouterr().out
    assert "telemetry_user" in out
    assert "sessions" in out.lower() or "1" in out
