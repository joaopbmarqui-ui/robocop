from __future__ import annotations

from pathlib import Path


def test_local_check_uses_repo_local_pytest_temp() -> None:
    script = Path("tools/dev/local_check.ps1").read_text(encoding="utf-8")

    assert "$localTemp" in script
    assert "$env:TEMP = $localTemp" in script
    assert "$env:TMP = $localTemp" in script
    assert "--basetemp" in script
    assert ".local-check-pytest" in script
