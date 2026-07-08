"""Common exception hierarchy for all SFDB components.

Every engine and module uses the same exception classes so that
error handling is uniform across the codebase.
"""


class SFDBError(Exception):
    """Base exception for all SFDB errors."""


# Storage errors ---------------------------------------------------------


class StorageError(SFDBError):
    """Raised when a storage operation fails."""


class IndexError(SFDBError):
    """Raised when an index operation fails."""


# Consistency errors -----------------------------------------------------


class ConsistencyError(SFDBError):
    """Raised when a consistency check fails."""


class ReferentialIntegrityError(ConsistencyError):
    """Raised when a fact references a non-existent entity."""


class GluingError(ConsistencyError):
    """Raised when sheaf gluing detects incompatible sections."""


# Query errors -----------------------------------------------------------


class QueryError(SFDBError):
    """Raised when query parsing or execution fails."""


class QueryParseError(QueryError):
    """Raised when a query cannot be parsed."""


class QueryExecutionError(QueryError):
    """Raised when query execution fails."""


# Validation errors ------------------------------------------------------


class ValidationError(SFDBError):
    """Raised when a SemanticFact fails invariant checks."""


class SerializationError(SFDBError):
    """Raised when serialisation or deserialisation fails."""


# Benchmark errors -------------------------------------------------------


class BenchmarkError(SFDBError):
    """Raised when the benchmark framework encounters an error."""


# Configuration errors ---------------------------------------------------


class ConfigError(SFDBError):
    """Raised when configuration loading or validation fails."""
