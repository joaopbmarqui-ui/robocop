"""Regression checks for the Dispatch user-story tracker and completion audit."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "docs" / "dispatch_user_story_tracker.csv"
AUDIT = ROOT / "docs" / "dispatch_user_story_completion_audit.md"
TRACKER_NAME_PATTERN = re.compile(r"(tracker|user.*story|feature.*status)", re.IGNORECASE)
EXTERNAL_GATE_PATTERN = re.compile(
    r"\b(Edge|Linux|Impala|Kerberos|kinit|klist|SSH|terminal|cluster|Level 4|real)\b|still needs|unavailable",
    re.IGNORECASE,
)

REQUIRED_COLUMNS = {
    "feature_id",
    "area",
    "user_story",
    "expected_behavior",
    "code_evidence",
    "test_evidence",
    "manual_test",
    "status",
    "local_test_status",
    "errors_found",
    "fix_status",
    "retest_status",
}

NON_FILE_TEST_EVIDENCE = {"Manual doc review", "git remote -v"}


def _tracker_rows() -> list[dict[str, str]]:
    with TRACKER.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _evidence_entries(value: str) -> list[str]:
    return [entry.strip() for entry in value.split(";") if entry.strip()]


def _evidence_path_and_lines(entry: str) -> tuple[Path | None, tuple[int, int] | None]:
    if entry in NON_FILE_TEST_EVIDENCE:
        return None, None
    relative_path = entry.split("::", maxsplit=1)[0]
    line_range: tuple[int, int] | None = None
    line_match = re.search(r":(?P<start>\d+)(?:-(?P<end>\d+))?$", relative_path)
    if line_match:
        start = int(line_match.group("start"))
        end = int(line_match.group("end") or start)
        line_range = (start, end)
        relative_path = relative_path[: line_match.start()]
    relative_path = relative_path.replace("\\", "/")
    while relative_path.startswith("./"):
        relative_path = relative_path[2:]
    relative_path = re.sub(r"/+", "/", relative_path).lstrip("/")
    assert relative_path and " " not in relative_path, f"Unparseable evidence reference: {entry}"
    return ROOT / relative_path, line_range


def _evidence_file(entry: str) -> Path | None:
    path, _line_range = _evidence_path_and_lines(entry)
    return path


def test_tracker_has_required_contract_and_unique_feature_ids() -> None:
    rows = _tracker_rows()

    assert rows
    assert set(rows[0]) == REQUIRED_COLUMNS

    feature_ids = [row["feature_id"] for row in rows]
    assert len(feature_ids) == len(set(feature_ids))


def test_user_story_tracker_is_the_only_tracker_artifact() -> None:
    candidates = [
        path
        for path in (ROOT / "docs").rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".csv", ".xlsx"}
        and TRACKER_NAME_PATTERN.search(path.name)
    ]

    assert candidates == [TRACKER]


def test_tracker_rows_have_story_behavior_and_evidence() -> None:
    rows = _tracker_rows()

    for row in rows:
        assert row["feature_id"]
        assert row["area"]
        assert row["user_story"].startswith("As ")
        assert row["expected_behavior"]
        assert row["code_evidence"]
        assert row["test_evidence"]
        assert row["manual_test"]
        assert row["status"] == "Implemented"
        assert row["local_test_status"]
        assert row["retest_status"]


def test_documented_errors_have_fix_and_retest_status() -> None:
    for row in _tracker_rows():
        if row["errors_found"] and row["errors_found"] != "None":
            assert row["fix_status"] and row["fix_status"] != "None", row["feature_id"]
            assert row["retest_status"], row["feature_id"]


def test_local_test_pending_language_is_only_used_for_pending_retests() -> None:
    for row in _tracker_rows():
        if re.search(r"pending", row["local_test_status"], re.IGNORECASE):
            assert re.search(r"pending", row["retest_status"], re.IGNORECASE), row["feature_id"]


def test_external_gate_retest_language_is_counted_as_pending() -> None:
    for row in _tracker_rows():
        if EXTERNAL_GATE_PATTERN.search(row["retest_status"]):
            assert re.search(r"pending", row["retest_status"], re.IGNORECASE), row["feature_id"]


def test_tracker_code_evidence_references_existing_files() -> None:
    for row in _tracker_rows():
        for entry in _evidence_entries(row["code_evidence"]):
            path = _evidence_file(entry)
            assert path is not None
            assert path.exists(), f"{row['feature_id']} references missing code evidence: {entry}"


def test_tracker_test_evidence_references_existing_files_or_explicit_manual_evidence() -> None:
    for row in _tracker_rows():
        for entry in _evidence_entries(row["test_evidence"]):
            path = _evidence_file(entry)
            if path is not None:
                assert path.exists(), f"{row['feature_id']} references missing test evidence: {entry}"


def test_tracker_evidence_line_ranges_are_inside_existing_files() -> None:
    for row in _tracker_rows():
        evidence_values = [row["code_evidence"], row["test_evidence"]]
        for value in evidence_values:
            for entry in _evidence_entries(value):
                path, line_range = _evidence_path_and_lines(entry)
                if path is None or line_range is None:
                    continue
                line_count = len(path.read_text(encoding="utf-8").splitlines())
                start, end = line_range
                assert 1 <= start <= end <= line_count, (
                    f"{row['feature_id']} references invalid line range {start}-{end} "
                    f"for {path.relative_to(ROOT)} with {line_count} lines"
                )


def test_pending_rows_match_completion_audit_matrix() -> None:
    rows = _tracker_rows()
    audit = AUDIT.read_text(encoding="utf-8")

    pending = [row for row in rows if re.search(r"pending", row["retest_status"], re.IGNORECASE)]
    count_match = re.search(r"Remaining real-environment retest gates: (\d+) rows", audit)
    guard_match = re.search(r"until the (\d+) pending tracker rows", audit)

    assert count_match is not None
    assert guard_match is not None
    assert int(count_match.group(1)) == len(pending)
    assert int(guard_match.group(1)) == len(pending)

    for row in pending:
        assert f"| {row['feature_id']} |" in audit


def test_pending_audit_matrix_has_route_and_required_evidence() -> None:
    rows = _tracker_rows()
    audit = AUDIT.read_text(encoding="utf-8")
    pending_ids = {
        row["feature_id"]
        for row in rows
        if re.search(r"pending", row["retest_status"], re.IGNORECASE)
    }
    matrix_rows: dict[str, tuple[str, str]] = {}
    for line in audit.splitlines():
        match = re.match(r"\| (?P<feature>[A-Z]+-\d{3}) \| (?P<route>[^|]+) \| (?P<evidence>[^|]+) \|", line)
        if match:
            matrix_rows[match.group("feature")] = (
                match.group("route").strip(),
                match.group("evidence").strip(),
            )

    assert set(matrix_rows) == pending_ids
    for feature_id, (route, evidence) in matrix_rows.items():
        assert route, feature_id
        assert evidence, feature_id
        assert evidence.endswith("."), feature_id


def test_pending_area_counts_match_completion_audit_summary() -> None:
    rows = _tracker_rows()
    audit = AUDIT.read_text(encoding="utf-8")

    pending_area_counts: dict[str, int] = {}
    for row in rows:
        if re.search(r"pending", row["retest_status"], re.IGNORECASE):
            pending_area_counts[row["area"]] = pending_area_counts.get(row["area"], 0) + 1

    for area, count in pending_area_counts.items():
        assert f"| {area} | {count} |" in audit


def test_completion_audit_states_not_complete_while_pending_gates_remain() -> None:
    rows = _tracker_rows()
    audit = AUDIT.read_text(encoding="utf-8")
    pending = [row for row in rows if re.search(r"pending", row["retest_status"], re.IGNORECASE)]
    verdict_match = re.search(r"Not complete\..*?(\d+) real-environment user-story gates pending", audit, re.DOTALL)

    assert pending
    assert "## Prompt-To-Artifact Checklist" in audit
    assert "Current verdict:" in audit
    assert verdict_match is not None
    assert int(verdict_match.group(1)) == len(pending)
    assert "TCP 2222" in audit


def test_completion_audit_next_action_requires_preflight_before_tmux() -> None:
    audit = AUDIT.read_text(encoding="utf-8")
    next_action = audit.split("## Next Required Action", maxsplit=1)[1]

    preflight_index = next_action.index("py -m tools.prod_tui preflight")
    tmux_index = next_action.index("py -m tools.prod_tui tmux start")

    assert preflight_index < tmux_index
    assert "connected: false" in next_action
    assert "Do not run `tmux start`, `smoke`, `job`, or `level`" in next_action


def test_tracker_and_audit_keep_harness_commands_config_explicit() -> None:
    command_pattern = re.compile(r"\b(?:py|python) -m tools\.prod_tui (?:tmux|smoke|job|level)\b")
    offenders: list[str] = []

    for artifact in (TRACKER, AUDIT):
        for line_number, line in enumerate(artifact.read_text(encoding="utf-8").splitlines(), start=1):
            if command_pattern.search(line) and "--config" not in line:
                offenders.append(f"{artifact.relative_to(ROOT)}:{line_number}:{line}")

    assert offenders == []
