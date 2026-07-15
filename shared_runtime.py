"""Build and activate immutable, content-addressed Dispatch runtimes.

This module is an installer implementation detail. It intentionally uses only
the Python standard library so it can run before Dispatch dependencies exist.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path, PurePosixPath

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_IMPORTS = ("textual", "sqlglot")
COMPLETE_MARKER = ".complete.json"


class RuntimeInstallError(RuntimeError):
    """An expected shared-runtime validation or construction failure."""


def _load_manifest(bundle_dir: Path) -> tuple[dict[str, object], str]:
    manifest_path = bundle_dir / "manifest.json"
    requirements = bundle_dir / "requirements" / "requirements.txt"
    wheels = bundle_dir / "wheels"
    if not manifest_path.is_file() or not requirements.is_file() or not wheels.is_dir():
        raise RuntimeInstallError(f"Verified dependency bundle is incomplete: {bundle_dir}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeInstallError(f"Invalid dependency bundle manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise RuntimeInstallError("Dependency bundle manifest must be a JSON object")
    if manifest.get("schema") != "edge-deploy/dependency-bundle/1":
        raise RuntimeInstallError("Dependency bundle manifest has an unsupported schema")
    if manifest.get("tool") != "robocop":
        raise RuntimeInstallError("Dependency bundle manifest is for a different tool")
    digest = manifest.get("bundle_digest")
    if not isinstance(digest, str) or DIGEST_RE.fullmatch(digest) is None:
        raise RuntimeInstallError("Dependency bundle manifest has an invalid bundle_digest")
    identity = {key: value for key, value in manifest.items() if key != "bundle_digest"}
    canonical = (json.dumps(identity, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if hashlib.sha256(canonical).hexdigest() != digest:
        raise RuntimeInstallError("Dependency bundle manifest digest does not match its contents")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise RuntimeInstallError("Dependency bundle manifest has no files")
    declared: set[Path] = set()
    for item in files:
        if not isinstance(item, dict):
            raise RuntimeInstallError("Dependency bundle manifest has an invalid file entry")
        raw_path = item.get("path")
        expected_hash = item.get("sha256")
        expected_size = item.get("size")
        if not isinstance(raw_path, str):
            raise RuntimeInstallError("Dependency bundle file path must be a string")
        relative = PurePosixPath(raw_path)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not relative.parts
            or relative.parts[0] not in {"requirements", "wheels"}
        ):
            raise RuntimeInstallError(f"Dependency bundle contains an unsafe path: {raw_path}")
        if not isinstance(expected_hash, str) or DIGEST_RE.fullmatch(expected_hash) is None:
            raise RuntimeInstallError(f"Dependency bundle has an invalid hash for {raw_path}")
        if not isinstance(expected_size, int) or expected_size < 0:
            raise RuntimeInstallError(f"Dependency bundle has an invalid size for {raw_path}")
        path = bundle_dir.joinpath(*relative.parts)
        if path.is_symlink() or path.resolve() in declared:
            raise RuntimeInstallError(
                f"Dependency bundle has a duplicate or linked path: {raw_path}"
            )
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise RuntimeInstallError(f"Dependency bundle file is missing: {raw_path}") from exc
        if len(content) != expected_size or hashlib.sha256(content).hexdigest() != expected_hash:
            raise RuntimeInstallError(f"Dependency bundle file failed verification: {raw_path}")
        declared.add(path.resolve())
    actual = {
        path.resolve()
        for directory in (bundle_dir / "requirements", bundle_dir / "wheels")
        for path in directory.rglob("*")
        if path.is_file()
    }
    if actual != declared:
        raise RuntimeInstallError("Dependency bundle contents do not match the manifest")
    return manifest, digest


def _complete_metadata(runtime: Path, digest: str) -> dict[str, object] | None:
    marker = runtime / COMPLETE_MARKER
    try:
        metadata = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if (
        not isinstance(metadata, dict)
        or metadata.get("bundle_digest") != digest
        or metadata.get("pip_check") != "passed"
        or metadata.get("required_imports") != list(REQUIRED_IMPORTS)
    ):
        return None
    if not (runtime / "bin" / "python").is_file():
        return None
    return metadata


@contextlib.contextmanager
def _install_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        try:
            if os.name == "nt":
                import msvcrt

                lock_file.seek(0)
                if lock_file.read(1) == "":
                    lock_file.write("0")
                    lock_file.flush()
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        except OSError as exc:
            raise RuntimeInstallError(
                f"Could not acquire runtime installation lock: {exc}"
            ) from exc
        try:
            yield
        finally:
            if os.name == "nt":
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _run(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeInstallError(
            f"Shared runtime command failed with exit code {exc.returncode}: {' '.join(command)}"
        ) from exc


def _write_metadata(runtime: Path, digest: str, approved_python: Path) -> None:
    runtime_python = runtime / "bin" / "python"
    version = subprocess.run(
        [str(runtime_python), "-c", "import platform; print(platform.python_version())"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    metadata = {
        "bundle_digest": digest,
        "approved_python": str(approved_python.resolve()),
        "runtime_python": str(runtime_python.resolve()),
        "python_version": version,
        "pip_check": "passed",
        "required_imports": list(REQUIRED_IMPORTS),
    }
    marker = runtime / COMPLETE_MARKER
    temporary = marker.with_name(f"{marker.name}.tmp.{os.getpid()}")
    temporary.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, marker)


def _make_owner_writable_only(runtime: Path) -> None:
    for path in [runtime, *runtime.rglob("*")]:
        # Virtual environments commonly symlink their interpreter to the
        # approved system Python. chmod follows symlinks, so changing one here
        # could mutate that interpreter outside the runtime boundary.
        if path.is_symlink():
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.is_dir():
            readable = (
                mode
                | stat.S_IRUSR
                | stat.S_IWUSR
                | stat.S_IXUSR
                | stat.S_IRGRP
                | stat.S_IXGRP
                | stat.S_IROTH
                | stat.S_IXOTH
            )
            path.chmod(readable & ~(stat.S_IWGRP | stat.S_IWOTH))
        else:
            path.chmod(
                (mode | stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                & ~(stat.S_IWGRP | stat.S_IWOTH)
            )


def _build_runtime(runtime: Path, bundle_dir: Path, digest: str, approved_python: Path) -> None:
    if runtime.exists():
        shutil.rmtree(runtime)
    runtime.parent.mkdir(parents=True, exist_ok=True)
    _run([str(approved_python), "-m", "venv", str(runtime)])
    runtime_python = runtime / "bin" / "python"
    _run(
        [
            str(runtime_python),
            "-m",
            "pip",
            "install",
            "--no-index",
            f"--find-links={bundle_dir / 'wheels'}",
            "-r",
            str(bundle_dir / "requirements" / "requirements.txt"),
        ]
    )
    _run([str(runtime_python), "-m", "pip", "check"])
    _run([str(runtime_python), "-c", "; ".join(f"import {name}" for name in REQUIRED_IMPORTS)])
    _write_metadata(runtime, digest, approved_python)
    _make_owner_writable_only(runtime)


def _activate(runtime_root: Path, runtime: Path) -> None:
    current = runtime_root / "current"
    temporary = runtime_root / f".current.tmp.{os.getpid()}"
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(Path("releases") / runtime.name, target_is_directory=True)
    os.replace(temporary, current)


def install(bundle_dir: Path, approved_python: Path, root: Path) -> tuple[str, bool]:
    _manifest, digest = _load_manifest(bundle_dir)
    runtime_root = root / ".venv"
    runtime = runtime_root / "releases" / digest
    runtime_root.mkdir(parents=True, exist_ok=True)
    runtime_root.chmod(0o755)
    with _install_lock(runtime_root / "install.lock"):
        reused = _complete_metadata(runtime, digest) is not None
        if not reused:
            try:
                _build_runtime(runtime, bundle_dir, digest, approved_python)
            except Exception:
                shutil.rmtree(runtime, ignore_errors=True)
                raise
        _activate(runtime_root, runtime)
        (runtime_root / "install.lock").chmod(0o600)
    return digest, reused


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        digest, reused = install(args.bundle, args.python, args.root.resolve())
    except (OSError, RuntimeInstallError, subprocess.SubprocessError) as exc:
        print(f"Shared runtime installation failed: {exc}", file=sys.stderr)
        return 1
    action = "reused" if reused else "created"
    print(f"Shared Dispatch runtime {action} and activated: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
