from __future__ import annotations

from types import SimpleNamespace

from tools.prod_tui import smoke_test


class _Driver:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def run_remote(self, command: str, timeout: float = 30.0):  # noqa: ANN201
        self.commands.append(command)
        assert timeout == 180
        return "", 0


def test_install_check_sets_detected_python_bin() -> None:
    driver = _Driver()
    ctx = SimpleNamespace(
        config=SimpleNamespace(operator_email="dispatch-smoke@example.com"),
        driver=driver,
        capture=lambda _name: "install ok",
    )

    result = smoke_test.check_install_runs(ctx)  # type: ignore[arg-type]

    assert result.passed is True
    assert driver.commands == [
        "DISPATCH_PYTHON_BIN=$(command -v python3.11 || command -v python3.10) ./install.sh"
    ]


def test_smoke_reuse_session_help_uses_current_tmux_module_cli() -> None:
    help_text = smoke_test.build_parser().format_help()
    normalized = " ".join(help_text.split())

    assert "py -m tools.prod_tui tmux start --config" in normalized
    assert "py tools/prod_tui/robocop_tmux.py" not in help_text
