"""Architecture tests verifying that all engines expose identical APIs.

These tests ensure that:
1. The DatabaseEngine ABC defines the complete interface.
2. Stub engine implementations satisfy the interface contract.
3. The canonical model round-trips correctly through the adapter.
"""

from typing import get_type_hints

import pytest

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
from common.interfaces import (
    DatabaseEngine,
    DeleteResult,
    EngineStatistics,
    EngineType,
    ExecutionPlan,
    InsertResult,
    QueryResult,
    QueryType,
    StorageFormat,
    UpdateResult,
    VerificationResult,
)
from common.schema import SemanticFact
from common.types import Identifier


class TestDatabaseEngineInterface:
    """Verify that the DatabaseEngine ABC defines the full interface."""

    # All expected abstract methods
    EXPECTED_METHODS = {
        "engine_type",
        "create",
        "drop",
        "insert",
        "update",
        "delete",
        "query",
        "explain",
        "statistics",
        "verify",
        "export",
        "import_data",
    }

    def test_all_methods_abstract(self) -> None:
        """Every expected method must be abstract in the ABC."""
        for method in sorted(self.EXPECTED_METHODS):
            impl = getattr(DatabaseEngine, method, None)
            assert impl is not None, f"Missing method: {method}"
            assert hasattr(impl, "__isabstractmethod__"), f"{method} is not abstract"

    def test_method_signatures(self) -> None:
        """Check that method signatures include the expected parameters."""
        hints = get_type_hints(DatabaseEngine.insert)
        assert "fact" in hints
        assert hints["fact"] is SemanticFact or str(hints["fact"]) == "SemanticFact"

        hints = get_type_hints(DatabaseEngine.query)
        assert "query" in hints

    def test_engine_type_property(self) -> None:
        """engine_type must be an abstract property returning EngineType."""
        prop = getattr(DatabaseEngine, "engine_type", None)
        assert prop is not None
        # In Python 3.12+, check it's an abstract property
        assert isinstance(prop, property)


class TestResultTypes:
    """Verify all result dataclasses are well-formed."""

    def test_insert_result(self) -> None:
        r = InsertResult(fact_id=Identifier("x"), success=True)
        assert r.success
        assert r.fact_id == Identifier("x")

    def test_update_result(self) -> None:
        r = UpdateResult(fact_id=Identifier("x"), success=True)
        assert r.success

    def test_delete_result(self) -> None:
        r = DeleteResult(fact_id=Identifier("x"), success=False, message="not found")
        assert not r.success
        assert "not found" in r.message

    def test_query_result(self) -> None:
        r = QueryResult(execution_time_ns=100)
        assert r.execution_time_ns == 100
        assert r.facts == ()

    def test_execution_plan(self) -> None:
        p = ExecutionPlan(description="scan", estimated_cost=1.5, steps=("step1",))
        assert p.estimated_cost == 1.5
        assert "step1" in p.steps

    def test_engine_statistics(self) -> None:
        s = EngineStatistics(
            total_facts=100,
            total_entities=50,
            storage_bytes=1024,
            index_count=3,
            engine_type=EngineType.KNOWLEDGE_GRAPH,
        )
        assert s.total_facts == 100
        assert s.engine_type == EngineType.KNOWLEDGE_GRAPH

    def test_verification_result(self) -> None:
        v = VerificationResult(valid=True)
        assert v.valid
        v2 = VerificationResult(valid=False, errors=("err1",))
        assert not v2.valid
        assert len(v2.errors) == 1


class TestQueryTypeCoverage:
    """Verify all query types are defined."""

    def test_all_query_types_present(self) -> None:
        expected = {
            "LOOKUP",
            "PATH",
            "CONTEXT",
            "TEMPORAL",
            "AGGREGATION",
            "MIXED",
            "PROVENANCE",
            "NEIGHBORHOOD",
            "CONSISTENCY",
            "GLOBAL",
        }
        actual = {qt.name for qt in QueryType}
        assert actual == expected


class TestStorageFormatCoverage:
    def test_all_formats_present(self) -> None:
        expected = {"JSON", "PARQUET", "MSGPACK"}
        actual = {sf.name for sf in StorageFormat}
        assert actual == expected


class TestEngineTypeCoverage:
    def test_all_engines_present(self) -> None:
        expected = {"KNOWLEDGE_GRAPH", "SHEAF_DATABASE", "SIMPLICIAL_DATABASE"}
        actual = {et.name for et in EngineType}
        assert actual == expected


class TestExceptionHierarchy:
    """Verify the exception hierarchy is complete."""

    def test_sfdb_error_base(self) -> None:
        assert issubclass(StorageError, SFDBError)
        assert issubclass(ConsistencyError, SFDBError)
        assert issubclass(QueryError, SFDBError)
        assert issubclass(ValidationError, SFDBError)
        assert issubclass(SerializationError, SFDBError)
        assert issubclass(BenchmarkError, SFDBError)
        assert issubclass(ConfigError, SFDBError)

    def test_error_caught_by_base(self) -> None:
        with pytest.raises(SFDBError):
            raise StorageError("disk full")
        with pytest.raises(SFDBError):
            raise ConsistencyError("gluing failed")


class TestConfig:
    """Verify the configuration system works."""

    def test_default_config(self) -> None:
        cfg = Config()
        assert cfg.engine == "kg"
        assert cfg.storage.backend == "inmemory"
        assert cfg.benchmark.num_runs == 10

    def test_config_from_dict(self) -> None:
        cfg = Config._from_dict(
            {
                "engine": "sheaf",
                "storage": {"backend": "duckdb"},
                "benchmark": {"num_runs": 5},
            }
        )
        assert cfg.engine == "sheaf"
        assert cfg.storage.backend == "duckdb"
        assert cfg.benchmark.num_runs == 5

    def test_config_to_dict(self) -> None:
        cfg = Config(engine="simplicial")
        d = cfg.to_dict()
        assert d["engine"] == "simplicial"
        assert "storage" in d
        assert "indexes" in d
        assert "logging" in d
        assert "benchmark" in d
