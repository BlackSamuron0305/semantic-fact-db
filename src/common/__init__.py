"""Canonical Semantic Model — foundational types for all SFDB modules.

This package defines the mathematically rigorous canonical model that every
storage engine (KG, SheafDB, SimplicialDB) must map to and from without
losing information.

The central type is ``SemanticFact``, which represents a single n-ary semantic
fact with full provenance, temporal validity, confidence, and metadata.

Sub-modules
-----------
- ``schema`` — SemanticFact dataclass.
- ``types`` — Identifier, Value, Context, Provenance, TemporalInfo.
- ``identifiers`` — ID generation utilities.
- ``validation`` — Invariant checking.
- ``serialization`` — JSON / Parquet / MessagePack.
- ``interfaces`` — DatabaseEngine ABC and query types.
- ``exceptions`` — Common exception hierarchy.
- ``config`` — YAML / env / CLI configuration.

Usage:
    from common.schema import SemanticFact
    from common.types import Identifier, Provenance
    from common.interfaces import DatabaseEngine, QueryType
"""

# ruff: noqa: F401

from common.config import Config
from common.exceptions import (
    BenchmarkError,
    ConfigError,
    ConsistencyError,
    QueryError,
    SerializationError,
    SFDBError,
    StorageError,
    ValidationError,
)
from common.identifiers import content_hash_id, new_id, prefixed_id
from common.interfaces import (
    DatabaseEngine,
    DeleteResult,
    EngineStatistics,
    EngineType,
    ExecutionPlan,
    InsertResult,
    Query,
    QueryResult,
    QueryType,
    StorageFormat,
    UpdateResult,
    VerificationResult,
)
from common.schema import SemanticFact
from common.serialization import (
    deserialize_json,
    deserialize_msgpack,
    deserialize_parquet,
    serialize_json,
    serialize_msgpack,
    serialize_parquet,
)
from common.types import (
    Context,
    Identifier,
    Provenance,
    RestrictionMap,
    SemanticType,
    TemporalInfo,
    Value,
)
from common.validation import check_fact_collection, check_fact_invariants

__all__ = sorted(
    [
        "BenchmarkError",
        "Config",
        "ConfigError",
        "ConsistencyError",
        "Context",
        "DatabaseEngine",
        "DeleteResult",
        "EngineStatistics",
        "EngineType",
        "ExecutionPlan",
        "Identifier",
        "InsertResult",
        "Provenance",
        "Query",
        "QueryError",
        "QueryResult",
        "QueryType",
        "RestrictionMap",
        "SFDBError",
        "SemanticFact",
        "SemanticType",
        "SerializationError",
        "StorageError",
        "StorageFormat",
        "TemporalInfo",
        "UpdateResult",
        "ValidationError",
        "Value",
        "VerificationResult",
        "check_fact_collection",
        "check_fact_invariants",
        "content_hash_id",
        "deserialize_json",
        "deserialize_msgpack",
        "deserialize_parquet",
        "new_id",
        "prefixed_id",
        "serialize_json",
        "serialize_msgpack",
        "serialize_parquet",
    ]
)
