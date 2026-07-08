"""Knowledge Graph (KG) subsystem.

A realistic RDF-style triple store used as the baseline for comparison
against the Sheaf Database. Implements standard SPO indexing, SPARQL-like
querying, and the full triple decomposition pipeline.

This is the *control group* in our experiment. It must be a correct,
realistic implementation — not a straw man.
"""

from sfdb.kg.engine import KnowledgeGraphEngine
from sfdb.kg.graph import KnowledgeGraph
from sfdb.kg.optimizer import QueryOptimizer, TableStatistics
from sfdb.kg.planner import PhysicalPlanBuilder, PlanExecutor
from sfdb.kg.query import KGQuery, KGQueryResult
from sfdb.kg.sparql import SparqlExecutor, SparqlParser
from sfdb.kg.triple import Triple, TripleStore
from sfdb.kg.visualization import KGViz

__all__ = [
    "KGQuery",
    "KGQueryResult",
    "KGViz",
    "KnowledgeGraph",
    "KnowledgeGraphEngine",
    "PhysicalPlanBuilder",
    "PlanExecutor",
    "QueryOptimizer",
    "SparqlExecutor",
    "SparqlParser",
    "TableStatistics",
    "Triple",
    "TripleStore",
]
