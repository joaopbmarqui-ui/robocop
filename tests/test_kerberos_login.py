"""Tests for Jupyter Kerberos login startup flow."""

from __future__ import annotations

import asyncio

import pytest
from textual.widgets import Input

from dispatch.app import DispatchApp
from dispatch.screens.dashboard import DashboardScreen
from dispatch.screens.kerberos_login import KerberosLoginScreen


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", True),
        ("true", True),
        ("0", False),
        ("false", False),
    ],
)
def test_is_jupyter_notebook_honors_override(monkeypatch, value: str, expected: bool) -> None:
    from dispatch import runtime

    monkeypatch.delenv("JPY_PARENT_PID", raising=False)
    monkeypatch.delenv("JPY_SESSION_NAME", raising=False)
    monkeypatch.setenv("DISPATCH_JUPYTER_MODE", value)
    assert runtime.is_jupyter_notebook() is expected


def test_jupyter_startup_prompts_for_kerberos_when_ticket_missing(
    mock_env_with_config, monkeypatch
) -> None:
    monkeypatch.setenv("DISPATCH_JUPYTER_MODE", "1")
    monkeypatch.setenv("DISPATCH_MOCK_KLIST_TTL", "0")

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(140, 50)) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, KerberosLoginScreen)
            app.screen.query_one("#kerberos-login-eid", Input).value = "testuser"
            app.screen.query_one("#kerberos-login-password", Input).value = "secret"
            await pilot.click("#kerberos-login-submit")
            await pilot.pause()
            assert isinstance(app.screen, DashboardScreen)
            assert app.kerberos_ttl is not None
            assert app.kerberos_ttl > 0

    asyncio.run(run())


def test_jupyter_startup_skips_login_when_ticket_present(mock_env_with_config, monkeypatch) -> None:
    monkeypatch.setenv("DISPATCH_JUPYTER_MODE", "1")
    monkeypatch.setenv("DISPATCH_MOCK_KLIST_TTL", "28800")

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(140, 50)) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, DashboardScreen)

    asyncio.run(run())


def test_non_jupyter_startup_skips_login_even_without_ticket(
    mock_env_with_config, monkeypatch
) -> None:
    monkeypatch.setenv("DISPATCH_JUPYTER_MODE", "0")
    monkeypatch.setenv("DISPATCH_MOCK_KLIST_TTL", "0")

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(140, 50)) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, DashboardScreen)

    asyncio.run(run())


def test_jupyter_login_shows_error_and_allows_retry(mock_env_with_config, monkeypatch) -> None:
    monkeypatch.setenv("DISPATCH_JUPYTER_MODE", "1")
    monkeypatch.setenv("DISPATCH_MOCK_KLIST_TTL", "0")
    monkeypatch.setenv("DISPATCH_MOCK_SCENARIO", "auth_error")

    async def run() -> None:
        app = DispatchApp()
        async with app.run_test(size=(140, 50)) as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, KerberosLoginScreen)
            screen.query_one("#kerberos-login-eid", Input).value = "testuser"
            screen.query_one("#kerberos-login-password", Input).value = "wrong"
            await pilot.click("#kerberos-login-submit")
            await pilot.pause(delay=0.2)
            error = str(screen.query_one("#kerberos-login-error").render())
            assert "Password incorrect" in error
            assert isinstance(app.screen, KerberosLoginScreen)

            monkeypatch.setenv("DISPATCH_MOCK_SCENARIO", "happy_path")
            password_input = screen.query_one("#kerberos-login-password", Input)
            password_input.value = "secret"
            assert password_input.value == "secret"
            screen.action_submit()
            await pilot.pause(delay=0.5)
            assert isinstance(app.screen, DashboardScreen)

    asyncio.run(run())
