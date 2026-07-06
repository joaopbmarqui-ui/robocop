"""Runtime environment detection for Dispatch."""

from __future__ import annotations

import os


def is_jupyter_notebook() -> bool:
    """Return True when Dispatch is running inside a Jupyter Notebook kernel."""
    override = os.environ.get("DISPATCH_JUPYTER_MODE", "").strip().lower()
    if override in {"1", "true", "yes", "on"}:
        return True
    if override in {"0", "false", "no", "off"}:
        return False
    if os.environ.get("JPY_PARENT_PID") or os.environ.get("JPY_SESSION_NAME"):
        return True
    try:
        from IPython import get_ipython
    except ImportError:
        return False
    shell = get_ipython()
    if shell is None:
        return False
    return shell.__class__.__name__ in {"ZMQInteractiveShell", "Shell"}
