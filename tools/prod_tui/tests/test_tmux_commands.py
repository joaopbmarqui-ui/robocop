from __future__ import annotations

import subprocess
from unittest.mock import Mock, patch

from tools.prod_tui.robocop_tmux import ProdTuiConfig, TmuxDriver, load_config


def test_build_ssh_command_includes_options_and_host() -> None:
    driver = TmuxDriver(
        "user@edge",
        "robocop-prod-test",
        "/ads_storage/dispatch",
        ssh_options="-J jump-host -o StrictHostKeyChecking=no",
    )
    assert driver._build_ssh_command("tmux ls") == [
        "ssh",
        "-J",
        "jump-host",
        "-o",
        "StrictHostKeyChecking=no",
        "user@edge",
        "tmux ls",
    ]


def test_build_ssh_command_interactive_adds_tty() -> None:
    driver = TmuxDriver("user@edge", "session", "/repo")
    assert driver._build_ssh_command("tmux attach -t session", interactive=True) == [
        "ssh",
        "-t",
        "user@edge",
        "tmux attach -t session",
    ]


def test_start_session_constructs_kill_new_and_verify_commands() -> None:
    driver = TmuxDriver("user@edge", "session", "/repo path", width=120, height=40)
    with patch("subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], 0, "", "")
        driver.start_session()

    argv = run.call_args.args[0]
    remote = argv[-1]
    assert argv[:2] == ["ssh", "user@edge"]
    assert "tmux kill-session -t session" in remote
    assert "tmux new-session -d -s session -x 120 -y 40" in remote
    assert "/repo path" in remote
    assert "exec bash -l" in remote
    assert "tmux has-session -t session" in remote


def test_send_keys_appends_enter_for_shell_commands() -> None:
    driver = TmuxDriver("user@edge", "session", "/repo")
    with patch("subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], 0, "", "")
        driver.send_keys("ls")
    assert run.call_args.args[0][-1] == "tmux send-keys -t session ls Enter"


def test_send_text_sends_literal_text_then_enter_key() -> None:
    driver = TmuxDriver("user@edge", "session", "/repo")
    with patch("subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], 0, "", "")
        driver.send_text("hello world")
    calls = [call.args[0][-1] for call in run.call_args_list]
    assert calls == [
        "tmux send-keys -l -t session 'hello world'",
        "tmux send-keys -t session Enter",
    ]


def test_capture_screen_returns_stripped_stdout() -> None:
    driver = TmuxDriver("user@edge", "session", "/repo")
    with patch("subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], 0, "screen\n\n", "")
        assert driver.capture_screen() == "screen"


def test_stop_session_is_idempotent() -> None:
    driver = TmuxDriver("user@edge", "session", "/repo")
    with patch("subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], 1, "", "no session")
        driver.stop_session()
    assert run.call_args.kwargs["check"] is False


def test_attach_uses_popen_for_interactive_session() -> None:
    driver = TmuxDriver("user@edge", "session", "/repo")
    proc = Mock()
    proc.wait.return_value = 0
    with patch("subprocess.Popen", return_value=proc) as popen:
        driver.attach()
    assert popen.call_args.args[0] == ["ssh", "-t", "user@edge", "tmux attach -t session"]


def test_load_config_fallback_parses_simple_yaml(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        'host: "user@edge"\nrepo_path: "/repo"\nterminal_width: 132\n',
        encoding="utf-8",
    )
    config = load_config(config_path)
    assert config == ProdTuiConfig(host="user@edge", repo_path="/repo", terminal_width=132)
