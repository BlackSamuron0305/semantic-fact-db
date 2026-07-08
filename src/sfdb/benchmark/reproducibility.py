"""Reproducibility tracking — system info, git commit, seed, dataset checksum."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from datetime import UTC, datetime
from typing import Any

import psutil


class ReproducibilityRecord:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def capture(self, seed: int = 42, dataset_checksum: str = "") -> dict[str, Any]:
        self._data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "cpu_model": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=True),
            "memory_total": psutil.virtual_memory().total,
            "os": platform.system(),
            "os_release": platform.release(),
            "seed": seed,
            "dataset_checksum": dataset_checksum,
            "git": self._get_git_info(),
            "uv_lock": self._get_uv_hash(),
        }
        return self._data

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def to_json(self, path: str) -> str:
        with open(path, "w") as f:
            json.dump(self._data, f, indent=2)
        return path

    @staticmethod
    def _get_git_info() -> dict[str, str]:
        try:
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5
            ).stdout.strip()
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            dirty = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5
            ).stdout.strip()
            return {"commit": commit, "branch": branch, "dirty": bool(dirty)}
        except Exception:
            return {"commit": "unknown", "branch": "unknown", "dirty": False}

    @staticmethod
    def _get_uv_hash() -> str:
        try:
            if os.path.exists("uv.lock"):
                h = hashlib.sha256()
                h.update(open("uv.lock", "rb").read())
                return h.hexdigest()[:16]
        except Exception:
            pass
        return ""

    @staticmethod
    def checksum(data: Any) -> str:
        h = hashlib.sha256()
        h.update(str(data).encode())
        return h.hexdigest()[:16]
