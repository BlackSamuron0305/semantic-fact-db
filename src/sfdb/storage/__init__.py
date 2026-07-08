"""Storage layer for the Semantic Fact Database.

Provides serialization, persistence, and I/O for both KG and Sheaf
representations. Uses Apache Arrow for columnar storage and DuckDB
for analytical queries during benchmarking.

The storage layer ensures that both representations can be persisted
to disk and reloaded identically — a requirement for reproducibility.
"""

from sfdb.storage.serialization import (
    CanonicalSerializer,
    FactSerializer,
    SectionSerializer,
    StorageStats,
    TripleSerializer,
)

__all__ = [
    "CanonicalSerializer",
    "FactSerializer",
    "SectionSerializer",
    "StorageStats",
    "TripleSerializer",
]
