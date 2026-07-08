"""Multi-level query plan caches."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    key_hash: int
    result: Any
    hit_count: int = 0

    def record_hit(self) -> None:
        self.hit_count += 1


class LRUCache:
    def __init__(self, max_size: int = 100) -> None:
        self._max_size = max_size
        self._store: OrderedDict[int, CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key_hash: int) -> Any | None:
        entry = self._store.get(key_hash)
        if entry is not None:
            self._hits += 1
            entry.record_hit()
            self._store.move_to_end(key_hash)
            return entry.result
        self._misses += 1
        return None

    def put(self, key_hash: int, result: Any) -> None:
        self._store[key_hash] = CacheEntry(key_hash=key_hash, result=result)
        self._store.move_to_end(key_hash)
        if len(self._store) > self._max_size:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()
        self._hits = 0
        self._misses = 0

    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def size(self) -> int:
        return len(self._store)

    def stats(self) -> dict:
        return {
            "size": len(self._store),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate(),
        }


class QueryCache:
    """Three-level cache: parsed AST, logical plan, physical plan."""

    def __init__(self, max_entries: int = 100) -> None:
        self.parsed = LRUCache(max_size=max_entries)
        self.logical = LRUCache(max_size=max_entries)
        self.physical = LRUCache(max_size=max_entries)

    def clear_all(self) -> None:
        self.parsed.clear()
        self.logical.clear()
        self.physical.clear()

    def stats(self) -> dict:
        return {
            "parsed": self.parsed.stats(),
            "logical": self.logical.stats(),
            "physical": self.physical.stats(),
        }
