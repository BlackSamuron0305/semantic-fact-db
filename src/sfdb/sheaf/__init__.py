"""Sheaf-Native Semantic Database.

This package implements a semantic database backed by finite sheaf
theory, where each SemanticFact is stored as a complete LocalSection
(rather than decomposed into triples).

Exports
-------
Core types:
    FiniteTopologicalSpace, OpenSet, Neighborhood
    Presheaf, Sheaf, Stalk, LocalSection, GlobalSection
    RestrictionMap, RestrictionGraph
    ConsistencyChecker, ConsistencyDiagnostic

Engine:
    SheafDatabaseEngine
    SheafBenchmarkHooks

Query:
    SheafQueryPlanner, SheafPlan, SheafPlanStep
    SheafOptimizer, QueryClassification

Builders:
    TopologyBuilder, TopologyStrategy

Indexes:
    OpenSetIndex, StalkIndex, RestrictionIndex, ContextIndex,
    NeighborhoodIndex, TemporalIndex, ProvenanceIndex,
    GlobalSectionCache

Visualization:
    SheafViz
"""

from __future__ import annotations

from sfdb.sheaf.builder import TopologyBuilder, TopologyStrategy
from sfdb.sheaf.consistency import ConsistencyChecker, ConsistencyDiagnostic
from sfdb.sheaf.engine import SheafBenchmarkHooks, SheafDatabaseEngine
from sfdb.sheaf.indexes import (
    ContextIndex,
    GlobalSectionCache,
    NeighborhoodIndex,
    OpenSetIndex,
    ProvenanceIndex,
    RestrictionIndex,
    StalkIndex,
    TemporalIndex,
)
from sfdb.sheaf.optimizer import QueryClassification, SheafOptimizer
from sfdb.sheaf.presheaf import GlobalSection, LocalSection, Presheaf, Sheaf, Stalk
from sfdb.sheaf.query import SheafPlan, SheafPlanStep, SheafQueryPlanner
from sfdb.sheaf.restriction import RestrictionGraph, RestrictionMap
from sfdb.sheaf.topology import FiniteTopologicalSpace, Neighborhood, OpenSet
from sfdb.sheaf.visualization import SheafViz

__all__ = [
    "ConsistencyChecker",
    "ConsistencyDiagnostic",
    "ContextIndex",
    "FiniteTopologicalSpace",
    "GlobalSection",
    "GlobalSectionCache",
    "LocalSection",
    "Neighborhood",
    "NeighborhoodIndex",
    "OpenSet",
    "OpenSetIndex",
    "Presheaf",
    "ProvenanceIndex",
    "QueryClassification",
    "RestrictionGraph",
    "RestrictionIndex",
    "RestrictionMap",
    "Sheaf",
    "SheafBenchmarkHooks",
    "SheafDatabaseEngine",
    "SheafOptimizer",
    "SheafPlan",
    "SheafPlanStep",
    "SheafQueryPlanner",
    "SheafViz",
    "Stalk",
    "StalkIndex",
    "TemporalIndex",
    "TopologyBuilder",
    "TopologyStrategy",
]
