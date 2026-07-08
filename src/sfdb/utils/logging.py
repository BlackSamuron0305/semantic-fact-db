"""Logging configuration for SFDB.

Sets up structured logging with timestamps and module names.
"""

from __future__ import annotations

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for SFDB.

    Parameters
    ----------
    level: Logging level (default: INFO).
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s :: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger("sfdb")
    root.setLevel(level)
    root.addHandler(handler)
