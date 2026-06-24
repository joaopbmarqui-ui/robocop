from __future__ import annotations

import json
import socket
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.prod_tui import preflight
from tools.prod_tui.robocop_tmux import ProdTuiConfig


def test_endpoint_from_config_extracts_host_and_ssh_port() -> None:
    config = ProdTuiConfig(
        host="user@hde2stl020003.mastercard.int",
        repo_path="/ads_storage/dispatch",
        ssh_options="-p 2222 -o StrictHostKeyChecking=no",
    )

    endpoint = preflight.endpoint_from_config(config)

    assert endpoint.user_host == "user@hde2stl020003.mastercard.int"
    assert endpoint.hostname == "hde2stl020003.mastercard.int"
    assert endpoint.port == 2222


def test_tcp_preflight_reports_dns_and_success_without_real_network(monkeypatch) -> None:
    config = ProdTuiConfig(host="user@edge.example", repo_path="/repo", ssh_options="-p 2222")
    connections: list[tuple[tuple[str, int], float]] = []

    def fake_getaddrinfo(host: str, port: int, *, type: int):  # noqa: A002, ANN001, ANN202
        assert type == socket.SOCK_STREAM
        assert (host, port) == ("edge.example", 2222)
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.5", port))]

    def fake_connector(address: tuple[str, int], timeout: float) -> SimpleNamespace:
        connections.append((address, timeout))
        return SimpleNamespace(close=lambda: None)

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    result = preflight.run_tcp_preflight(config, timeout=3, connector=fake_connector)

    assert result.connected is True
    assert result.resolved_addresses == ("10.0.0.5",)
    assert connections == [(("edge.example", 2222), 3.0)]


def test_tcp_preflight_reports_timeout_without_traceback(monkeypatch) -> None:
    config = ProdTuiConfig(host="user@edge.example", repo_path="/repo", ssh_options="-p 2222")

    def fake_getaddrinfo(host: str, port: int, *, type: int):  # noqa: A002, ANN001, ANN202
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.5", port))]

    def fake_connector(address: tuple[str, int], timeout: float) -> object:
        raise TimeoutError("timed out")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    result = preflight.run_tcp_preflight(config, timeout=3, connector=fake_connector)

    assert result.connected is False
    assert result.error == "timed out"
    assert result.resolved_addresses == ("10.0.0.5",)


def test_tcp_preflight_reports_blank_timeout_as_timed_out(monkeypatch) -> None:
    config = ProdTuiConfig(host="user@edge.example", repo_path="/repo", ssh_options="-p 2222")

    def fake_getaddrinfo(host: str, port: int, *, type: int):  # noqa: A002, ANN001, ANN202
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.5", port))]

    def fake_connector(address: tuple[str, int], timeout: float) -> object:
        raise TimeoutError()

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    result = preflight.run_tcp_preflight(config, timeout=3, connector=fake_connector)

    assert result.connected is False
    assert result.error == "timed out"
    assert result.resolved_addresses == ("10.0.0.5",)


def test_preflight_cli_loads_config_and_returns_failure_without_real_network(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        'host: "user@edge.example"\nrepo_path: "/repo"\nssh_options: "-p 2222"\n',
        encoding="utf-8",
    )

    def fake_getaddrinfo(host: str, port: int, *, type: int):  # noqa: A002, ANN001, ANN202
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.5", port))]

    def fake_connector(address: tuple[str, int], timeout: float) -> object:
        raise TimeoutError("timed out")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with patch.object(preflight.socket, "create_connection", side_effect=fake_connector):
        assert preflight.main(["--config", str(config_path), "--timeout", "3"]) == 2

    captured = capsys.readouterr()
    assert "Endpoint: edge.example:2222" in captured.out
    assert "Resolved addresses: 10.0.0.5" in captured.out
    assert "TCP preflight: FAIL - timed out" in captured.err


def test_preflight_cli_writes_json_report_for_archived_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    config_path = tmp_path / "config.yaml"
    report_path = tmp_path / "reports" / "preflight.json"
    config_path.write_text(
        'host: "user@edge.example"\nrepo_path: "/repo"\nssh_options: "-p 2222"\n',
        encoding="utf-8",
    )

    def fake_getaddrinfo(host: str, port: int, *, type: int):  # noqa: A002, ANN001, ANN202
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.5", port))]

    def fake_connector(address: tuple[str, int], timeout: float) -> object:
        raise TimeoutError("timed out")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with patch.object(preflight.socket, "create_connection", side_effect=fake_connector):
        assert preflight.main(
            [
                "--config",
                str(config_path),
                "--timeout",
                "3",
                "--json-report",
                str(report_path),
            ]
        ) == 2

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["config"] == str(config_path)
    assert report["host"] == "user@edge.example"
    assert report["endpoint"] == "edge.example:2222"
    assert report["resolved_addresses"] == ["10.0.0.5"]
    assert report["connected"] is False
    assert report["error"] == "timed out"
