"""System metrics collection — CPU, memory, timing, profiling."""

from __future__ import annotations

import gc
import platform
import time
from dataclasses import dataclass
from typing import Any

import psutil


@dataclass(slots=True)
class SystemMetrics:
    latency_ns: int = 0
    memory_bytes: int = 0
    cpu_percent: float = 0.0
    rss_bytes: int = 0
    gc_collections: int = 0
    disk_read_bytes: int = 0
    disk_write_bytes: int = 0

    @property
    def latency_ms(self) -> float:
        return self.latency_ns / 1e6


@dataclass(slots=True)
class ProfileSnapshot:
    timestamp: float = 0.0
    rss: int = 0
    cpu: float = 0.0
    gc_count: int = 0
    disk_read: int = 0
    disk_write: int = 0


class Profiler:
    def __init__(self) -> None:
        self._process = psutil.Process()
        self._io_start = (
            self._process.io_counters() if hasattr(self._process, "io_counters") else None
        )
        self._gc_start = gc.get_count()

    def snapshot(self) -> ProfileSnapshot:
        io = self._process.io_counters() if hasattr(self._process, "io_counters") else None
        return ProfileSnapshot(
            timestamp=time.time(),
            rss=self._process.memory_info().rss,
            cpu=self._process.cpu_percent(interval=0),
            gc_count=sum(gc.get_count()),
            disk_read=io.read_bytes if io else 0,
            disk_write=io.write_bytes if io else 0,
        )

    @staticmethod
    def system_info() -> dict[str, Any]:
        uname = platform.uname()
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_model": uname.processor,
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_physical": psutil.cpu_count(logical=False),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "os": uname.system,
            "os_release": uname.release,
            "os_version": uname.version,
        }

    @staticmethod
    def force_gc() -> None:
        gc.collect()
        gc.collect()
        gc.collect()


class MeasuredRun:
    def __init__(self, label: str = "") -> None:
        self.label = label
        self._profiler = Profiler()

    def __enter__(self) -> MeasuredRun:
        Profiler.force_gc()
        self._before = self._profiler.snapshot()
        self._start = time.perf_counter_ns()
        return self

    def __exit__(self, *args: Any) -> None:
        self._end = time.perf_counter_ns()
        self._after = self._profiler.snapshot()
        self.latency_ns = self._end - self._start
        self.memory_delta = self._after.rss - self._before.rss
        self.cpu_delta = self._after.cpu - self._before.cpu
        self.gc_delta = self._after.gc_count - self._before.gc_count
        self.disk_read_delta = self._after.disk_read - self._before.disk_read
        self.disk_write_delta = self._after.disk_write - self._before.disk_write

    def metrics(self) -> SystemMetrics:
        return SystemMetrics(
            latency_ns=self.latency_ns,
            memory_bytes=max(0, self.memory_delta),
            cpu_percent=max(0.0, self.cpu_delta),
            rss_bytes=self._after.rss,
            gc_collections=max(0, self.gc_delta),
            disk_read_bytes=max(0, self.disk_read_delta),
            disk_write_bytes=max(0, self.disk_write_delta),
        )
