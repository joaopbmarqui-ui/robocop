"""Shared runtime and launcher contracts."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import threading
from pathlib import Path

import pytest
from bundle_helpers import make_bundle

import shared_runtime

ROOT = Path(__file__).resolve().parents[1]


def completion_metadata(digest: str) -> dict[str, object]:
    return {
        "bundle_digest": digest,
        "pip_check": "passed",
        "required_imports": ["textual", "sqlglot"],
    }


def copy_launcher(root: Path) -> Path:
    launcher = root / "bin" / "dispatch"
    launcher.parent.mkdir(parents=True, exist_ok=True)
    for name in ("dispatch", "runtime_check.sh"):
        shutil.copy2(ROOT / "bin" / name, root / "bin" / name)
    launcher.chmod(0o755)
    return launcher


def test_manifest_digest_drives_release_path_and_completed_reuse(tmp_path: Path) -> None:
    bundle, digest = make_bundle(tmp_path)
    _manifest, loaded_digest = shared_runtime._load_manifest(bundle)
    runtime = tmp_path / ".venv" / "releases" / digest
    (runtime / "bin").mkdir(parents=True)
    (runtime / "bin" / "python").write_text("", encoding="utf-8")
    (runtime / shared_runtime.COMPLETE_MARKER).write_text(
        json.dumps(completion_metadata(digest)), encoding="utf-8"
    )

    assert loaded_digest == digest
    assert shared_runtime._complete_metadata(runtime, digest) == completion_metadata(digest)


@pytest.mark.parametrize("unsafe_path", ["../escape", "/absolute", "other/file.txt"])
def test_manifest_rejects_unsafe_paths(tmp_path: Path, unsafe_path: str) -> None:
    bundle, _digest = make_bundle(tmp_path)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["path"] = unsafe_path
    identity = {key: value for key, value in manifest.items() if key != "bundle_digest"}
    canonical = (json.dumps(identity, sort_keys=True, separators=(",", ":")) + "\n").encode()
    manifest["bundle_digest"] = hashlib.sha256(canonical).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(shared_runtime.RuntimeInstallError, match="unsafe path"):
        shared_runtime._load_manifest(bundle)


def test_manifest_rejects_tampered_bundle_file(tmp_path: Path) -> None:
    bundle, _digest = make_bundle(tmp_path)
    (bundle / "requirements" / "requirements.txt").write_text("changed\n", encoding="utf-8")

    with pytest.raises(shared_runtime.RuntimeInstallError, match="failed verification"):
        shared_runtime._load_manifest(bundle)


def test_manifest_rejects_undeclared_extra_file(tmp_path: Path) -> None:
    bundle, _digest = make_bundle(tmp_path)
    (bundle / "wheels" / "smuggled.whl").write_bytes(b"undeclared")

    with pytest.raises(shared_runtime.RuntimeInstallError, match="do not match the manifest"):
        shared_runtime._load_manifest(bundle)


def test_manifest_rejects_malformed_digest(tmp_path: Path) -> None:
    bundle, _digest = make_bundle(tmp_path)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["bundle_digest"] = "not-a-digest"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(shared_runtime.RuntimeInstallError, match="invalid bundle_digest"):
        shared_runtime._load_manifest(bundle)


def test_manifest_requires_verified_bundle_layout(tmp_path: Path) -> None:
    with pytest.raises(shared_runtime.RuntimeInstallError, match="bundle is incomplete"):
        shared_runtime._load_manifest(tmp_path / "missing")


def test_shared_launcher_forwards_arguments_and_preserves_cwd(tmp_path: Path) -> None:
    if shutil.which("sh") is None:
        pytest.skip("shared launcher smoke requires sh")
    root = tmp_path / "dispatch-root"
    launcher = copy_launcher(root)
    runtime = root / ".venv" / "releases" / ("a" * 64)
    (runtime / "bin").mkdir(parents=True)
    (runtime / shared_runtime.COMPLETE_MARKER).write_text(
        json.dumps(completion_metadata(runtime.name)), encoding="utf-8"
    )
    capture = tmp_path / "capture.txt"
    fake_python = runtime / "bin" / "python"
    fake_python.write_text(
        "#!/usr/bin/env sh\n"
        'printf \'%s\\n\' "$PWD" "$PYTHONPATH" "$DISPATCH_SCR_DIR" "$DISPATCH_RUNTIME" "$@" > "$CAPTURE"\n',
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    current = root / ".venv" / "current"
    try:
        current.symlink_to(Path("releases") / runtime.name, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    launch_cwd = tmp_path / "sql"
    launch_cwd.mkdir()
    env = os.environ.copy()
    env["CAPTURE"] = capture.resolve().as_posix()

    result = subprocess.run(
        ["sh", launcher.resolve().as_posix(), "--help", "two words"],
        cwd=launch_cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    lines = capture.read_text(encoding="utf-8").splitlines()
    assert lines[0] == shell_path(launch_cwd)
    assert lines[1] == shell_path(root)
    assert lines[2] == shell_path(root / "scr")
    assert lines[3] == shell_path(runtime)
    assert lines[4:] == ["-m", "dispatch", "--help", "two words"]


def shell_path(path: Path) -> str:
    resolved = path.resolve()
    if os.name != "nt":
        return resolved.as_posix()
    return subprocess.check_output(["cygpath", "-u", str(resolved)], text=True).strip()


def test_shared_launcher_fails_clearly_without_active_runtime(tmp_path: Path) -> None:
    if shutil.which("sh") is None:
        pytest.skip("shared launcher smoke requires sh")
    root = tmp_path / "dispatch-root"
    launcher = copy_launcher(root)

    result = subprocess.run(
        ["sh", launcher.resolve().as_posix()],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "shared runtime is not active" in result.stderr


def test_shared_launcher_rejects_corrupt_completion_metadata(tmp_path: Path) -> None:
    if shutil.which("sh") is None:
        pytest.skip("shared launcher smoke requires sh")
    root = tmp_path / "dispatch-root"
    launcher = copy_launcher(root)
    runtime = root / ".venv" / "releases" / ("c" * 64)
    (runtime / "bin").mkdir(parents=True)
    (runtime / "bin" / "python").write_text("", encoding="utf-8")
    (runtime / shared_runtime.COMPLETE_MARKER).write_text("{}\n", encoding="utf-8")
    try:
        (root / ".venv" / "current").symlink_to(
            Path("releases") / runtime.name, target_is_directory=True
        )
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    result = subprocess.run(
        ["sh", launcher.resolve().as_posix()],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "completion metadata is corrupt" in result.stderr


def test_shared_launcher_rejects_runtime_outside_release_root(tmp_path: Path) -> None:
    if shutil.which("sh") is None:
        pytest.skip("shared launcher smoke requires sh")
    root = tmp_path / "dispatch-root"
    launcher = copy_launcher(root)
    rogue = tmp_path / "rogue-runtime"
    (rogue / "bin").mkdir(parents=True)
    (rogue / "bin" / "python").write_text("", encoding="utf-8")
    (rogue / "bin" / "python").chmod(0o755)
    (rogue / shared_runtime.COMPLETE_MARKER).write_text(
        json.dumps(completion_metadata(rogue.name)), encoding="utf-8"
    )
    (root / ".venv").mkdir(parents=True)
    try:
        (root / ".venv" / "current").symlink_to(rogue, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    result = subprocess.run(
        ["sh", launcher.resolve().as_posix()],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "resolves outside the release root" in result.stderr


def fake_completed_build(
    runtime: Path, _bundle: Path, digest: str, _python: Path, _target: str | None
) -> None:
    (runtime / "bin").mkdir(parents=True)
    (runtime / "bin" / "python").write_text("", encoding="utf-8")
    (runtime / shared_runtime.COMPLETE_MARKER).write_text(
        json.dumps(completion_metadata(digest)), encoding="utf-8"
    )


def test_activation_reuse_switch_and_rollback(tmp_path: Path, monkeypatch) -> None:
    if os.name == "nt":
        pytest.skip("activation symlinks are validated on Linux")
    root = tmp_path / "root"
    first_bundle, first_digest = make_bundle(
        tmp_path, {"requirements/requirements.txt": b"first\n"}
    )
    second_bundle, second_digest = make_bundle(
        tmp_path, {"requirements/requirements.txt": b"second\n"}
    )
    monkeypatch.setattr(shared_runtime, "_build_runtime", fake_completed_build)

    digest, reused = shared_runtime.install(first_bundle, Path("/python"), root)
    assert (digest, reused) == (first_digest, False)
    assert (root / ".venv" / "current").resolve().name == first_digest

    digest, reused = shared_runtime.install(first_bundle, Path("/python"), root)
    assert (digest, reused) == (first_digest, True)

    digest, reused = shared_runtime.install(second_bundle, Path("/python"), root)
    assert (digest, reused) == (second_digest, False)
    assert (root / ".venv" / "current").resolve().name == second_digest

    digest, reused = shared_runtime.install(first_bundle, Path("/python"), root)
    assert (digest, reused) == (first_digest, True)
    assert (root / ".venv" / "current").resolve().name == first_digest


def test_failed_candidate_does_not_change_current(tmp_path: Path, monkeypatch) -> None:
    if os.name == "nt":
        pytest.skip("activation symlinks are validated on Linux")
    root = tmp_path / "root"
    first_bundle, first_digest = make_bundle(
        tmp_path, {"requirements/requirements.txt": b"first\n"}
    )
    second_bundle, _second_digest = make_bundle(
        tmp_path, {"requirements/requirements.txt": b"second\n"}
    )
    monkeypatch.setattr(shared_runtime, "_build_runtime", fake_completed_build)
    shared_runtime.install(first_bundle, Path("/python"), root)

    def fail_build(runtime: Path, *_args) -> None:
        runtime.mkdir(parents=True)
        (runtime / "partial").write_text("incomplete", encoding="utf-8")
        raise shared_runtime.RuntimeInstallError("simulated failure")

    monkeypatch.setattr(shared_runtime, "_build_runtime", fail_build)
    with pytest.raises(shared_runtime.RuntimeInstallError, match="simulated"):
        shared_runtime.install(second_bundle, Path("/python"), root)

    assert (root / ".venv" / "current").resolve().name == first_digest
    assert not (root / ".venv" / "releases" / _second_digest).exists()


def test_reinstall_of_active_digest_with_corrupt_marker_preserves_runtime(
    tmp_path: Path, monkeypatch
) -> None:
    if os.name == "nt":
        pytest.skip("activation symlinks are validated on Linux")
    root = tmp_path / "root"
    bundle, digest = make_bundle(tmp_path)
    monkeypatch.setattr(shared_runtime, "_build_runtime", fake_completed_build)
    shared_runtime.install(bundle, Path("/python"), root)
    runtime = root / ".venv" / "releases" / digest
    (runtime / shared_runtime.COMPLETE_MARKER).write_text("{}\n", encoding="utf-8")

    def destructive_build(runtime: Path, *_args) -> None:
        raise AssertionError("the active runtime must never be rebuilt in place")

    monkeypatch.setattr(shared_runtime, "_build_runtime", destructive_build)
    with pytest.raises(shared_runtime.RuntimeInstallError, match="rebuilt in place"):
        shared_runtime.install(bundle, Path("/python"), root)

    assert (runtime / "bin" / "python").exists()
    assert (root / ".venv" / "current").resolve() == runtime.resolve()


def test_incomplete_inactive_runtime_is_rebuilt_on_retry(tmp_path: Path, monkeypatch) -> None:
    if os.name == "nt":
        pytest.skip("activation symlinks are validated on Linux")
    root = tmp_path / "root"
    bundle, digest = make_bundle(tmp_path)
    partial = root / ".venv" / "releases" / digest
    partial.mkdir(parents=True)
    (partial / "partial").write_text("incomplete", encoding="utf-8")

    def rebuild(runtime: Path, *args) -> None:
        # Mirror the real builder's contract: an incomplete directory is
        # cleared and rebuilt from scratch.
        if runtime.exists():
            shutil.rmtree(runtime)
        fake_completed_build(runtime, *args)

    monkeypatch.setattr(shared_runtime, "_build_runtime", rebuild)

    installed_digest, reused = shared_runtime.install(bundle, Path("/python"), root)

    assert (installed_digest, reused) == (digest, False)
    assert (root / ".venv" / "current").resolve() == partial.resolve()
    assert not (partial / "partial").exists()


def test_activation_cleans_stale_temporary_symlinks(tmp_path: Path, monkeypatch) -> None:
    if os.name == "nt":
        pytest.skip("activation symlinks are validated on Linux")
    root = tmp_path / "root"
    bundle, _digest = make_bundle(tmp_path)
    runtime_root = root / ".venv"
    runtime_root.mkdir(parents=True)
    stale = runtime_root / ".current.tmp.99999999"
    stale.symlink_to(Path("releases") / ("d" * 64), target_is_directory=True)
    monkeypatch.setattr(shared_runtime, "_build_runtime", fake_completed_build)

    shared_runtime.install(bundle, Path("/python"), root)

    assert not list(runtime_root.glob(".current.tmp.*"))


def test_release_directories_are_traversable_under_restrictive_umask(
    tmp_path: Path, monkeypatch
) -> None:
    if os.name == "nt":
        pytest.skip("POSIX mode contract is validated on Linux")
    root = tmp_path / "root"
    bundle, _digest = make_bundle(tmp_path)
    monkeypatch.setattr(shared_runtime, "_build_runtime", fake_completed_build)
    previous_umask = os.umask(0o077)
    try:
        shared_runtime.install(bundle, Path("/python"), root)
    finally:
        os.umask(previous_umask)

    assert stat.S_IMODE((root / ".venv").stat().st_mode) == 0o755
    assert stat.S_IMODE((root / ".venv" / "releases").stat().st_mode) == 0o755


def test_install_lock_excludes_concurrent_installer(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("flock concurrency contract is validated on Linux")
    lock_path = tmp_path / "install.lock"
    first_acquired = threading.Event()
    release_first = threading.Event()
    second_attempted = threading.Event()
    second_acquired = threading.Event()

    def first() -> None:
        with shared_runtime._install_lock(lock_path):
            first_acquired.set()
            release_first.wait(timeout=5)

    def second() -> None:
        first_acquired.wait(timeout=5)
        second_attempted.set()
        with shared_runtime._install_lock(lock_path):
            second_acquired.set()

    first_thread = threading.Thread(target=first)
    second_thread = threading.Thread(target=second)
    first_thread.start()
    second_thread.start()
    assert second_attempted.wait(timeout=5)
    assert not second_acquired.is_set()
    release_first.set()
    first_thread.join(timeout=5)
    second_thread.join(timeout=5)
    assert second_acquired.is_set()


def test_completed_runtime_permissions_are_not_publicly_writable(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("POSIX mode contract is validated on Linux")
    runtime = tmp_path / "runtime"
    package = runtime / "lib" / "package.py"
    executable = runtime / "bin" / "python"
    package.parent.mkdir(parents=True)
    executable.parent.mkdir(parents=True)
    package.write_text("", encoding="utf-8")
    executable.write_text("", encoding="utf-8")
    executable.chmod(0o755)
    approved_python = tmp_path / "approved-python"
    approved_python.write_text("", encoding="utf-8")
    approved_python.chmod(0o755)
    interpreter_link = runtime / "bin" / "python3"
    interpreter_link.symlink_to(approved_python)

    shared_runtime._make_owner_writable_only(runtime)

    assert runtime.stat().st_mode & 0o022 == 0
    assert package.stat().st_mode & 0o022 == 0
    assert package.stat().st_mode & 0o044 == 0o044
    assert executable.stat().st_mode & 0o055 == 0o055
    assert stat.S_IMODE(approved_python.stat().st_mode) == 0o755
