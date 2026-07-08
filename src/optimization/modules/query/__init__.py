"""Query-level optimization modules."""

from __future__ import annotations

from typing import Any


def all_query_optimizations() -> dict[str, Any]:
    """Return dict of {name: module_dict} for all query optimizations."""
    return {
        "query.lru_parsed_cache": {
            "description": "LRU cache of parsed AST by query text hash",
            "module": "sfdb.query.cache",
            "hook": "parsed_cache",
        },
        "query.lru_logical_cache": {
            "description": "LRU cache of logical plans by AST hash",
            "module": "sfdb.query.cache",
            "hook": "logical_cache",
        },
        "query.lru_physical_cache": {
            "description": "LRU cache of physical plans by logical plan hash",
            "module": "sfdb.query.cache",
            "hook": "physical_cache",
        },
        "query.constant_folding": {
            "description": "Evaluate constant expressions at planning time",
            "module": "sfdb.query.optimizer",
            "hook": "constant_folding",
        },
        "query.predicate_pushdown": {
            "description": "Move predicates closer to scan operators",
            "module": "sfdb.query.optimizer",
            "hook": "predicate_pushdown",
        },
        "query.projection_pushdown": {
            "description": "Remove unused columns early",
            "module": "sfdb.query.optimizer",
            "hook": "projection_pushdown",
        },
        "query.dead_operator_removal": {
            "description": "Remove operators producing no results",
            "module": "sfdb.query.optimizer",
            "hook": "dead_operator_removal",
        },
        "query.logical_simplification": {
            "description": "Simplify redundant projections and selections",
            "module": "sfdb.query.optimizer",
            "hook": "logical_simplification",
        },
        "query.cost_optimizer": {
            "description": "Select optimal engine via cost model",
            "module": "sfdb.optimizer",
            "hook": "cost_optimizer",
        },
        "query.result_caching": {
            "description": "Cache final query results by hash",
            "module": "sfdb.query.cache",
            "hook": "result_caching",
        },
    }
