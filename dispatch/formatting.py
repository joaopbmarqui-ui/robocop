"""Shared formatting helpers for Dispatch TUI."""

from __future__ import annotations

from datetime import datetime, timezone


def parse_utc_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def format_elapsed(item: dict) -> str:
    """Format elapsed time consistently across Dashboard and Job Detail."""
    start_dt = parse_utc_timestamp(item.get("started_at"))
    if start_dt is None:
        return "--"
    if item.get("state") == "Running":
        delta = datetime.now(timezone.utc) - start_dt
    else:
        end_dt = parse_utc_timestamp(item.get("finished_at"))
        if end_dt is None:
            return "--"
        delta = end_dt - start_dt
    total = max(0, int(delta.total_seconds()))
    if total < 60:
        return f"{total}s"
    minutes = total // 60
    if minutes < 60:
        return f"{minutes}m {total % 60}s"
    hours = minutes // 60
    return f"{hours}h {minutes % 60}m"


def format_job_id(job_id: str, style: str = "short") -> str:
    """Format job IDs for table display."""
    if style == "full":
        return job_id
    if len(job_id) > 20:
        return job_id[9:]
    return job_id
