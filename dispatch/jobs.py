"""Job directory queries and lifecycle helpers."""

from __future__ import annotations

from contextlib import contextmanager
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from . import config, manifest

logger = logging.getLogger("dispatch.jobs")

ACTIVE_WINDOW = timedelta(days=7)
RUNNING_CAP = 2
LAUNCH_SLOT_STATES = {"Pending", "Running"}

_manifest_cache: dict[Path, tuple[float, manifest.JobManifest]] = {}


class LaunchSlotUnavailable(RuntimeError):
    """Raised when a Job cannot be accepted because all launch slots are full."""


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _load_manifest_cached(path: Path) -> manifest.JobManifest:
    try:
        mtime = path.stat().st_mtime
    except OSError as exc:
        raise ValueError(str(exc)) from exc
    cached = _manifest_cache.get(path)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    loaded = manifest.load(path)
    _manifest_cache[path] = (mtime, loaded)
    return loaded


def _cached_terminal_outside_active_window(path: Path, now: datetime) -> bool:
    """Return whether an unchanged cached manifest can be skipped by Overview.

    The active dashboard only needs Running/Pending Jobs plus terminal Jobs
    inside the seven-day supervision window. Once a terminal manifest is cached
    and known to be older than that window, each refresh only stats the file to
    detect changes rather than reparsing JSON or reconciling process state.
    """
    cached = _manifest_cache.get(path)
    if cached is None:
        return False
    try:
        mtime = path.stat().st_mtime
    except OSError as exc:
        raise ValueError(str(exc)) from exc
    cached_mtime, item = cached
    if cached_mtime != mtime or item["state"] in LAUNCH_SLOT_STATES:
        return False
    finished = parse_time(item["finished_at"])
    return finished is not None and now - finished > ACTIVE_WINDOW


def _manifest_paths(root: Path | None = None) -> list[Path]:
    base = root or config.jobs_dir()
    if not base.exists():
        return []
    return sorted(base.glob("*/manifest.json"), reverse=True)


def _prune_manifest_cache(paths: list[Path]) -> None:
    # Drop cache entries for deleted job dirs so the cache cannot grow
    # unbounded across a long supervision session.
    if len(_manifest_cache) > len(paths):
        live = set(paths)
        for stale in [cached for cached in _manifest_cache if cached not in live]:
            del _manifest_cache[stale]


def list_manifests(root: Path | None = None) -> list[manifest.JobManifest]:
    paths = _manifest_paths(root)
    loaded: list[manifest.JobManifest] = []
    for path in paths:
        try:
            loaded.append(_load_manifest_cached(path))
        except Exception as exc:
            logger.warning("Skipping corrupt manifest %s: %s", path, exc)
            continue
    _prune_manifest_cache(paths)
    return loaded


def pid_is_alive(pid: int) -> bool:
    """Return whether ``pid`` still names a live process.

    ``os.kill(pid, 0)`` performs the conservative POSIX liveness probe without
    sending a signal. A permission failure means a process exists but cannot be
    signalled by this user, so it is treated as alive.
    """
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _append_stale_log(job_dir: Path, pid: int) -> None:
    log_path = job_dir / "run.log"
    if not log_path.exists():
        return
    try:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"[dispatch] stale runner pid {pid} not found; "
                "manifest marked Failed\n"
            )
    except OSError:
        logger.info("Could not append stale-runner note for %s", job_dir)


def reconcile_manifest(path: Path) -> manifest.JobManifest | None:
    """Load and conservatively reconcile one manifest.

    Only ``Running`` Jobs with a stored PID are reconciled. ``Pending`` Jobs are
    left untouched because the product has not chosen an automatic age
    threshold for spawn stalls.
    """
    item = _load_manifest_cached(path)
    pid = item.get("pid")
    if item["state"] != "Running" or pid is None or pid_is_alive(pid):
        return item
    updated = manifest.update(
        path,
        state="Failed",
        exit_code=-1,
        finished_at=manifest.now_utc(),
    )
    _manifest_cache.pop(path, None)
    _append_stale_log(path.parent, pid)
    return updated


def reconciled_list_manifests(root: Path | None = None) -> list[manifest.JobManifest]:
    paths = _manifest_paths(root)
    loaded: list[manifest.JobManifest] = []
    for path in paths:
        try:
            loaded.append(reconcile_manifest(path) or _load_manifest_cached(path))
        except Exception as exc:
            logger.warning("Skipping corrupt manifest %s: %s", path, exc)
            continue
    _prune_manifest_cache(paths)
    return loaded


def running_jobs(root: Path | None = None) -> list[manifest.JobManifest]:
    return [item for item in reconciled_list_manifests(root) if item["state"] == "Running"]


def launch_slot_jobs(root: Path | None = None) -> list[manifest.JobManifest]:
    """Jobs that already occupy one of the user's launch slots.

    ``Pending`` manifests have passed launch acceptance and are waiting for the
    detached runner to flip them to ``Running``, so they count against the cap.
    """
    paths = _manifest_paths(root)
    loaded: list[manifest.JobManifest] = []
    for path in paths:
        try:
            item = reconcile_manifest(path) or _load_manifest_cached(path)
        except Exception as exc:
            logger.warning("Skipping corrupt manifest %s: %s", path, exc)
            continue
        if item["state"] in LAUNCH_SLOT_STATES:
            loaded.append(item)
            if len(loaded) >= RUNNING_CAP:
                break
    _prune_manifest_cache(paths)
    return loaded


def can_launch(root: Path | None = None) -> bool:
    return len(launch_slot_jobs(root)) < RUNNING_CAP


@contextmanager
def _launch_lock(user: str | None = None) -> Iterator[None]:
    jobs_path = config.jobs_dir(user)
    jobs_path.mkdir(parents=True, exist_ok=True)
    lock_path = jobs_path / ".dispatch-launch.lock"
    with lock_path.open("a+b") as handle:
        try:
            import fcntl  # type: ignore[import-not-found]

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return
        except ImportError:
            pass

        try:
            import msvcrt  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "Dispatch launch locking requires fcntl.flock on POSIX or "
                "msvcrt.locking on Windows; refusing to run without a real lock."
            ) from exc

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def create_job_if_slot_available(
    source: manifest.Source,
    destination: manifest.Destination,
    params: dict[str, Any],
    launch_cwd: Path,
    sql_text: str = "",
    user: str | None = None,
) -> tuple[Path, manifest.JobManifest]:
    """Create a Pending Job only if a launch slot is available.

    The slot decision and manifest creation happen while holding a filesystem
    lock so concurrent TUI sessions cannot both consume the last slot.
    """
    with _launch_lock(user):
        root = config.jobs_dir(user)
        if not can_launch(root=root):
            raise LaunchSlotUnavailable(
                f"Already at the {RUNNING_CAP}-Job concurrency cap; wait for one to finish"
            )
        return manifest.create_job(
            source=source,
            destination=destination,
            params=params,
            launch_cwd=launch_cwd,
            sql_text=sql_text,
            user=user,
        )


def active_jobs(root: Path | None = None) -> list[manifest.JobManifest]:
    now = datetime.now(timezone.utc)
    result = []
    paths = _manifest_paths(root)
    for path in paths:
        try:
            if _cached_terminal_outside_active_window(path, now):
                continue
            item = reconcile_manifest(path) or _load_manifest_cached(path)
        except Exception as exc:
            logger.warning("Skipping corrupt manifest %s: %s", path, exc)
            continue
        finished = parse_time(item["finished_at"])
        if item["state"] == "Running" or finished is None or now - finished <= ACTIVE_WINDOW:
            result.append(item)
    _prune_manifest_cache(paths)
    return result


def history_jobs(root: Path | None = None) -> list[manifest.JobManifest]:
    now = datetime.now(timezone.utc)
    result = []
    for item in reconciled_list_manifests(root):
        finished = parse_time(item["finished_at"])
        if finished is not None and now - finished > ACTIVE_WINDOW:
            result.append(item)
    return result
