"""Job directory queries and lifecycle helpers."""

from __future__ import annotations

from contextlib import contextmanager
import logging
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


def list_manifests(root: Path | None = None) -> list[manifest.JobManifest]:
    base = root or config.jobs_dir()
    if not base.exists():
        return []
    paths = sorted(base.glob("*/manifest.json"), reverse=True)
    loaded: list[manifest.JobManifest] = []
    for path in paths:
        try:
            loaded.append(_load_manifest_cached(path))
        except Exception as exc:
            logger.warning("Skipping corrupt manifest %s: %s", path, exc)
            continue
    # Drop cache entries for deleted job dirs so the cache cannot grow
    # unbounded across a long supervision session.
    if len(_manifest_cache) > len(paths):
        live = set(paths)
        for stale in [cached for cached in _manifest_cache if cached not in live]:
            del _manifest_cache[stale]
    return loaded


def running_jobs(root: Path | None = None) -> list[manifest.JobManifest]:
    return [item for item in list_manifests(root) if item["state"] == "Running"]


def launch_slot_jobs(root: Path | None = None) -> list[manifest.JobManifest]:
    """Jobs that already occupy one of the user's launch slots.

    ``Pending`` manifests have passed launch acceptance and are waiting for the
    detached runner to flip them to ``Running``, so they count against the cap.
    """
    return [item for item in list_manifests(root) if item["state"] in LAUNCH_SLOT_STATES]


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
    for item in list_manifests(root):
        finished = parse_time(item["finished_at"])
        if item["state"] == "Running" or finished is None or now - finished <= ACTIVE_WINDOW:
            result.append(item)
    return result


def history_jobs(root: Path | None = None) -> list[manifest.JobManifest]:
    now = datetime.now(timezone.utc)
    result = []
    for item in list_manifests(root):
        finished = parse_time(item["finished_at"])
        if finished is not None and now - finished > ACTIVE_WINDOW:
            result.append(item)
    return result
