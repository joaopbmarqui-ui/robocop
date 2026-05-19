"""Remote tmux driver and CLI for production Dispatch TUI validation."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.yaml")


@dataclass(frozen=True)
class ProdTuiConfig:
    """Configuration for the production TUI harness."""

    host: str
    repo_path: str
    session_name: str = "robocop-prod-test"
    terminal_width: int = 120
    terminal_height: int = 40
    ssh_options: str = ""
    smoke_query_sql: str = "SELECT 1 AS smoke_test_value"
    scratch_schema: str = "dw_settle"
    table_prefix: str = "dispatch_smoke"
    max_smoke_job_wait_seconds: int = 120
    operator_email: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ProdTuiConfig":
        return cls(
            host=str(data.get("host", "your-user@edge-node")),
            repo_path=str(data.get("repo_path", "/ads_storage/dispatch")),
            session_name=str(data.get("session_name", "robocop-prod-test")),
            terminal_width=int(data.get("terminal_width", 120)),
            terminal_height=int(data.get("terminal_height", 40)),
            ssh_options=str(data.get("ssh_options", "") or ""),
            smoke_query_sql=str(data.get("smoke_query_sql", "SELECT 1 AS smoke_test_value")),
            scratch_schema=str(data.get("scratch_schema", "dw_settle")),
            table_prefix=str(data.get("table_prefix", "dispatch_smoke")),
            max_smoke_job_wait_seconds=int(data.get("max_smoke_job_wait_seconds", 120)),
            operator_email=str(data.get("operator_email", "") or os.environ.get("DISPATCH_EMAIL", "")),
        )

    def current_user(self) -> str:
        user_part = self.host.rsplit("@", 1)[0] if "@" in self.host else ""
        return os.environ.get("USER") or os.environ.get("USERNAME") or user_part or "dispatch"


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        return value


def _fallback_yaml_load(text: str) -> dict[str, Any]:
    """Parse the simple key/value YAML used by the harness config.

    PyYAML is the supported parser for operators, but this fallback keeps unit
    tests and command construction usable in a minimal local environment.
    """
    data: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = _parse_scalar(value)
    return data


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> ProdTuiConfig:
    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        data = _fallback_yaml_load(text)
    else:
        loaded = yaml.safe_load(text) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"Config must be a YAML mapping: {config_path}")
        data = loaded
    return ProdTuiConfig.from_mapping(data)


class TmuxDriver:
    """Drive a real Dispatch TUI running in tmux on a remote Edge Node."""

    def __init__(
        self,
        host: str,
        session: str,
        repo_path: str,
        width: int = 120,
        height: int = 40,
        ssh_options: str = "",
        retries: int = 0,
        retry_backoff: float = 3.0,
    ) -> None:
        self.host = host
        self.session = session
        self.repo_path = repo_path
        self.width = width
        self.height = height
        self.ssh_options = ssh_options
        self.retries = retries
        self.retry_backoff = retry_backoff

    @classmethod
    def from_config(cls, config: ProdTuiConfig, *, retries: int = 0) -> "TmuxDriver":
        return cls(
            host=config.host,
            session=config.session_name,
            repo_path=config.repo_path,
            width=config.terminal_width,
            height=config.terminal_height,
            ssh_options=config.ssh_options,
            retries=retries,
        )

    def _build_ssh_command(self, cmd: str, *, interactive: bool = False) -> list[str]:
        argv = ["ssh"]
        if interactive:
            argv.append("-t")
        if self.ssh_options:
            argv.extend(shlex.split(self.ssh_options))
        argv.extend([self.host, cmd])
        return argv

    def _ssh(
        self,
        cmd: str,
        *,
        interactive: bool = False,
        check: bool = True,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str] | int:
        argv = self._build_ssh_command(cmd, interactive=interactive)
        if interactive:
            proc = subprocess.Popen(argv)
            return proc.wait()

        attempts = self.retries + 1
        last_error: subprocess.CalledProcessError | None = None
        for attempt in range(attempts):
            try:
                return subprocess.run(
                    argv,
                    check=check,
                    capture_output=capture_output,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                last_error = exc
                if attempt == attempts - 1:
                    raise
                time.sleep(self.retry_backoff)
        assert last_error is not None
        raise last_error

    def start_session(self) -> None:
        kill = f"tmux kill-session -t {shlex.quote(self.session)} 2>/dev/null || true"
        start_inner = f"cd {shlex.quote(self.repo_path)} && exec bash -l"
        start = (
            f"tmux new-session -d -s {shlex.quote(self.session)} "
            f"-x {int(self.width)} -y {int(self.height)} {shlex.quote(start_inner)}"
        )
        verify = f"tmux has-session -t {shlex.quote(self.session)}"
        self._ssh(f"{kill}; {start}; {verify}")

    def send_keys(self, keys: str, *, literal: bool = False) -> None:
        flag = " -l" if literal else ""
        command = f"tmux send-keys{flag} -t {shlex.quote(self.session)} {shlex.quote(keys)}"
        if not literal:
            command += " Enter"
        self._ssh(command)

    def send_key(self, key: str) -> None:
        """Send a single tmux key without appending Enter."""
        self._ssh(f"tmux send-keys -t {shlex.quote(self.session)} {shlex.quote(key)}")

    def send_text(self, text: str) -> None:
        self.send_keys(text, literal=True)
        self.send_key("Enter")

    def capture_screen(self, history_lines: int = 200) -> str:
        command = (
            f"tmux capture-pane -t {shlex.quote(self.session)} "
            f"-p -S -{int(history_lines)}"
        )
        result = self._ssh(command)
        assert isinstance(result, subprocess.CompletedProcess)
        return result.stdout.rstrip()

    def attach(self) -> None:
        self._ssh(f"tmux attach -t {shlex.quote(self.session)}", interactive=True)

    def stop_session(self) -> None:
        self._ssh(
            f"tmux kill-session -t {shlex.quote(self.session)} 2>/dev/null || true",
            check=False,
        )

    def wait_for(
        self,
        pattern: str,
        timeout: float = 10.0,
        poll_interval: float = 0.5,
    ) -> str:
        import re

        deadline = time.monotonic() + timeout
        last_screen = ""
        while time.monotonic() < deadline:
            last_screen = self.capture_screen()
            if re.search(pattern, last_screen, flags=re.MULTILINE):
                return last_screen
            time.sleep(poll_interval)
        raise TimeoutError(
            f"Timed out after {timeout:.1f}s waiting for {pattern!r}.\n"
            f"Last screen:\n{last_screen}"
        )


def driver_from_config_path(path: str | Path, *, retries: int = 0) -> tuple[ProdTuiConfig, TmuxDriver]:
    config = load_config(path)
    return config, TmuxDriver.from_config(config, retries=retries)


_KEY_ALIASES = {
    "tab": "Tab",
    "enter": "Enter",
    "escape": "Escape",
    "esc": "Escape",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "home": "Home",
    "end": "End",
    "delete": "Delete",
    "backspace": "BSpace",
    "ctrl-a": "C-a",
    "ctrl-c": "C-c",
    "ctrl-e": "C-e",
}


def _add_common_args(parser: argparse.ArgumentParser, *, default: bool = True) -> None:
    kwargs: dict[str, object] = {
        "help": "Path to production TUI harness config.yaml",
    }
    if default:
        kwargs["default"] = str(DEFAULT_CONFIG_PATH)
    else:
        kwargs["default"] = argparse.SUPPRESS
    parser.add_argument("--config", **kwargs)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Drive Dispatch in a remote tmux session")
    _add_common_args(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Start a clean remote tmux session")
    _add_common_args(start, default=False)

    send = subparsers.add_parser("send", help="Send a shell command or TUI action and Enter")
    _add_common_args(send, default=False)
    send.add_argument("text")

    keys = subparsers.add_parser("keys", help="Send one or more tmux key names")
    _add_common_args(keys, default=False)
    keys.add_argument("keys", nargs="+")

    capture = subparsers.add_parser("capture", help="Capture the current tmux screen")
    _add_common_args(capture, default=False)
    capture.add_argument("--raw", action="store_true", help="Print raw capture text")
    capture.add_argument("--history-lines", type=int, default=200)

    attach = subparsers.add_parser("attach", help="Attach interactively to the remote tmux session")
    _add_common_args(attach, default=False)
    stop = subparsers.add_parser("stop", help="Stop the remote tmux session")
    _add_common_args(stop, default=False)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config, driver = driver_from_config_path(args.config)

    if args.command == "start":
        driver.start_session()
        print(
            f"Started tmux session {config.session_name!r} on {config.host} "
            f"at {config.terminal_width}x{config.terminal_height}"
        )
        return 0
    if args.command == "send":
        driver.send_keys(args.text)
        return 0
    if args.command == "keys":
        for key in args.keys:
            driver.send_key(_KEY_ALIASES.get(key.lower(), key))
        return 0
    if args.command == "capture":
        screen = driver.capture_screen(history_lines=args.history_lines)
        print(screen if args.raw else screen.encode("utf-8", "replace").decode("utf-8"))
        return 0
    if args.command == "attach":
        driver.attach()
        return 0
    if args.command == "stop":
        driver.stop_session()
        return 0
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
