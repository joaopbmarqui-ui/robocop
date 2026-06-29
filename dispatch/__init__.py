"""Dispatch TUI package."""

import logging
from logging.handlers import RotatingFileHandler

from .version import __version__

__all__ = ["__version__", "setup_logging"]

logger = logging.getLogger("dispatch")


def setup_logging() -> None:
    """Configure rotating file handler at ~/.dispatch/dispatch.log."""
    from . import config  # deferred to avoid circular import

    try:
        log_path = config.ensure_private_dir(config.dispatch_home()) / "dispatch.log"
        handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    except OSError:
        pass
