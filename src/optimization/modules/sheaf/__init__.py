"""Sheaf-specific optimization modules."""

from __future__ import annotations

from typing import Any


def all_sheaf_optimizations() -> dict[str, Any]:
    """Return dict of {name: module_dict} for all sheaf optimizations."""
    return {
        "sheaf.restriction_cache": {
            "description": "Cache restriction map results",
            "module": "sfdb.sheaf.presheaf",
            "hook": "restriction_cache",
        },
        "sheaf.global_section_cache": {
            "description": "Cache computed global sections",
            "module": "sfdb.sheaf.indexes",
            "hook": "global_section_cache",
        },
        "sheaf.neighborhood_index": {
            "description": "Entity adjacency index",
            "module": "sfdb.sheaf.indexes",
            "hook": "neighborhood_index",
        },
        "sheaf.context_index": {
            "description": "Context string index",
            "module": "sfdb.sheaf.indexes",
            "hook": "context_index",
        },
        "sheaf.temporal_index": {
            "description": "Temporal index for year-based queries",
            "module": "sfdb.sheaf.indexes",
            "hook": "temporal_index",
        },
        "sheaf.provenance_index": {
            "description": "Provenance source/method index",
            "module": "sfdb.sheaf.indexes",
            "hook": "provenance_index",
        },
        "sheaf.topology_compression": {
            "description": "Collapse open sets with identical sections",
            "module": "sfdb.sheaf.topology",
            "hook": "topology_compression",
        },
        "sheaf.lazy_restriction": {
            "description": "Defer restriction computation",
            "module": "sfdb.sheaf.restriction",
            "hook": "lazy_restriction",
        },
        "sheaf.stalk_prefetch": {
            "description": "Prefetch likely stalks",
            "module": "sfdb.sheaf.stalk",
            "hook": "stalk_prefetch",
        },
        "sheaf.section_dedup": {
            "description": "Deduplicate sections with identical content",
            "module": "sfdb.sheaf.presheaf",
            "hook": "section_dedup",
        },
        "sheaf.parallel_gluing": {
            "description": "Parallelise global section computation",
            "module": "sfdb.sheaf.sheaf",
            "hook": "parallel_gluing",
        },
        "sheaf.context_aware_gluing": {
            "description": "Only glue sections sharing a context",
            "module": "sfdb.sheaf.sheaf",
            "hook": "context_aware_gluing",
        },
        "sheaf.incremental_update": {
            "description": "Incremental global section updates",
            "module": "sfdb.sheaf.sheaf",
            "hook": "incremental_update",
        },
    }
