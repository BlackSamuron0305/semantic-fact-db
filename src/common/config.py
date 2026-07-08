"""Common configuration system for all SFDB engines.

Supports three configuration sources (in increasing priority order):

1. YAML files
2. Environment variables
3. CLI overrides

All engines use the same ``Config`` dataclass, ensuring uniform setup.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import orjson
import yaml

from common.exceptions import ConfigError


@dataclass
class StorageConfig:
    backend: str = "inmemory"
    path: str = "./data"
    cache_size_mb: int = 256


@dataclass
class IndexConfig:
    enabled: bool = True
    auto_build: bool = True


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "sfdb.log"


@dataclass
class BenchmarkConfig:
    num_runs: int = 10
    warm_up: int = 3
    timeout_seconds: int = 300
    output_dir: str = "./results"


@dataclass
class Config:
    """Top-level configuration shared by all engines."""

    engine: str = "kg"
    name: str = "sfdb_default"

    storage: StorageConfig = field(default_factory=StorageConfig)
    indexes: IndexConfig = field(default_factory=IndexConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    benchmark: BenchmarkConfig = field(default_factory=BenchmarkConfig)

    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> Config:
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return cls._from_dict(raw)

    @classmethod
    def from_json(cls, path: str | Path) -> Config:
        """Load configuration from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
        raw = orjson.loads(path.read_bytes())
        return cls._from_dict(raw)

    @classmethod
    def _from_dict(cls, raw: dict[str, Any]) -> Config:
        cfg = cls()
        if "engine" in raw:
            cfg.engine = raw["engine"]
        if "name" in raw:
            cfg.name = raw["name"]
        if "storage" in raw:
            s = raw["storage"]
            cfg.storage = StorageConfig(
                backend=s.get("backend", cfg.storage.backend),
                path=s.get("path", cfg.storage.path),
                cache_size_mb=s.get("cache_size_mb", cfg.storage.cache_size_mb),
            )
        if "indexes" in raw:
            ix = raw["indexes"]
            cfg.indexes = IndexConfig(
                enabled=ix.get("enabled", cfg.indexes.enabled),
                auto_build=ix.get("auto_build", cfg.indexes.auto_build),
            )
        if "logging" in raw:
            lg = raw["logging"]
            cfg.logging = LoggingConfig(
                level=lg.get("level", cfg.logging.level),
                file=lg.get("file", cfg.logging.file),
            )
        if "benchmark" in raw:
            bm = raw["benchmark"]
            cfg.benchmark = BenchmarkConfig(
                num_runs=bm.get("num_runs", cfg.benchmark.num_runs),
                warm_up=bm.get("warm_up", cfg.benchmark.warm_up),
                timeout_seconds=bm.get("timeout_seconds", cfg.benchmark.timeout_seconds),
                output_dir=bm.get("output_dir", cfg.benchmark.output_dir),
            )
        skip = {"engine", "name", "storage", "indexes", "logging", "benchmark"}
        cfg.extra = {k: v for k, v in raw.items() if k not in skip}
        return cfg

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables.

        Environment variables use the prefix ``SFDB_``.
        Example: ``SFDB_ENGINE=sheaf``, ``SFDB_STORAGE_BACKEND=duckdb``.
        """
        cfg = cls()
        if "SFDB_ENGINE" in os.environ:
            cfg.engine = os.environ["SFDB_ENGINE"]
        if "SFDB_NAME" in os.environ:
            cfg.name = os.environ["SFDB_NAME"]
        if "SFDB_STORAGE_BACKEND" in os.environ:
            cfg.storage.backend = os.environ["SFDB_STORAGE_BACKEND"]
        if "SFDB_STORAGE_PATH" in os.environ:
            cfg.storage.path = os.environ["SFDB_STORAGE_PATH"]
        if "SFDB_LOG_LEVEL" in os.environ:
            cfg.logging.level = os.environ["SFDB_LOG_LEVEL"]
        if "SFDB_BENCHMARK_RUNS" in os.environ:
            cfg.benchmark.num_runs = int(os.environ["SFDB_BENCHMARK_RUNS"])
        return cfg

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "name": self.name,
            "storage": {
                "backend": self.storage.backend,
                "path": self.storage.path,
                "cache_size_mb": self.storage.cache_size_mb,
            },
            "indexes": {
                "enabled": self.indexes.enabled,
                "auto_build": self.indexes.auto_build,
            },
            "logging": {
                "level": self.logging.level,
                "file": self.logging.file,
            },
            "benchmark": {
                "num_runs": self.benchmark.num_runs,
                "warm_up": self.benchmark.warm_up,
                "timeout_seconds": self.benchmark.timeout_seconds,
                "output_dir": self.benchmark.output_dir,
            },
            **self.extra,
        }
