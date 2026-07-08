"""KG-specific optimization modules."""

from __future__ import annotations

from typing import Any


def all_kg_optimizations() -> dict[str, Any]:
    """Return dict of {name: module_dict} for all KG optimizations."""
    return {
        "kg.six_index": {
            "description": "Six-way SPO/POS/OPS/SOP/PSO/OSP indexes",
            "module": "sfdb.kg.engine",
            "hook": "six_index",
        },
        "kg.dictionary_encoding": {
            "description": "Dictionary encoding for entities/predicates/literals",
            "module": "sfdb.kg.engine",
            "hook": "dictionary_encoding",
        },
        "kg.dictionary_cache": {
            "description": "In-memory dictionary lookup cache",
            "module": "sfdb.kg.engine",
            "hook": "dictionary_cache",
        },
        "kg.predicate_partitioning": {
            "description": "Partition triples by predicate",
            "module": "sfdb.kg.engine",
            "hook": "predicate_partitioning",
        },
        "kg.join_reordering": {
            "description": "Reorder joins by cardinality",
            "module": "sfdb.kg.optimizer",
            "hook": "join_reordering",
        },
        "kg.filter_pushdown": {
            "description": "Push filters toward scans",
            "module": "sfdb.kg.optimizer",
            "hook": "filter_pushdown",
        },
        "kg.batch_insert": {
            "description": "Batch inserts into single transaction",
            "module": "sfdb.kg.engine",
            "hook": "batch_insert",
        },
        "kg.pragma_tuning": {
            "description": "SQLite PRAGMA settings",
            "module": "sfdb.kg.engine",
            "hook": "pragma_tuning",
        },
        "kg.reification_skip": {
            "description": "Skip unused reification triples",
            "module": "sfdb.kg.engine",
            "hook": "reification_skip",
        },
        "kg.result_caching": {
            "description": "Cache query results by normalized text",
            "module": "sfdb.kg.engine",
            "hook": "result_caching",
        },
    }
