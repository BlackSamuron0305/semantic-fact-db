"""Deep memory analysis.

Measures the memory footprint of each cache and index structure.
Uses sys.getsizeof (shallow) and a recursive size estimator (deep)
to attribute memory to each optimization module.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEntry:
    name: str
    shallow_bytes: int = 0
    deep_bytes: int = 0
    item_count: int = 0
    note: str = ""


@dataclass
class MemoryReport:
    entries: list[MemoryEntry] = field(default_factory=list)

    @property
    def total_shallow(self) -> int:
        return sum(e.shallow_bytes for e in self.entries)

    @property
    def total_deep(self) -> int:
        return sum(e.deep_bytes for e in self.entries)

    def by_category(self) -> dict[str, int]:
        cat: dict[str, int] = defaultdict(int)
        for e in self.entries:
            cat["all"] += e.deep_bytes
        return dict(cat)

    def top_k(self, k: int = 10) -> list[MemoryEntry]:
        return sorted(self.entries, key=lambda e: e.deep_bytes, reverse=True)[:k]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_shallow_bytes": self.total_shallow,
            "total_deep_bytes": self.total_deep,
            "entries": [
                {
                    "name": e.name,
                    "shallow_bytes": e.shallow_bytes,
                    "deep_bytes": e.deep_bytes,
                    "item_count": e.item_count,
                    "note": e.note,
                }
                for e in self.entries
            ],
            "top_k": [
                {"name": e.name, "deep_bytes": e.deep_bytes}
                for e in self.top_k(10)
            ],
        }

    def to_text(self) -> str:
        lines = [
            "Memory Analysis Report",
            "=" * 80,
            f"Total shallow: {self.total_shallow:,} bytes ({self.total_shallow/1024:.1f} KB)",
            f"Total deep:    {self.total_deep:,} bytes ({self.total_deep/1024:.1f} KB)",
            "",
            "Top Consumers",
            "-" * 60,
        ]
        for e in self.top_k():
            lines.append(
                f"  {e.name:45s}  {e.deep_bytes:>10,} B  ({e.deep_bytes/1024:>8.1f} KB)  [{e.item_count} items]"
            )
        lines.extend(["", "All Entries", "-" * 60])
        for e in self.entries:
            lines.append(f"  {e.name:45s}  {e.deep_bytes:>10,} B  [{e.item_count} items]  {e.note}")
        return "\n".join(lines)


def estimate_deep_size(obj: Any, seen: set | None = None) -> int:
    """Estimate the deep memory size of an object and its references."""
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)

    if isinstance(obj, dict):
        for k, v in obj.items():
            size += estimate_deep_size(k, seen)
            size += estimate_deep_size(v, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            size += estimate_deep_size(item, seen)
    elif hasattr(obj, "__dict__"):
        size += estimate_deep_size(obj.__dict__, seen)
    elif hasattr(obj, "_store"):
        size += estimate_deep_size(obj._store, seen)
    elif hasattr(obj, "_cache"):
        size += estimate_deep_size(obj._cache, seen)

    return size


class MemoryAnalysis:
    def __init__(self) -> None:
        self._entries: list[MemoryEntry] = []

    def add(self, name: str, obj: Any, note: str = "") -> MemoryEntry:
        shallow = sys.getsizeof(obj)
        deep = estimate_deep_size(obj)
        item_count = len(obj) if hasattr(obj, "__len__") else (len(obj._store) if hasattr(obj, "_store") else 0)
        entry = MemoryEntry(name=name, shallow_bytes=shallow, deep_bytes=deep, item_count=item_count, note=note)
        self._entries.append(entry)
        return entry

    def analyze(self, objects: dict[str, Any]) -> MemoryReport:
        self._entries = []
        for name, obj in objects.items():
            self.add(name, obj)
        return MemoryReport(entries=self._entries)

    def report(self) -> MemoryReport:
        return MemoryReport(entries=self._entries)

    @staticmethod
    def analyze_engines(
        sheaf_engine: Any | None = None,
        kg_engine: Any | None = None,
    ) -> MemoryReport:
        analysis = MemoryAnalysis()
        targets: dict[str, Any] = {}

        if sheaf_engine is not None:
            if hasattr(sheaf_engine, "_presheaf"):
                targets["sheaf.presheaf"] = sheaf_engine._presheaf
            if hasattr(sheaf_engine, "_indexes"):
                targets["sheaf.indexes"] = sheaf_engine._indexes
            if hasattr(sheaf_engine, "_topology"):
                targets["sheaf.topology"] = sheaf_engine._topology
            if hasattr(sheaf_engine, "_global_section_cache"):
                targets["sheaf.global_section_cache"] = sheaf_engine._global_section_cache

        if kg_engine is not None:
            if hasattr(kg_engine, "_encoder"):
                targets["kg.dictionary_encoder"] = kg_engine._encoder
            if hasattr(kg_engine, "_indexes"):
                targets["kg.index_manager"] = kg_engine._indexes
            if hasattr(kg_engine, "_conn"):
                targets["kg.sqlite_connection"] = kg_engine._conn

        return analysis.analyze(targets)
