"""Installer onboarding should give users a short path to running dispatch."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_version_sources_agree() -> None:
    """Version metadata must match the edge-node deploy artifact."""

    import re

    from dispatch.version import __version__

    version_file = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert version_file == __version__

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    assert match is not None, "pyproject.toml has no version field"
    assert match.group(1) == __version__


def test_install_updates_path_instead_of_alias_only() -> None:
    install_script = (ROOT / "install.sh").read_text(encoding="utf-8")

    assert 'export PATH="$HOME/.local/bin:$PATH"' in install_script
    assert "alias dispatch=" not in install_script


def test_install_prints_current_session_next_step() -> None:
    install_script = (ROOT / "install.sh").read_text(encoding="utf-8")

    assert "To use dispatch in this shell now:" in install_script
    assert "export PATH=" in install_script


def test_update_permissions_do_not_recurse_through_runtime_directories() -> None:
    update_script = (ROOT / "update.sh").read_text(encoding="utf-8")

    assert "chmod -R" not in update_script
    assert "$CHANGED_FILES" in update_script


def test_install_fails_when_verified_bundle_is_missing(
    tmp_path: Path,
) -> None:
    if shutil.which("sh") is None:
        pytest.skip("install.sh smoke requires sh")

    install_root = tmp_path / "install-root"
    vendor = install_root / "vendor"
    home = tmp_path / "home"
    data_root = tmp_path / "ads_storage" / "testuser"
    fake_bin = tmp_path / "bin"
    vendor.mkdir(parents=True)
    home.mkdir()
    data_root.mkdir(parents=True)
    fake_bin.mkdir()
    shutil.copy2(ROOT / "install.sh", install_root / "install.sh")

    for name in ("klist", "impala-shell"):
        tool = fake_bin / name
        tool.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
        tool.chmod(0o755)

    fake_python = fake_bin / "python3.11"
    fake_python.write_text(
        """#!/usr/bin/env sh
set -eu
mkdir -p "$3/bin"
cat > "$3/bin/pip" <<'EOF'
#!/usr/bin/env sh
exit 0
EOF
chmod +x "$3/bin/pip"
""",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    env = os.environ.copy()
    env.pop("DISPATCH_ALLOW_ONLINE_PIP", None)
    env.update(
        {
            "HOME": fake_path(home),
            "USER": "testuser",
            "DISPATCH_DATA_ROOT": fake_path(data_root),
            "DISPATCH_EMAIL": "dispatch-smoke@example.com",
            "DISPATCH_PYTHON_BIN": fake_path(fake_python),
            "PATH": f"{fake_path(fake_bin)}{os.pathsep}{env['PATH']}",
        }
    )

    result = subprocess.run(
        ["sh", "install.sh"],
        cwd=install_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Verified dependency bundle not found" in result.stderr


@pytest.mark.parametrize(
    "email",
    [
        pytest.param("dispatch-smoke@example.com", id="simple"),
        pytest.param(
            'dispatch"team\\north\tline\nnext@example.com',
            id="json-special-characters",
        ),
    ],
)
def test_install_creates_runtime_artifacts_with_mocked_edge_tools(
    tmp_path: Path,
    email: str,
) -> None:
    if shutil.which("sh") is None:
        pytest.skip("install.sh smoke requires sh")

    home = tmp_path / "home"
    data_root = tmp_path / "ads_storage" / "testuser"
    fake_bin = tmp_path / "bin"
    home.mkdir()
    data_root.mkdir(parents=True)
    fake_bin.mkdir()
    stale_venv_file = data_root / ".dispatch" / "venv" / "stale-interpreter"
    stale_venv_file.parent.mkdir(parents=True)
    stale_venv_file.write_text("python3.11\n", encoding="utf-8")
    bundle = tmp_path / "bundle"
    (bundle / "wheels").mkdir(parents=True)
    (bundle / "requirements").mkdir()
    (bundle / "manifest.json").write_text("{}\n", encoding="utf-8")
    (bundle / "requirements" / "requirements.txt").write_text("demo==1.0\n", encoding="utf-8")
    (bundle / "wheels" / "demo-1.0-py3-none-any.whl").write_bytes(b"wheel")

    for name in ("klist", "impala-shell"):
        tool = fake_bin / name
        tool.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
        tool.chmod(0o755)

    fake_python = fake_bin / "python3.11"
    fake_python.write_text(
        """#!/usr/bin/env sh
set -eu
if [ "${1:-}" = "-m" ] && [ "${2:-}" = "venv" ]; then
  if [ "${3:-}" = "--clear" ]; then
    target=$4
    rm -rf "$target"
  else
    target=$3
  fi
  mkdir -p "$target/bin"
  cat > "$target/bin/pip" <<'EOF'
#!/usr/bin/env sh
exit 0
EOF
  chmod +x "$target/bin/pip"
  cat > "$target/bin/python" <<'EOF'
#!/usr/bin/env sh
if [ "${1:-}" = "-m" ] && [ "${2:-}" = "pip" ]; then
  touch "$0.pip-invoked"
fi
exit 0
EOF
  chmod +x "$target/bin/python"
  exit 0
fi
if [ "${1:-}" = "-" ]; then
  exec "__REAL_PYTHON__" "$@"
fi
exit 0
""".replace("__REAL_PYTHON__", fake_path(Path(sys.executable))),
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "EDGE_DEPLOY_BUNDLE_DIR": fake_path(bundle),
            "HOME": fake_path(home),
            "USER": "testuser",
            "DISPATCH_DATA_ROOT": fake_path(data_root),
            "DISPATCH_EMAIL": email,
            "DISPATCH_PYTHON_BIN": fake_path(fake_python),
            "PATH": f"{fake_path(fake_bin)}{os.pathsep}{env['PATH']}",
        }
    )

    result = subprocess.run(
        ["sh", "install.sh"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    dispatch_home = data_root / ".dispatch"
    assert (dispatch_home / "jobs").is_dir()
    if os.name != "nt":
        assert stat.S_IMODE(dispatch_home.stat().st_mode) == 0o700
        assert stat.S_IMODE((dispatch_home / "jobs").stat().st_mode) == 0o700
    assert (dispatch_home / "venv" / "bin" / "python").is_file()
    assert not stale_venv_file.exists()
    assert (dispatch_home / "venv" / "bin" / "python.pip-invoked").is_file()
    data = json.loads((dispatch_home / "config.json").read_text(encoding="utf-8"))
    assert data == {"form_defaults": {"email": email}}
    assert (dispatch_home / "installed_version").read_text(encoding="utf-8") == (
        ROOT / "VERSION"
    ).read_text(encoding="utf-8")
    launcher = home / ".local" / "bin" / "dispatch"
    assert launcher.is_file()
    launcher_text = launcher.read_text(encoding="utf-8")
    assert f'export PYTHONPATH="{fake_path(ROOT)}"' in launcher_text
    assert 'exec "' in launcher_text


def fake_path(path: Path) -> str:
    return path.resolve().as_posix()
