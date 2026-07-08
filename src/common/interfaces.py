"""Abstract interface for all database engines.

Every storage engine (KnowledgeGraph, SheafDatabase, SimplicialDatabase)
must implement exactly this interface.  The benchmark layer communicates
only through this ABC — it never depends on a specific engine.

This ensures that:

1. Engines are drop-in replaceable.
2. Benchmark comparisons are fair.
3. New engines can be added without changing the benchmark.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Protocol, TypeVar

from common.schema import SemanticFact
from common.types import Identifier

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EngineType(Enum):
    KNOWLEDGE_GRAPH = auto()
    SHEAF_DATABASE = auto()
    SIMPLICIAL_DATABASE = auto()


class QueryType(Enum):
    LOOKUP = auto()
    PATH = auto()
    CONTEXT = auto()
    TEMPORAL = auto()
    AGGREGATION = auto()
    MIXED = auto()
    PROVENANCE = auto()
    NEIGHBORHOOD = auto()
    CONSISTENCY = auto()
    GLOBAL = auto()


class StorageFormat(Enum):
    JSON = auto()
    PARQUET = auto()
    MSGPACK = auto()


# ---------------------------------------------------------------------------
# Data-class results
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InsertResult:
    fact_id: Identifier
    success: bool
    message: str = ""


@dataclass(frozen=True)
class UpdateResult:
    fact_id: Identifier
    success: bool
    message: str = ""


@dataclass(frozen=True)
class DeleteResult:
    fact_id: Identifier
    success: bool
    message: str = ""


@dataclass(frozen=True)
class QueryResult:
    facts: tuple[SemanticFact, ...] = field(default_factory=tuple)
    execution_time_ns: int = 0
    rows_scanned: int = 0


@dataclass(frozen=True)
class ExecutionPlan:
    description: str
    estimated_cost: float
    steps: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EngineStatistics:
    total_facts: int
    total_entities: int
    storage_bytes: int
    index_count: int
    engine_type: EngineType
    selectivity: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    errors: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Query representation (logical)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Query:
    """A logical query, independent of any engine."""

    query_type: QueryType
    subject: Identifier | None = None
    relation: Identifier | None = None
    objects: tuple[Identifier, ...] = field(default_factory=tuple)
    context: str = "world"
    temporal_start: str | None = None
    temporal_end: str | None = None
    limit: int = 100
    offset: int = 0


# ---------------------------------------------------------------------------
# Abstract Database Engine
# ---------------------------------------------------------------------------


class DatabaseEngine(ABC):
    """Abstract interface that every storage engine must implement.

    Lifecycle
    ---------
    1. ``create``  — initialise storage and indexes.
    2. ``insert`` / ``update`` / ``delete`` — mutate data.
    3. ``query`` / ``explain`` — read data.
    4. ``statistics`` / ``verify`` — introspection.
    5. ``export`` / ``import_data`` — bulk transfer.
    6. ``drop`` — teardown.
    """

    @property
    @abstractmethod
    def engine_type(self) -> EngineType: ...

    # Lifecycle -------------------------------------------------------

    @abstractmethod
    def create(self, config: dict[str, Any] | None = None) -> None:
        """Initialise the database (create tables, directories, etc.)."""

    @abstractmethod
    def drop(self) -> None:
        """Destroy all data and teardown."""

    # CRUD ------------------------------------------------------------

    @abstractmethod
    def insert(self, fact: SemanticFact) -> InsertResult:
        """Store a single SemanticFact."""

    @abstractmethod
    def update(self, fact_id: Identifier, fact: SemanticFact) -> UpdateResult:
        """Replace the fact identified by *fact_id* with *fact*."""

    @abstractmethod
    def delete(self, fact_id: Identifier) -> DeleteResult:
        """Remove the fact identified by *fact_id*."""

    # Query -----------------------------------------------------------

    @abstractmethod
    def query(self, query: Query) -> QueryResult:
        """Execute a logical query and return semantic facts."""

    @abstractmethod
    def explain(self, query: Query) -> ExecutionPlan:
        """Return the execution plan without running it."""

    # Introspection ---------------------------------------------------

    @abstractmethod
    def statistics(self) -> EngineStatistics:
        """Return current engine statistics."""

    @abstractmethod
    def verify(self) -> VerificationResult:
        """Run internal consistency checks."""

    # Bulk ------------------------------------------------------------

    @abstractmethod
    def export(self, fmt: StorageFormat = StorageFormat.JSON) -> bytes:
        """Export all facts as bytes in the given format."""

    @abstractmethod
    def import_data(self, data: bytes, fmt: StorageFormat = StorageFormat.JSON) -> int:
        """Import facts from bytes.  Returns the number of facts imported."""


# ---------------------------------------------------------------------------
# Engine factory protocol
# ---------------------------------------------------------------------------


class EngineFactory(Protocol):
    """A callable that creates a DatabaseEngine instance."""

    def __call__(self, name: str = "default") -> DatabaseEngine: ...


EngineT = TypeVar("EngineT", bound=DatabaseEngine)


class EngineRegistry:
    """Registry of available engine factories."""

    def __init__(self) -> None:
        self._factories: dict[str, EngineFactory] = {}

    def register(self, name: str, factory: EngineFactory) -> None:
        self._factories[name] = factory

    def create(self, name: str, engine_name: str = "default") -> DatabaseEngine:
        if name not in self._factories:
            msg = f"Unknown engine: {name}.  Available: {list(self._factories)}"
            raise KeyError(msg)
        return self._factories[name](engine_name)

    def available(self) -> list[str]:
        return list(self._factories)


# ---------------------------------------------------------------------------
# Adapter base (for canonical-model bridging)
# ---------------------------------------------------------------------------


class CanonicalAdapter[EngineT: DatabaseEngine](ABC):
    """Bridges between an engine's native types and the canonical model."""

    def __init__(self, engine: EngineT) -> None:
        self._engine = engine

    @abstractmethod
    def to_canonical(self, native: Any) -> SemanticFact: ...

    @abstractmethod
    def from_canonical(self, fact: SemanticFact) -> Any: ...
