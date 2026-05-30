"""Best-effort error classification from orchestrator logs."""

from __future__ import annotations

import re
from pathlib import Path

PATTERNS: list[tuple[str, str]] = [
    ("SYNTAX", r"AnalysisException.*Syntax error"),
    ("TABLE_NOT_FOUND", r"Table.*does not exist|TableNotFoundException"),
    ("MEMORY", r"Memory limit exceeded|MEMORY_LIMIT_EXCEEDED"),
    ("AUTH", r"AuthorizationException|Kerberos.*expired"),
    ("QUEUE", r"Rejected.*pool|All pools busy|queue timeout"),
]

SUGGESTIONS: dict[str, str] = {
    "SYNTAX": "Review the SQL file for syntax errors and re-run Preview SQL.",
    "TABLE_NOT_FOUND": "Verify the source table or schema exists in Impala.",
    "MEMORY": "Reduce query scope or ask your platform team about memory limits.",
    "AUTH": "Refresh your Kerberos ticket with kinit and retry.",
    "QUEUE": "Wait for cluster capacity or try again during off-peak hours.",
}


def classify(log_path: Path, *, tail_lines: int = 50) -> str | None:
    """Return a short error code if a known pattern matches recent log lines."""
    if not log_path.is_file():
        return None
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    lines = text.splitlines()[-tail_lines:]
    blob = "\n".join(lines)
    for code, pattern in PATTERNS:
        if re.search(pattern, blob, re.IGNORECASE):
            return code
    return None


def suggestion(code: str | None) -> str:
    if code is None:
        return "Check the log for details."
    return SUGGESTIONS.get(code, "Check the log for details.")


def first_matching_line(log_path: Path, code: str | None, *, tail_lines: int = 50) -> str:
    if code is None or not log_path.is_file():
        return ""
    pattern = next((p for c, p in PATTERNS if c == code), None)
    if pattern is None:
        return ""
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-tail_lines:]
    except OSError:
        return ""
    compiled = re.compile(pattern, re.IGNORECASE)
    for line in reversed(lines):
        if compiled.search(line):
            return line.strip()[:120]
    return ""
