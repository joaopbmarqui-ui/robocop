"""Release installation and per-user onboarding integration contracts."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from bundle_helpers import make_bundle

ROOT = Path(__file__).resolve().parents[1]


def test_version_sources_agree() -> None:
    import re

    from dispatch.version import __version__

    version_file = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert version_file == __version__
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    assert match is not None
    assert match.group(1) == __version__


def make_install_root(tmp_path: Path) -> Path:
    root = tmp_path / "dispatch-root"
    (root / "bin").mkdir(parents=True)
    for relative in ("install.sh", "shared_runtime.py", "bin/dispatch", "bin/runtime_check.sh"):
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        target.chmod(0o755)
    return root


def make_install_bundle(
    tmp_path: Path, requirements: bytes = b"demo==1.0\n", *, target_python: str = "3.10"
) -> tuple[Path, str]:
    return make_bundle(
        tmp_path,
        {
            "requirements/requirements.txt": requirements,
            "wheels/demo.whl": b"offline-wheel",
        },
        target_python=target_python,
    )


def make_edge_tools(tmp_path: Path) -> Path:
    """Provide the mock klist/impala-shell binaries onboarding preflights."""
    tools = tmp_path / "edge-tools"
    tools.mkdir(exist_ok=True)
    for name in ("klist", "impala-shell"):
        tool = tools / name
        tool.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
        tool.chmod(0o755)
    return tools


def make_approved_python(tmp_path: Path) -> Path:
    fake = tmp_path / "approved-python"
    fake.write_text(
        """#!/usr/bin/env sh
set -eu
case "${1:-}" in
  *shared_runtime.py) exec "__REAL_PYTHON__" "$@" ;;
esac
if [ "${1:-}" = "-m" ] && [ "${2:-}" = "venv" ]; then
  target=$3
  mkdir -p "$target/bin"
  cat > "$target/bin/python" <<'EOF'
#!/usr/bin/env sh
set -eu
printf '%s\n' "$*" >> "${RUNTIME_CALLS:?}"
if [ "${1:-}" = "-c" ]; then
  case "${2:-}" in
    *platform.python_version*) printf '3.10.99\n' ;;
  esac
fi
exit 0
EOF
  chmod 755 "$target/bin/python"
  exit 0
fi
exit 2
""".replace("__REAL_PYTHON__", fake_path(Path(sys.executable))),
        encoding="utf-8",
    )
    fake.chmod(0o755)
    return fake


def install_runtime(
    root: Path, bundle: Path, approved_python: Path, calls: Path
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "EDGE_DEPLOY_BUNDLE_DIR": fake_path(bundle),
            "DISPATCH_PYTHON_BIN": fake_path(approved_python),
            "RUNTIME_CALLS": fake_path(calls),
        }
    )
    return subprocess.run(
        ["sh", "install.sh"],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_release_install_builds_offline_runtime_without_user_state(tmp_path: Path) -> None:
    if shutil.which("sh") is None or os.name == "nt":
        pytest.skip("Linux install smoke requires POSIX executables and symlinks")
    root = make_install_root(tmp_path)
    bundle, digest = make_install_bundle(tmp_path)
    calls = tmp_path / "runtime-calls"
    calls.touch()
    result = install_runtime(root, bundle, make_approved_python(tmp_path), calls)

    assert result.returncode == 0, result.stderr
    runtime = root / ".venv" / "releases" / digest
    assert (runtime / ".complete.json").is_file()
    assert (root / ".venv" / "current").resolve() == runtime.resolve()
    commands = calls.read_text(encoding="utf-8")
    assert "pip install --no-index" in commands
    assert "pip check" in commands
    assert "import textual; import sqlglot" in commands
    assert not (tmp_path / "home" / ".local" / "bin" / "dispatch").exists()
    metadata = json.loads((runtime / ".complete.json").read_text(encoding="utf-8"))
    assert metadata["bundle_digest"] == digest
    assert metadata["pip_check"] == "passed"


def test_failed_release_install_preserves_active_runtime(tmp_path: Path) -> None:
    if shutil.which("sh") is None or os.name == "nt":
        pytest.skip("Linux install smoke requires POSIX executables and symlinks")
    root = make_install_root(tmp_path)
    first_bundle, first_digest = make_install_bundle(tmp_path, b"demo==1.0\n")
    calls = tmp_path / "runtime-calls"
    calls.touch()
    approved = make_approved_python(tmp_path)
    assert install_runtime(root, first_bundle, approved, calls).returncode == 0
    second_bundle, second_digest = make_install_bundle(tmp_path, b"demo==2.0\n")
    (second_bundle / "wheels" / "demo.whl").write_bytes(b"tampered")

    result = install_runtime(root, second_bundle, approved, calls)

    assert result.returncode != 0
    assert (root / ".venv" / "current").resolve().name == first_digest
    assert not (root / ".venv" / "releases" / second_digest / ".complete.json").exists()


def test_release_install_rejects_interpreter_that_misses_bundle_target(tmp_path: Path) -> None:
    if shutil.which("sh") is None or os.name == "nt":
        pytest.skip("Linux install smoke requires POSIX executables and symlinks")
    root = make_install_root(tmp_path)
    # The fake approved interpreter reports 3.10.99; a 3.11 bundle must fail
    # validation before pip runs, leaving no completion marker behind.
    bundle, digest = make_install_bundle(tmp_path, b"demo==3.0\n", target_python="3.11")
    calls = tmp_path / "runtime-calls"
    calls.touch()

    result = install_runtime(root, bundle, make_approved_python(tmp_path), calls)

    assert result.returncode != 0
    assert "targets Python 3.11" in result.stderr
    assert "pip install" not in calls.read_text(encoding="utf-8")
    assert not (root / ".venv" / "releases" / digest / ".complete.json").exists()


def prepare_onboarding_root(tmp_path: Path) -> tuple[Path, Path]:
    root = make_install_root(tmp_path)
    shutil.copy2(ROOT / "onboard.sh", root / "onboard.sh")
    (root / "onboard.sh").chmod(0o755)
    runtime = root / ".venv" / "releases" / ("b" * 64)
    (runtime / "bin").mkdir(parents=True)
    (runtime / ".complete.json").write_text(
        json.dumps(
            {
                "bundle_digest": runtime.name,
                "pip_check": "passed",
                "required_imports": ["textual", "sqlglot"],
            }
        ),
        encoding="utf-8",
    )
    runtime_python = runtime / "bin" / "python"
    runtime_python.write_text(
        '#!/usr/bin/env sh\nprintf \'%s\\n\' "$*" >> "${ONBOARD_CALLS:?}"\nexec "__REAL_PYTHON__" "$@"\n'.replace(
            "__REAL_PYTHON__", fake_path(Path(sys.executable))
        ),
        encoding="utf-8",
    )
    runtime_python.chmod(0o755)
    current = root / ".venv" / "current"
    try:
        current.symlink_to(Path("releases") / runtime.name, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    return root, runtime


def run_onboarding(
    root: Path,
    *,
    home: Path,
    data_root: Path,
    email: str,
    calls: Path,
    edge_tools: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    home.mkdir(exist_ok=True)
    data_root.mkdir(parents=True, exist_ok=True)
    calls.touch(exist_ok=True)
    if edge_tools is None:
        edge_tools = make_edge_tools(root.parent)
    env = os.environ.copy()
    env.update(
        {
            "HOME": fake_path(home),
            "USER": data_root.parent.name,
            "DISPATCH_DATA_ROOT": fake_path(data_root),
            "DISPATCH_EMAIL": email,
            "ONBOARD_CALLS": fake_path(calls),
            "PATH": f"{fake_path(edge_tools)}{os.pathsep}{env.get('PATH', '')}",
        }
    )
    return subprocess.run(
        ["sh", "onboard.sh"],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_existing_user_migrates_launcher_without_touching_state_or_personal_venv(
    tmp_path: Path,
) -> None:
    if shutil.which("sh") is None:
        pytest.skip("onboarding smoke requires sh")
    root, _runtime = prepare_onboarding_root(tmp_path)
    home = tmp_path / "home"
    data_root = tmp_path / "ads_storage" / "alice"
    dispatch_home = data_root / ".dispatch"
    (dispatch_home / "jobs").mkdir(parents=True)
    config = dispatch_home / "config.json"
    config.write_text('{"form_defaults":{"email":"kept@example.com"}}\n', encoding="utf-8")
    job = dispatch_home / "jobs" / "kept.json"
    job.write_text("{}\n", encoding="utf-8")
    personal_venv = dispatch_home / "venv" / "bin" / "python"
    personal_venv.parent.mkdir(parents=True)
    personal_venv.write_text("old\n", encoding="utf-8")
    old_launcher = home / ".local" / "bin" / "dispatch"
    old_launcher.parent.mkdir(parents=True)
    old_launcher.write_text(
        f'exec "{fake_path(personal_venv)}" -m dispatch "$@"\n', encoding="utf-8"
    )
    calls = tmp_path / "onboard-calls"

    result = run_onboarding(
        root,
        home=home,
        data_root=data_root,
        email="ignored@example.com",
        calls=calls,
    )

    assert result.returncode == 0, result.stderr
    assert (
        json.loads(config.read_text(encoding="utf-8"))["form_defaults"]["email"]
        == "kept@example.com"
    )
    assert job.read_text(encoding="utf-8") == "{}\n"
    assert personal_venv.read_text(encoding="utf-8") == "old\n"
    launcher = old_launcher.read_text(encoding="utf-8")
    assert fake_path(root / "bin" / "dispatch") in launcher
    assert ".dispatch/venv" not in launcher
    assert calls.read_text(encoding="utf-8") == ""
    assert not (dispatch_home / "installed_version").exists()


def test_two_users_share_launcher_runtime_but_keep_private_state(tmp_path: Path) -> None:
    if shutil.which("sh") is None:
        pytest.skip("onboarding smoke requires sh")
    root, runtime = prepare_onboarding_root(tmp_path)
    launchers = []
    for user in ("alice", "bob"):
        home = tmp_path / f"home-{user}"
        data_root = tmp_path / "ads_storage" / user
        result = run_onboarding(
            root,
            home=home,
            data_root=data_root,
            email=f"{user}@example.com",
            calls=tmp_path / f"calls-{user}",
        )
        assert result.returncode == 0, result.stderr
        launchers.append((home / ".local" / "bin" / "dispatch").read_text(encoding="utf-8"))
        assert (
            json.loads((data_root / ".dispatch" / "config.json").read_text(encoding="utf-8"))[
                "form_defaults"
            ]["email"]
            == f"{user}@example.com"
        )
        if os.name != "nt":
            assert stat.S_IMODE((data_root / ".dispatch").stat().st_mode) == 0o700

    assert launchers[0] == launchers[1]
    assert fake_path(root / "bin" / "dispatch") in launchers[0]
    assert (root / ".venv" / "current").resolve() == runtime.resolve()


def test_onboarding_fails_before_changing_state_when_runtime_is_missing(tmp_path: Path) -> None:
    if shutil.which("sh") is None:
        pytest.skip("onboarding smoke requires sh")
    root = make_install_root(tmp_path)
    shutil.copy2(ROOT / "onboard.sh", root / "onboard.sh")
    data_root = tmp_path / "ads_storage" / "alice"
    data_root.mkdir(parents=True)
    env = os.environ.copy()
    env.update({"HOME": fake_path(tmp_path / "home"), "DISPATCH_DATA_ROOT": fake_path(data_root)})

    result = subprocess.run(
        ["sh", "onboard.sh"], cwd=root, env=env, text=True, capture_output=True, check=False
    )

    assert result.returncode != 0
    assert "shared runtime is not active" in result.stderr
    assert not (data_root / ".dispatch").exists()


def test_onboarding_fails_before_changing_state_when_klist_is_missing(tmp_path: Path) -> None:
    if shutil.which("sh") is None:
        pytest.skip("onboarding smoke requires sh")
    if shutil.which("klist"):
        pytest.skip("host provides klist; cannot simulate a missing edge tool")
    root, _runtime = prepare_onboarding_root(tmp_path)
    tools = tmp_path / "impala-only"
    tools.mkdir()
    shell_tool = tools / "impala-shell"
    shell_tool.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    shell_tool.chmod(0o755)
    data_root = tmp_path / "ads_storage" / "alice"

    result = run_onboarding(
        root,
        home=tmp_path / "home",
        data_root=data_root,
        email="alice@example.com",
        calls=tmp_path / "onboard-calls",
        edge_tools=tools,
    )

    assert result.returncode != 0
    assert "klist not found on PATH" in result.stderr
    assert not (data_root / ".dispatch").exists()


def test_onboarded_user_runs_dispatch_help_through_shared_launcher(tmp_path: Path) -> None:
    if shutil.which("sh") is None:
        pytest.skip("onboarding smoke requires sh")
    root, runtime = prepare_onboarding_root(tmp_path)
    home = tmp_path / "home"
    data_root = tmp_path / "ads_storage" / "alice"
    calls = tmp_path / "onboard-calls"
    result = run_onboarding(
        root, home=home, data_root=data_root, email="alice@example.com", calls=calls
    )
    assert result.returncode == 0, result.stderr

    # Swap the runtime interpreter for one that records the launch and exits
    # cleanly, so the assertion covers the launcher chain rather than the app.
    runtime_python = runtime / "bin" / "python"
    runtime_python.write_text(
        '#!/usr/bin/env sh\nprintf \'%s\\n\' "$*" >> "${ONBOARD_CALLS:?}"\nexit 0\n',
        encoding="utf-8",
    )
    runtime_python.chmod(0o755)
    launcher = home / ".local" / "bin" / "dispatch"
    env = os.environ.copy()
    env["ONBOARD_CALLS"] = fake_path(calls)

    run = subprocess.run(
        ["sh", fake_path(launcher), "--help"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert run.returncode == 0, run.stderr
    assert "-m dispatch --help" in calls.read_text(encoding="utf-8")


def test_update_permissions_do_not_recurse_through_runtime_directories() -> None:
    update_script = (ROOT / "update.sh").read_text(encoding="utf-8")
    assert "chmod -R" not in update_script
    assert "$CHANGED_FILES" in update_script


def fake_path(path: Path) -> str:
    return path.resolve().as_posix()
