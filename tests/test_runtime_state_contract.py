"""User state remains private when the Python runtime is shared."""

from __future__ import annotations

from pathlib import Path

from dispatch import config
from dispatch.app import DispatchApp


def test_users_resolve_distinct_private_state(monkeypatch) -> None:
    monkeypatch.delenv("DISPATCH_DATA_ROOT", raising=False)

    alice_home = config.dispatch_home("alice")
    bob_home = config.dispatch_home("bob")

    assert alice_home == Path("/ads_storage/alice/.dispatch")
    assert bob_home == Path("/ads_storage/bob/.dispatch")
    assert alice_home != bob_home
    assert config.jobs_dir("alice").is_relative_to(alice_home)
    assert config.config_path("bob").is_relative_to(bob_home)


def test_app_captures_caller_working_directory_without_personal_venv(
    tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "data"
    dispatch_home = data_root / ".dispatch"
    dispatch_home.mkdir(parents=True)
    monkeypatch.setenv("DISPATCH_DATA_ROOT", str(data_root))
    monkeypatch.chdir(tmp_path)

    app = DispatchApp()

    assert app.launch_cwd == tmp_path
    assert not (dispatch_home / "venv").exists()

