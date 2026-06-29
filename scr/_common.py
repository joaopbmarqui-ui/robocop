# pylint: disable=logging-fstring-interpolation,too-many-return-statements,too-many-branches
import logging
import os
import re
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from typing import Callable


FATAL_ERRORS = {"TABLE_NOT_FOUND", "SYNTAX_ERROR", "DUPLICATE_COLUMN", "AUTH_ERROR", "GENERIC_ERROR"}
IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
FULL_TABLE_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*"
)
SMTP_TIMEOUT_SECONDS = 30.0


def validate_identifier(value: str) -> bool:
    return IDENTIFIER_RE.fullmatch(value) is not None


def validate_full_table(value: str) -> bool:
    return FULL_TABLE_RE.fullmatch(value) is not None


def send_email(messageBody, subject, to_email):
    msg = MIMEMultipart()
    from_email = 'AutoQueryExecution_Analytics@mastercard.com'
    msg['From'] = from_email
    msg['TO'] = to_email
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(messageBody))

    try:
        mailhost = os.environ.get("MAILHOST", "mailhost.mclocal.int")
        host, _, port = mailhost.partition(":")
        server = smtplib.SMTP(host, int(port) if port else 0, timeout=SMTP_TIMEOUT_SECONDS)
        try:
            server.sendmail(from_email, to_email.split(';'), msg.as_string())
        finally:
            server.quit()
        logging.info(f"Email sent to {to_email} with subject: {subject}")
    except Exception as e:
        logging.error(f"Failed to send email. Error: {e}")


def classificar_erro_impala(stderr_text: str) -> dict:
    texto = stderr_text.lower()
    details = {"detalhes": stderr_text}
    if "memory limit exceeded" in texto:
        return {"categoria": "MEMORY_EXCEEDED", **details}
    if "not enough memory available" in texto:
        return {"categoria": "MEMORY_EXCEEDED", **details}
    if "syntax error" in texto or "parseexception" in texto:
        return {"categoria": "SYNTAX_ERROR", **details}
    if "authenticationexception" in texto:
        return {"categoria": "AUTH_ERROR", **details}
    if "table not found" in texto or "could not resolve" in texto:
        return {"categoria": "TABLE_NOT_FOUND", **details}
    if "timed out" in texto or "deadline exceeded" in texto:
        return {"categoria": "TIMEOUT", **details}
    if "queue is full" in texto or "no resources available" in texto:
        return {"categoria": "QUEUE_FULL", **details}
    if "could not connect" in texto or "connection refused" in texto:
        return {"categoria": "CONNECTION_ERROR", **details}
    if "dropped due to backpressure" in texto:
        return {"categoria": "BACKPRESSURE", **details}
    if "could not resolve host" in texto or "name or service not known" in texto:
        return {"categoria": "HOST_RESOLUTION_ERROR", **details}
    if "invalid credentials" in texto or "authentication failed" in texto:
        return {"categoria": "AUTH_ERROR", **details}
    if "invalid or unknown query handle" in texto:
        return {"categoria": "TIMEOUT", **details}
    if "time limit" in texto:
        return {"categoria": "TIMEOUT", **details}
    if "duplicate column name" in texto:
        return {"categoria": "DUPLICATE_COLUMN", **details}
    if "unreachable" in texto:
        return {"categoria": "HOST_UNREACHABLE", **details}
    if "diskspace" in texto or "disk full" in texto:
        return {"categoria": "DISK_FULL", **details}
    if "memory available" in texto:
        return {"categoria": "MEMORY_AVAILABLE", **details}
    if "space limit" in texto:
        return {"categoria": "SPACE_LIMIT", **details}
    if "timeout" in texto:
        return {"categoria": "TIMEOUT", **details}
    return {"categoria": "GENERIC_ERROR", **details}


def cycle_through_pools(
    pools: list[str],
    operation: Callable[[str], bool],
    on_cycle_failure: Callable[[int], None],
    retry_interval: int = 30,
    max_cycles: int | None = None,
) -> bool:
    retry_cnt = 1
    while True:
        for pool in pools:
            if operation(pool):
                return True
        if max_cycles is not None and retry_cnt >= max_cycles:
            raise TimeoutError("Retry cycle limit reached.")
        on_cycle_failure(retry_cnt)
        retry_cnt += 1
        time.sleep(retry_interval)
