from __future__ import annotations

from pathlib import Path

import pytest

from dispatch import manifest, sql


def test_resolve_csv_output_path_accepts_direct_csv_in_launch_cwd(tmp_path: Path) -> None:
    resolved = sql.resolve_csv_output_path(tmp_path, "dispatch_export.csv")

    assert resolved == tmp_path.resolve() / "dispatch_export.csv"


@pytest.mark.parametrize(
    ("raw_path", "message"),
    [
        pytest.param("nested/dispatch_export.csv", "launch directory", id="nested-path"),
        pytest.param("bad name.csv", "plain Impala identifier", id="unsafe-stem"),
        pytest.param("../escape.csv", "launch directory", id="escape"),
        pytest.param("dispatch_export.txt", ".csv", id="wrong-suffix"),
    ],
)
def test_resolve_csv_output_path_rejects_unsafe_paths(
    tmp_path: Path, raw_path: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        sql.resolve_csv_output_path(tmp_path, raw_path)


def test_build_orchestrator_calls_rejects_nested_explicit_csv_path(tmp_path: Path) -> None:
    job_dir = tmp_path / "job"
    job_dir.mkdir()

    with pytest.raises(ValueError, match="launch directory"):
        manifest.build_orchestrator_calls(
            job_dir,
            {"type": "SqlFile"},
            {
                "type": "Csv",
                "table_name": "dispatch_export",
                "csv_path": "nested/dispatch_export.csv",
            },
            {"to_email": "x@y.com", "subject": "S"},
            tmp_path,
            "user1",
        )
