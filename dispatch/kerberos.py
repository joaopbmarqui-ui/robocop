"""Kerberos pre-flight helpers.

TTL parsing expects MIT Kerberos `klist` output with a header line:
`Valid starting       Expires              Service principal`, followed by at
least one ticket row whose first two columns are `MM/DD/YYYY HH:MM:SS` start
and `MM/DD/YYYY HH:MM:SS` expiry timestamps.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime

from . import process

logger = logging.getLogger("dispatch.kerberos")

DEFAULT_REALM = "CORP.MASTERCARD.ORG"
KINIT_TIMEOUT_SECONDS = 30.0


def krb5_realm() -> str:
    return os.environ.get("DISPATCH_KRB5_REALM", DEFAULT_REALM)


def principal_for_eid(eid: str) -> str:
    login = eid.strip()
    if not login:
        return ""
    if "@" in login:
        return login
    return f"{login}@{krb5_realm()}"


async def has_ticket() -> bool:
    try:
        rc, _stdout, _stderr = await process.run_exec("klist", "-s", timeout=5)
        return rc == 0
    except (OSError, FileNotFoundError):
        logger.warning("klist not found on PATH")
        return False


async def kinit_with_password(eid: str, password: str) -> tuple[bool, str]:
    """Run ``kinit`` non-interactively and return ``(success, error_message)``."""
    principal = principal_for_eid(eid)
    if not principal:
        return False, "Enter your EID."
    if not password:
        return False, "Enter your Windows password."

    logger.info("Running kinit for principal %s", principal)
    try:
        proc = await asyncio.create_subprocess_exec(
            "kinit",
            principal,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except (OSError, FileNotFoundError):
        logger.warning("kinit not found on PATH")
        return False, "Kerberos tools are unavailable on this host."

    try:
        _stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=f"{password}\n".encode()),
            timeout=KINIT_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        logger.warning("kinit timed out for principal %s", principal)
        return False, "Kerberos sign-in timed out. Try again."

    if proc.returncode == 0:
        if not await has_ticket():
            return False, "Kerberos sign-in did not produce an active ticket."
        return True, ""

    message = stderr.decode(errors="replace").strip()
    if not message:
        message = "Kerberos authentication failed."
    logger.warning("kinit failed for principal %s: %s", principal, message)
    return False, message


async def ticket_ttl_seconds() -> int | None:
    try:
        rc, stdout, _stderr = await process.run_exec("klist", timeout=5)
    except (OSError, FileNotFoundError):
        logger.warning("klist not found on PATH; Kerberos unavailable")
        return None
    if rc != 0:
        return None
    return parse_ttl_seconds(stdout)


def parse_ttl_seconds(klist_output: str, now: datetime | None = None) -> int | None:
    current = now or datetime.now()
    for line in klist_output.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            expires = datetime.strptime(f"{parts[2]} {parts[3]}", "%m/%d/%Y %H:%M:%S")
        except ValueError:
            continue
        return max(0, int((expires - current).total_seconds()))
    return None
