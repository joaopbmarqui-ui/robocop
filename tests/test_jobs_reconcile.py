"""Regression tests for stale Job reconciliation and explicit Pending cancel."""

from __future__ import annotations

import asyncio
from pathlib import Path

from dispatch import jobs, manifest, process
from dispatch.app import DispatchApp
from dispatch.screens.job_detail import JobDetailScreen


def _create_csv_job(tmp_path: Path, *, user: str = "testuser") -> Path:
    sql_file = tmp_path / "query.sql"
    sql_file.write_text("SELECT 1;", encoding="utf-8")
    job_dir, _item = manifest.create_job(
        source={"type": "SqlFile", "sql_path_at_launch": str(sql_file)},
        destination={
            "type": "Csv",
            "schema": "",
            "table_name": "dispatch_export",
            "csv_path": "",
        },
        params={"to_email": "test@example.com", "subject": "Test"},
        launch_cwd=tmp_path,
        sql_text="SELECT 1;",
        user=user,
    )
    return job_dir


def test_stale_running_manifest_reconciles_to_failed(
    mock_env, tmp_path: Path, monkeypatch
) -> None:
    job_dir = _create_csv_job(tmp_path)
    manifest_path = job_dir / "manifest.json"
    (job_dir / "run.log").write_text("started\n", encoding="utf-8")
    manifest.update(manifest_path, state="Running", pid=999_999, started_at=manifest.now_utc())
    monkeypatch.setattr(jobs, "pid_is_alive", lambda pid: False)

    reconciled = jobs.reconcile_manifest(manifest_path)

    assert reconciled is not None
    assert reconciled["state"] == "Failed"
    assert reconciled["exit_code"] == -1
    assert reconciled["finished_at"] is not None
    assert "stale runner pid 999999" in (job_dir / "run.log").read_text(encoding="utf-8")


def test_running_jobs_reconcile_dead_pid_before_counting(
    mock_env, tmp_path: Path, monkeypatch
) -> None:
    stale_dir = _create_csv_job(tmp_path)
    live_dir = _create_csv_job(tmp_path)
    manifest.update(
        stale_dir / "manifest.json",
        state="Running",
        pid=111_111,
        started_at=manifest.now_utc(),
    )
    manifest.update(
        live_dir / "manifest.json",
        state="Running",
        pid=222_222,
        started_at=manifest.now_utc(),
    )
    monkeypatch.setattr(jobs, "pid_is_alive", lambda pid: pid == 222_222)

    running = jobs.running_jobs()

    assert [item["pid"] for item in running] == [222_222]
    assert manifest.load(stale_dir / "manifest.json")["state"] == "Failed"
    assert jobs.can_launch() is True


def test_cancel_dead_pid_marks_running_job_failed(
    mock_env_with_config, tmp_path: Path, monkeypatch
) -> None:
    job_dir = _create_csv_job(tmp_path)
    manifest.update(
        job_dir / "manifest.json",
        state="Running",
        pid=123_456,
        started_at=manifest.now_utc(),
    )

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = JobDetailScreen(job_dir.name)
            app.push_screen(screen)
            await pilot.pause()
            monkeypatch.setattr(screen, "_confirm_cancel", _async_true)
            monkeypatch.setattr(
                process,
                "cancel_process_group",
                lambda pid: (_ for _ in ()).throw(ProcessLookupError(pid)),
            )
            monkeypatch.setattr(jobs, "pid_is_alive", lambda pid: False)

            await screen._cancel_flow()
            await pilot.pause()

    asyncio.run(run())

    final = manifest.load(job_dir / "manifest.json")
    assert final["state"] == "Failed"
    assert final["exit_code"] == -1


def test_pending_cancel_without_pid_marks_job_cancelled(
    mock_env_with_config, tmp_path: Path, monkeypatch
) -> None:
    job_dir = _create_csv_job(tmp_path)

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(120, 40)) as pilot:
            screen = JobDetailScreen(job_dir.name)
            app.push_screen(screen)
            await pilot.pause()
            monkeypatch.setattr(screen, "_confirm_pending_cancel", _async_true)

            await screen._cancel_flow()
            await pilot.pause()

    asyncio.run(run())

    final = manifest.load(job_dir / "manifest.json")
    assert final["state"] == "Cancelled"
    assert final["exit_code"] == 0
    assert final["finished_at"] is not None
    assert job_dir.exists()


async def _async_true(*_args, **_kwargs) -> bool:
    return True
