"""Tests for offline usage telemetry (emit + aggregation + CLI)."""

from __future__ import annotations

import json
import os
import stat
import sys
import threading
import time
from pathlib import Path

import pytest

from dispatch import telemetry

try:
    import fcntl
except ImportError:  # Windows: every test that needs it carries _posix_only
    fcntl = None  # type: ignore[assignment]

_posix_only = pytest.mark.skipif(
    sys.platform == "win32",
    reason="POSIX file semantics (Edge Node behavior: flock/umask/euid/fifo/symlink)",
)


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
    yield {"data_root": data_root, "shared": shared}
    assert telemetry.flush(timeout=1)
    telemetry.reset_session_for_tests()


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            lines.append(json.loads(line))
    return lines


def test_emit_writes_private_and_shared_jsonl(telemetry_env):
    telemetry.note_session_start(cwd=Path("queries"))
    assert telemetry.flush(timeout=1)

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
    telemetry.note_session_start()
    assert telemetry.flush(timeout=1)
    assert not telemetry.private_events_path().exists()
    assert not telemetry.shared_user_events_path().exists()


def test_emit_still_writes_private_when_shared_unwritable(telemetry_env, monkeypatch):
    # Point shared root at a file so mkdir/open fails for the shared path.
    blocker = telemetry_env["shared"] / "not_a_dir"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("DISPATCH_TELEMETRY_DIR", str(blocker))
    telemetry.note_screen_view("overview")
    assert telemetry.flush(timeout=1)
    assert len(_read_jsonl(telemetry.private_events_path())) == 1


@_posix_only
def test_emit_does_not_follow_shared_user_symlink(telemetry_env):
    users_dir = telemetry_env["shared"] / "users"
    users_dir.mkdir()
    target = telemetry_env["shared"] / "not-telemetry.txt"
    target.write_text("unchanged\n", encoding="utf-8")
    telemetry.shared_user_events_path().symlink_to(target)

    telemetry.note_screen_view("overview")
    assert telemetry.flush(timeout=1)

    assert target.read_text(encoding="utf-8") == "unchanged\n"
    assert len(_read_jsonl(telemetry.private_events_path())) == 1


@_posix_only
def test_emit_makes_shared_file_analyst_readable_under_restrictive_umask(telemetry_env):
    users_dir = telemetry_env["shared"] / "users"
    users_dir.mkdir()
    users_dir.chmod(0o1777)
    previous_umask = os.umask(0o077)
    try:
        telemetry.note_session_start()
        assert telemetry.flush(timeout=1)
    finally:
        os.umask(previous_umask)

    mode = stat.S_IMODE(telemetry.shared_user_events_path().stat().st_mode)
    assert mode == 0o644


@_posix_only
def test_emit_skips_shared_file_not_owned_by_current_user(telemetry_env, monkeypatch):
    users_dir = telemetry_env["shared"] / "users"
    users_dir.mkdir()
    shared_path = telemetry.shared_user_events_path()
    shared_path.write_text("preexisting\n", encoding="utf-8")
    expected_euid = os.geteuid() + 1
    monkeypatch.setattr(telemetry.os, "geteuid", lambda: expected_euid)

    telemetry.note_screen_view("overview")
    assert telemetry.flush(timeout=1)

    assert shared_path.read_text(encoding="utf-8") == "preexisting\n"
    assert len(_read_jsonl(telemetry.private_events_path())) == 1


def test_emit_drops_username_that_is_not_one_path_component(telemetry_env, monkeypatch):
    monkeypatch.setenv("USER", "../escape")

    telemetry.note_screen_view("overview")

    assert telemetry.flush(timeout=1)
    assert not list(telemetry_env["shared"].rglob("*.jsonl"))
    assert not telemetry.private_events_path().exists()


@_posix_only
def test_emit_skips_fifo_without_stalling_writer(telemetry_env):
    users_dir = telemetry_env["shared"] / "users"
    users_dir.mkdir()
    shared_path = telemetry.shared_user_events_path()
    os.mkfifo(shared_path)

    telemetry.note_screen_view("overview")
    started = time.monotonic()
    flushed = telemetry.flush(timeout=0.1)
    elapsed = time.monotonic() - started

    reader_fd = os.open(shared_path, os.O_RDONLY | os.O_NONBLOCK)
    try:
        assert telemetry.flush(timeout=1)
    finally:
        os.close(reader_fd)

    assert flushed is True
    assert elapsed < 0.1


@_posix_only
def test_emit_skips_contended_private_lock_and_writes_shared_copy(telemetry_env):
    private_path = telemetry.private_events_path()
    private_path.parent.mkdir(parents=True)
    with private_path.open("a", encoding="utf-8") as locked_file:
        fcntl.flock(locked_file.fileno(), fcntl.LOCK_EX)
        telemetry.note_screen_view("overview")
        assert telemetry.flush(timeout=1)

    assert _read_jsonl(private_path) == []
    shared_events = _read_jsonl(telemetry.shared_user_events_path())
    assert [event["event"] for event in shared_events] == ["screen_view"]


def test_who_and_summary_aggregate_events(telemetry_env):
    telemetry.note_session_start(cwd=Path("a"))
    telemetry.note_screen_view("overview")
    telemetry.note_screen_view("new_job")
    telemetry.note_job_launched(
        job_id="job1",
        source="SqlFile",
        destination="Csv",
    )
    telemetry.note_launch_refused("slot_cap")
    telemetry.note_session_end()
    assert telemetry.flush(timeout=1)

    who = telemetry.who(days=30, root=telemetry.shared_telemetry_dir())
    assert who["users"][0]["user"] == "telemetry_user"
    assert who["users"][0]["sessions"] == 1
    assert who["users"][0]["jobs_launched"] == 1

    summary = telemetry.summary(days=30, root=telemetry.shared_telemetry_dir())
    assert summary["screens"]["overview"] == 1
    assert summary["screens"]["new_job"] == 1
    assert summary["launches"]["SqlFile|Csv"] == 1
    assert summary["refusals"]["slot_cap"] == 1


def test_default_summary_does_not_count_private_and_shared_copies_twice(telemetry_env):
    telemetry.note_session_start()
    assert telemetry.flush(timeout=1)

    assert telemetry.summary(days=30)["sessions"] == 1


def test_cli_telemetry_who_prints_users(telemetry_env, capsys, monkeypatch):
    telemetry.note_session_start()
    assert telemetry.flush(timeout=1)
    monkeypatch.setattr(sys, "argv", ["dispatch", "telemetry", "who", "--days", "7"])
    from dispatch.__main__ import main

    main()
    out = capsys.readouterr().out
    assert "telemetry_user" in out
    assert "sessions" in out.lower() or "1" in out


def test_cli_telemetry_who_rejects_summary_only_user_filter(telemetry_env, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["dispatch", "telemetry", "who", "--user", "telemetry_user"],
    )
    from dispatch.__main__ import main

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2


def test_note_screen_view_returns_without_waiting_for_file_io(telemetry_env, monkeypatch):
    release_writer = threading.Event()

    def slow_append(*_args, **_kwargs):
        release_writer.wait(timeout=1)

    monkeypatch.setattr(telemetry, "_append_line", slow_append)
    started = time.monotonic()
    telemetry.note_screen_view("overview")
    elapsed = time.monotonic() - started
    release_writer.set()

    assert elapsed < 0.1
    assert telemetry.flush(timeout=1)


@pytest.mark.parametrize(
    ("function_name", "value"),
    [
        ("note_screen_view", "account_email"),
        ("note_launch_refused", "raw error text"),
    ],
)
def test_event_helpers_drop_values_outside_the_catalog(telemetry_env, function_name, value):
    event_helper = getattr(telemetry, function_name)

    event_helper(value)

    assert telemetry.flush(timeout=1)
    assert not telemetry.private_events_path().exists()


def test_job_launched_helper_emits_only_catalogued_properties(telemetry_env):
    telemetry.note_job_launched(
        job_id="job1",
        source="SqlFile",
        destination="Csv",
    )
    assert telemetry.flush(timeout=1)

    event = _read_jsonl(telemetry.private_events_path())[0]
    assert event["event"] == "job_launched"
    assert event["props"] == {
        "job_id": "job1",
        "source": "SqlFile",
        "destination": "Csv",
    }


def test_flush_waits_up_to_timeout_when_queue_is_full(telemetry_env, monkeypatch):
    writer_entered = threading.Event()
    release_writer = threading.Event()

    def blocking_append(*_args, **_kwargs):
        writer_entered.set()
        release_writer.wait(timeout=1)

    monkeypatch.setattr(telemetry, "_append_line", blocking_append)
    telemetry.note_screen_view("overview")
    assert writer_entered.wait(timeout=1)
    for _ in range(telemetry._QUEUE_CAPACITY):
        telemetry.note_screen_view("overview")

    started = time.monotonic()
    flushed = telemetry.flush(timeout=0.1)
    elapsed = time.monotonic() - started
    release_writer.set()
    assert telemetry.flush(timeout=1)

    assert flushed is False
    assert elapsed >= 0.08
