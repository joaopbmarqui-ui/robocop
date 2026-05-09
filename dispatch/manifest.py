"""Job manifest schema and helpers."""

from __future__ import annotations

import base64
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict

from . import config

SourceType = Literal["SqlFile", "SqlTemplate", "ExistingTable"]
DestinationType = Literal["Table", "Csv", "Table+Csv"]
JobState = Literal["Pending", "Running", "Succeeded", "Failed", "Cancelled"]


class Source(TypedDict, total=False):
    type: SourceType
    sql_path_at_launch: str
    table_name: str


class Destination(TypedDict, total=False):
    type: DestinationType
    schema: str
    table_name: str
    csv_path: str


class OrchestratorCall(TypedDict):
    script: str
    argv: list[str]


class JobManifest(TypedDict):
    schema_version: int
    id: str
    tool: str
    user: str
    source: Source
    destination: Destination
    params: dict[str, Any]
    orchestrator_calls: list[OrchestratorCall]
    state: JobState
    pid: int | None
    started_at: str | None
    finished_at: str | None
    exit_code: int | None


LEGAL_CELLS: set[tuple[SourceType, DestinationType]] = {
    ("SqlFile", "Table"),
    ("SqlFile", "Csv"),
    ("SqlFile", "Table+Csv"),
    ("SqlTemplate", "Table"),
    ("ExistingTable", "Csv"),
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_job_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    token = base64.b32encode(os.urandom(5)).decode("ascii").lower()[:6]
    return f"{timestamp}_{token}"


def load(path: Path) -> JobManifest:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    validate(data)
    return data


def write(path: Path, manifest: JobManifest) -> None:
    validate(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    tmp.replace(path)


def update(path: Path, **changes: Any) -> JobManifest:
    manifest = load(path)
    manifest.update(changes)
    write(path, manifest)
    return manifest


def validate(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    required = {
        "schema_version",
        "id",
        "tool",
        "user",
        "source",
        "destination",
        "params",
        "orchestrator_calls",
        "state",
        "pid",
        "started_at",
        "finished_at",
        "exit_code",
    }
    missing = required - set(data)
    if missing:
        raise ValueError(f"manifest missing keys: {sorted(missing)}")
    if data["schema_version"] != 1:
        raise ValueError("unsupported manifest schema_version")
    if data["tool"] != "dispatch":
        raise ValueError("manifest tool must be dispatch")
    source_type = data["source"].get("type")
    destination_type = data["destination"].get("type")
    if (source_type, destination_type) not in LEGAL_CELLS:
        raise ValueError(f"illegal Source/Destination cell: {source_type}/{destination_type}")
    if data["state"] not in {"Pending", "Running", "Succeeded", "Failed", "Cancelled"}:
        raise ValueError("invalid Job state")
    if not isinstance(data["orchestrator_calls"], list) or not data["orchestrator_calls"]:
        raise ValueError("manifest requires at least one orchestrator call")


def create_job(
    source: Source,
    destination: Destination,
    params: dict[str, Any],
    launch_cwd: Path,
    sql_text: str = "",
    user: str | None = None,
) -> tuple[Path, JobManifest]:
    job_user = user or config.current_user()
    job_id = new_job_id()
    job_dir = config.jobs_dir(job_user) / job_id
    job_dir.mkdir(parents=True)
    (job_dir / "job.sql").write_text(sql_text, encoding="utf-8")
    manifest: JobManifest = {
        "schema_version": 1,
        "id": job_id,
        "tool": "dispatch",
        "user": job_user,
        "source": source,
        "destination": destination,
        "params": params,
        "orchestrator_calls": build_orchestrator_calls(job_dir, source, destination, params, launch_cwd, job_user),
        "state": "Pending",
        "pid": None,
        "started_at": None,
        "finished_at": None,
        "exit_code": None,
    }
    write(job_dir / "manifest.json", manifest)
    return job_dir, manifest


def script_argv(script: str) -> list[str]:
    scr_dir = Path(os.environ.get("DISPATCH_SCR_DIR", "/ads_storage/dispatch/scr"))
    script_path = scr_dir / script
    if script_path.exists() and os.access(script_path, os.X_OK):
        return [str(script_path)]
    python = shutil.which("python3.10") or shutil.which("python3") or sys.executable
    return [python, str(script_path)]


def build_orchestrator_calls(
    job_dir: Path,
    source: Source,
    destination: Destination,
    params: dict[str, Any],
    launch_cwd: Path,
    user: str,
) -> list[OrchestratorCall]:
    source_type = source["type"]
    destination_type = destination["type"]
    if (source_type, destination_type) not in LEGAL_CELLS:
        raise ValueError(f"illegal Source/Destination cell: {source_type}/{destination_type}")

    schema = destination.get("schema", "")
    table = destination.get("table_name", "")
    full_table = f"{schema}.{table}" if schema and "." not in table else table
    csv_path = destination.get("csv_path") or str(launch_cwd / f"{table or 'dispatch_export'}.csv")
    email = str(params.get("to_email", ""))
    subject = str(params.get("subject", "Dispatch Job"))
    calls: list[OrchestratorCall] = []

    if source_type == "SqlFile" and destination_type in {"Table", "Table+Csv"}:
        argv = script_argv("Query_Impala_Parametrized.py") + [
            "--sql-file",
            str(job_dir / "job.sql"),
            "--table-name",
            full_table,
            "--to-email",
            email,
            "--subject",
            subject,
            "--user",
            user,
            "--session-folder",
            str(job_dir),
        ]
        calls.append({"script": "Query_Impala_Parametrized.py", "argv": argv})

    if source_type == "SqlFile" and destination_type == "Csv":
        argv = script_argv("download_to_csv.py") + [
            "--query-file",
            str(job_dir / "job.sql"),
            "--output-file",
            csv_path,
        ]
        calls.append({"script": "download_to_csv.py", "argv": argv})

    if source_type == "SqlFile" and destination_type == "Table+Csv":
        argv = script_argv("download_to_csv.py") + [
            "--table-name",
            full_table,
            "--output-file",
            csv_path,
        ]
        calls.append({"script": "download_to_csv.py", "argv": argv})

    if source_type == "SqlTemplate":
        argv = script_argv("monthly_query_processor.py") + [
            "--sql-file",
            str(job_dir / "job.sql"),
            "--schema",
            schema,
            "--table-name",
            table,
            "--start-date",
            str(params["start_date"]),
            "--end-date",
            str(params["end_date"]),
            "--user",
            user,
            "--to-email",
            email,
            "--subject",
            subject,
        ]
        calls.append({"script": "monthly_query_processor.py", "argv": argv})

    if source_type == "ExistingTable":
        argv = script_argv("download_to_csv.py") + [
            "--table-name",
            full_table,
            "--output-file",
            csv_path,
        ]
        calls.append({"script": "download_to_csv.py", "argv": argv})

    destination["csv_path"] = csv_path
    return calls
