"""Installer onboarding should give users a short path to running dispatch."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_install_updates_path_instead_of_alias_only() -> None:
    install_script = (ROOT / "install.sh").read_text(encoding="utf-8")

    assert 'export PATH="$HOME/.local/bin:$PATH"' in install_script
    assert "alias dispatch=" not in install_script


def test_install_prints_current_session_next_step() -> None:
    install_script = (ROOT / "install.sh").read_text(encoding="utf-8")

    assert "To use dispatch in this shell now:" in install_script
    assert "export PATH=" in install_script


def test_install_fails_when_vendor_empty_and_no_online_opt_in(
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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode != 0
    assert "DISPATCH_ALLOW_ONLINE_PIP" in result.stderr


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

    for name in ("klist", "impala-shell"):
        tool = fake_bin / name
        tool.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
        tool.chmod(0o755)

    fake_python = fake_bin / "python3.11"
    fake_python.write_text(
        """#!/usr/bin/env sh
set -eu
if [ "${1:-}" = "-m" ] && [ "${2:-}" = "venv" ]; then
  mkdir -p "$3/bin"
  cat > "$3/bin/pip" <<'EOF'
#!/usr/bin/env sh
exit 0
EOF
  chmod +x "$3/bin/pip"
  cat > "$3/bin/python" <<'EOF'
#!/usr/bin/env sh
exit 0
EOF
  chmod +x "$3/bin/python"
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
            "DISPATCH_ALLOW_ONLINE_PIP": "1",
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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    dispatch_home = data_root / ".dispatch"
    assert (dispatch_home / "jobs").is_dir()
    assert (dispatch_home / "venv" / "bin" / "python").is_file()
    data = json.loads((dispatch_home / "config.json").read_text(encoding="utf-8"))
    assert data == {"form_defaults": {"email": email}}
    assert (dispatch_home / "installed_version").read_text(encoding="utf-8") == (
        ROOT / "VERSION"
    ).read_text(encoding="utf-8")
    launcher = home / ".local" / "bin" / "dispatch"
    assert launcher.is_file()
    launcher_text = launcher.read_text(encoding="utf-8")
    assert 'export PYTHONPATH="' in launcher_text
    assert "robocop" in launcher_text
    assert 'exec "' in launcher_text


def fake_path(path: Path) -> str:
    return path.resolve().as_posix()
