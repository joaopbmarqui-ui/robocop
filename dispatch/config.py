"""Configuration and data-root helpers for Dispatch."""

import getpass
import json
import os
from pathlib import Path
from typing import Any


def current_user() -> str:
    return os.environ.get("USER") or getpass.getuser()


def data_root(user: str | None = None) -> Path:
    override = os.environ.get("DISPATCH_DATA_ROOT")
    if override:
        return Path(override)
    return Path("/ads_storage") / (user or current_user())


def dispatch_home(user: str | None = None) -> Path:
    return data_root(user) / ".dispatch"


def jobs_dir(user: str | None = None) -> Path:
    return dispatch_home(user) / "jobs"


def config_path(user: str | None = None) -> Path:
    return dispatch_home(user) / "config.json"


def installed_version_path(user: str | None = None) -> Path:
    return dispatch_home(user) / "installed_version"


def read_config(user: str | None = None) -> dict[str, Any]:
    path = config_path(user)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_config(config: dict[str, Any], user: str | None = None) -> None:
    path = config_path(user)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, sort_keys=True)
        handle.write("\n")
