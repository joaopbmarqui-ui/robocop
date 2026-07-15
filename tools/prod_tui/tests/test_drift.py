from __future__ import annotations

from tools.prod_tui import drift


def test_runtime_critical_paths_cover_expected_release_surface() -> None:
    paths = drift.runtime_critical_paths()

    assert "dispatch/app.py" in paths
    assert "dispatch/app.tcss" in paths
    assert "scr/Query_Impala_Parametrized.py" in paths
    assert "install.sh" in paths
    assert "onboard.sh" in paths
    assert "shared_runtime.py" in paths
    assert "bin/dispatch" in paths
    assert "update.sh" in paths
    assert "pyproject.toml" in paths
    assert "requirements.txt" in paths
    assert "VERSION" in paths


def test_drift_summary_counts_match_and_missing_states() -> None:
    local = {
        "dispatch/app.py": "aaa",
        "dispatch/app.tcss": "bbb",
        "install.sh": "ccc",
    }
    remote = {
        "dispatch/app.py": "aaa",
        "dispatch/app.tcss": "zzz",
        "update.sh": "ddd",
    }

    summary = drift.summarize_drift(local, remote)

    assert summary["MATCH"] == 1
    assert summary["DRIFT"] == 1
    assert summary["MISSING"] == 1
    assert summary["EXTRA_RUNTIME"] == 1
