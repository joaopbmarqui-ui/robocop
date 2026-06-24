"""Local network preflight for the production TUI harness."""
from __future__ import annotations

import argparse
import json
import shlex
import socket
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from tools.prod_tui.robocop_tmux import DEFAULT_CONFIG_PATH, ProdTuiConfig, load_config


@dataclass(frozen=True)
class EdgeEndpoint:
    """Resolved SSH endpoint extracted from the harness config."""

    user_host: str
    hostname: str
    port: int


@dataclass(frozen=True)
class TcpPreflightResult:
    """Outcome of one local TCP preflight."""

    endpoint: EdgeEndpoint
    resolved_addresses: tuple[str, ...]
    connected: bool
    error: str = ""


SocketConnector = Callable[[tuple[str, int], float], object]


def endpoint_from_config(config: ProdTuiConfig) -> EdgeEndpoint:
    """Return the SSH hostname and port selected by the production config."""

    hostname = config.host.rsplit("@", 1)[-1]
    port = 22
    option_parts = shlex.split(config.ssh_options)
    for index, part in enumerate(option_parts):
        if part == "-p" and index + 1 < len(option_parts):
            port = int(option_parts[index + 1])
        elif part.startswith("-p") and len(part) > 2:
            port = int(part[2:])
        elif part.startswith("Port="):
            port = int(part.split("=", 1)[1])
    return EdgeEndpoint(user_host=config.host, hostname=hostname, port=port)


def run_tcp_preflight(
    config: ProdTuiConfig,
    *,
    timeout: float | None = None,
    connector: SocketConnector | None = None,
) -> TcpPreflightResult:
    endpoint = endpoint_from_config(config)
    effective_timeout = float(timeout if timeout is not None else config.ssh_connect_timeout)
    try:
        infos = socket.getaddrinfo(endpoint.hostname, endpoint.port, type=socket.SOCK_STREAM)
        addresses = tuple(dict.fromkeys(info[4][0] for info in infos))
    except OSError as exc:
        return TcpPreflightResult(endpoint, (), False, f"DNS lookup failed: {exc}")

    try:
        active_connector = connector or socket.create_connection
        connection = active_connector((endpoint.hostname, endpoint.port), effective_timeout)
    except TimeoutError as exc:
        return TcpPreflightResult(endpoint, addresses, False, str(exc) or "timed out")
    except OSError as exc:
        return TcpPreflightResult(endpoint, addresses, False, str(exc) or "connection failed")

    close = getattr(connection, "close", None)
    if callable(close):
        close()
    return TcpPreflightResult(endpoint, addresses, True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check DNS and TCP reachability before starting the Edge TUI harness."
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to production TUI config.yaml")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="TCP connect timeout in seconds; defaults to ssh_connect_timeout from the config",
    )
    parser.add_argument(
        "--json-report",
        default=None,
        help="Optional path to write a machine-readable preflight report",
    )
    return parser


def _write_json_report(path: str | Path, *, config_path: str, result: TcpPreflightResult) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": config_path,
        "host": result.endpoint.user_host,
        "endpoint": f"{result.endpoint.hostname}:{result.endpoint.port}",
        "resolved_addresses": list(result.resolved_addresses),
        "connected": result.connected,
        "error": result.error,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    config = load_config(args.config)
    result = run_tcp_preflight(config, timeout=args.timeout)
    addresses = ", ".join(result.resolved_addresses) if result.resolved_addresses else "(none)"

    print(f"Config: {args.config}")
    print(f"Host: {result.endpoint.user_host}")
    print(f"Endpoint: {result.endpoint.hostname}:{result.endpoint.port}")
    print(f"Resolved addresses: {addresses}")
    if args.json_report:
        _write_json_report(args.json_report, config_path=args.config, result=result)
        print(f"JSON report: {args.json_report}")
    if result.connected:
        print("TCP preflight: PASS")
        return 0

    print(f"TCP preflight: FAIL - {result.error}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
