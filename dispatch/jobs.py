"""Job directory queries and lifecycle helpers."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config, manifest

logger = logging.getLogger("dispatch.jobs")

ACTIVE_WINDOW = timedelta(days=7)
RUNNING_CAP = 2


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def list_manifests(root: Path | None = None) -> list[manifest.JobManifest]:
    base = root or config.jobs_dir()
    if not base.exists():
        return []
    loaded: list[manifest.JobManifest] = []
    for path in sorted(base.glob("*/manifest.json"), reverse=True):
        try:
            loaded.append(manifest.load(path))
        except Exception as exc:
            logger.warning("Skipping corrupt manifest %s: %s", path, exc)
            continue
    return loaded


def running_jobs(root: Path | None = None) -> list[manifest.JobManifest]:
    return [item for item in list_manifests(root) if item["state"] == "Running"]


def can_launch(root: Path | None = None) -> bool:
    return len(running_jobs(root)) < RUNNING_CAP


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
