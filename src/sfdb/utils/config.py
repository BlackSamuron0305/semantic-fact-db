"""Configuration loading and saving.

Uses JSON for configuration files. The configuration format is simple
and human-readable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a configuration from a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    return dict(orjson.loads(path.read_bytes()))


def save_config(config: dict[str, Any], path: str | Path) -> None:
    """Save a configuration to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(orjson.dumps(config, option=orjson.OPT_INDENT_2))
