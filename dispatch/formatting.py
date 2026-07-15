"""Shared formatting helpers for Dispatch TUI."""

from __future__ import annotations

import re
from datetime import datetime, timezone

_SIZE_RE = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*([KMGT]?B)\s*$",
    re.IGNORECASE,
)
_SIZE_UNITS = ("B", "KB", "MB", "GB", "TB", "PB")


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


def format_timestamp(value: str | None) -> str:
    """Render a manifest UTC timestamp as compact local time."""
    parsed = parse_utc_timestamp(value)
    if parsed is None:
        return "--"
    return parsed.astimezone().strftime("%Y-%m-%d %H:%M")


# State rendering: every state pairs a distinct symbol with its label so
# meaning survives terminals without color (NO_COLOR, low-color SSH).
_STATE_STYLES: dict[str, tuple[str, str]] = {
    "Running": ("\u25cf", "green"),
    "Succeeded": ("\u2713", "green"),
    "Failed": ("\u2717", "red"),
    "Cancelled": ("\u25cb", "dim"),
    "Pending": ("\u25cc", "dim"),
}


def format_state(state: str, error_code: str | None = None) -> str:
    """Markup for a Job state cell, consistent across all tables."""
    symbol, color = _STATE_STYLES.get(state, ("\u25cf", "dim"))
    label = state.upper()
    if state == "Failed" and error_code:
        label = f"{label} \u00b7 {error_code}"
    return f"[{color}]{symbol} {label}[/]"


def style_log_line(line: str) -> str:
    """Shared markup styling for orchestrator log lines (dim timestamps/comments)."""
    if line.lstrip().startswith("--"):
        return f"[dim]{line}[/]"
    if line.startswith("[") and "]" in line:
        idx = line.index("]") + 1
        return f"[dim]{line[:idx]}[/]{line[idx:]}"
    return line


def parse_data_size(value: str) -> int | None:
    """Parse Impala ``SHOW TABLE STATS`` size strings such as ``370.45MB``."""
    match = _SIZE_RE.match(value.strip())
    if not match:
        return None
    amount = float(match.group(1))
    if amount < 0:
        return None
    unit = match.group(2).upper()
    if unit == "B":
        return int(amount)
    try:
        exponent = _SIZE_UNITS.index(unit)
    except ValueError:
        return None
    return int(amount * (1024**exponent))


def format_data_size(bytes_value: int | None) -> str:
    """Format byte counts consistently for table lists (e.g. ``12.6 MB``)."""
    if bytes_value is None:
        return "—"
    if bytes_value < 0:
        return "—"
    if bytes_value == 0:
        return "0 B"
    value = float(bytes_value)
    unit_index = 0
    while value >= 1024 and unit_index < len(_SIZE_UNITS) - 1:
        value /= 1024
        unit_index += 1
    unit = _SIZE_UNITS[unit_index]
    if unit_index == 0:
        return f"{int(value)} {unit}"
    return f"{value:.1f} {unit}"


def format_kerberos_ttl(ttl_seconds: int | None) -> str:
    """Compact Kerberos TTL text shared by the sidebar chip and stat card."""
    if ttl_seconds is None:
        return "missing"
    hours, remainder = divmod(ttl_seconds, 3600)
    minutes = remainder // 60
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"
