"""Contextual benchmark workload definitions — C1 through C10.

Each workload defines a semantic question, a KG-equivalent approach,
a SheafDB approach, a structured input schema, and a correctness oracle.
These workloads specifically stress-test SheafDB's advantages: contextual
neighborhood, high arity, temporal intervals, provenance, consistency,
and global sections.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable


class WorkloadCategory(Enum):
    CONTEXTUAL_NEIGHBORHOOD = auto()
    HIGH_ARITY = auto()
    TEMPORAL = auto()
    PROVENANCE = auto()
    CONSISTENCY = auto()
    GLOBAL_SECTION = auto()
    MIXED = auto()


@dataclass(frozen=True)
class ContextualWorkload:
    """A contextual benchmark workload with fairness contract.

    Fields
    ------
    id : str
        Short identifier (C1 … C10).
    name : str
        Human-readable name.
    category : WorkloadCategory
        Semantic category.
    description : str
        What this workload tests and why it matters.
    semantic_question : str
        The natural-language question both engines must answer.
    kg_approach : str
        Description of how KG answers this (including any simulation).
    sheaf_approach : str
        Description of how SheafDB answers natively.
    is_sheaf_native : bool
        Whether SheafDB has a native operator for this (KG must simulate).
    kg_simulation_note : str
        How KG simulates the answer if is_sheaf_native is True.
    input_params : dict[str, str]
        Named parameters for the workload generator.
    output_schema : dict[str, str]
        Expected columns in result rows.
    tags : tuple[str, ...]
        Searchable tags.
    """
    id: str
    name: str
    category: WorkloadCategory
    description: str
    semantic_question: str
    kg_approach: str
    sheaf_approach: str
    is_sheaf_native: bool = False
    kg_simulation_note: str = ""
    input_params: dict[str, str] = field(default_factory=dict)
    output_schema: dict[str, str] = field(default_factory=dict)
    tags: tuple[str, ...] = ()


C1 = ContextualWorkload(
    id="C1",
    name="Fact Neighborhood",
    category=WorkloadCategory.CONTEXTUAL_NEIGHBORHOOD,
    description=(
        "Retrieve all facts that share an entity with a given fact, "
        "within a configurable radius. Tests SheafDB's ability to "
        "traverse the presheaf star around a fact without index scans."
    ),
    semantic_question=(
        "Given fact f with subject s and object o, retrieve all facts "
        "whose subject or object references s or o, within k hops."
    ),
    kg_approach=(
        "Two-hop SPARQL query over ?s ?p ?o patterns with UNION. "
        "Requires O(k^n) UNION clauses for k-radius neighborhood."
    ),
    sheaf_approach=(
        "Stalk lookup: compute the star of the fact's identifier "
        "via the presheaf restriction map in O(deg(v)) time."
    ),
    is_sheaf_native=True,
    kg_simulation_note=(
        "KG can simulate via recursive SPARQL UNION queries, "
        "but query size grows exponentially with radius."
    ),
    input_params={
        "radius": "int (1-5): neighborhood radius in hops",
        "num_facts": "int: number of facts in the base dataset",
        "num_seeds": "int: number of random seed facts to query",
    },
    output_schema={
        "fact_id": "str",
        "subject": "str",
        "predicate": "str",
        "object": "str",
        "context": "str",
        "distance": "int",
    },
    tags=("contextual", "neighborhood", "stalk", "star"),
)

C2 = ContextualWorkload(
    id="C2",
    name="Path Context",
    category=WorkloadCategory.CONTEXTUAL_NEIGHBORHOOD,
    description=(
        "Given two entities, find all paths connecting them through "
        "intermediate facts. Tests SheafDB's topological path "
        "enumeration via the sheaf restriction structure."
    ),
    semantic_question=(
        "Find all paths of length ≤ L connecting entity A to entity B, "
        "where each step is a fact sharing a common entity."
    ),
    kg_approach=(
        "Property path query (SPARQL) with regex patterns like "
        "?s (ex:p|^ex:p){L} ?o. Path enumeration requires joins."
    ),
    sheaf_approach=(
        "Topological path enumeration: walk the sheaf's incidence "
        "structure using restriction maps to find connecting paths."
    ),
    is_sheaf_native=True,
    kg_simulation_note=(
        "KG uses SPARQL property paths; path extraction requires "
        "post-processing to reconstruct the full sequence of facts."
    ),
    input_params={
        "max_path_length": "int (1-6): maximum path length",
        "num_entity_pairs": "int: number of A-B pairs to query",
        "graph_density": "float (0-1): probability of edge between entities",
    },
    output_schema={
        "path_id": "str",
        "step": "int",
        "fact_id": "str",
        "subject": "str",
        "predicate": "str",
        "object": "str",
    },
    tags=("contextual", "path", "topology", "enumeration"),
)

C3 = ContextualWorkload(
    id="C3",
    name="High-Arity Lookup",
    category=WorkloadCategory.HIGH_ARITY,
    description=(
        "Lookup facts by partial pattern over high-arity relations "
        "(arity ≥ 5). Tests SheafDB's native multi-argument indexing "
        "vs KG's reification overhead."
    ),
    semantic_question=(
        "Find all facts of relation R where argument positions "
        "2, 4, and 5 match given values."
    ),
    kg_approach=(
        "Reified statement pattern with rdf:type R, rdf:subject, "
        "rdf:object for each positional argument. Requires joins "
        "across reification triples."
    ),
    sheaf_approach=(
        "Direct tuple lookup on the multi-arity fact store using "
        "a partial match on the relation signature."
    ),
    is_sheaf_native=True,
    kg_simulation_note=(
        "KG uses the N-ary reification pattern from W3C standards. "
        "Each high-arity fact requires 2a+1 triples (a = arity). "
        "Lookup requires a-way self-join over reification triples."
    ),
    input_params={
        "arity": "int (3-30): number of argument positions",
        "num_facts": "int: dataset size",
        "match_positions": "list[int]: which positions are constrained",
    },
    output_schema={
        "fact_id": "str",
        **{f"arg_{i}": "str" for i in range(5)},
    },
    tags=("high-arity", "lookup", "reification", "tuple"),
)

C4 = ContextualWorkload(
    id="C4",
    name="High-Arity Star Join",
    category=WorkloadCategory.HIGH_ARITY,
    description=(
        "Join two high-arity fact types on shared argument positions. "
        "Tests SheafDB's ability to exploit multi-arity signatures "
        "for efficient join planning."
    ),
    semantic_question=(
        "Find pairs of facts (f1 of relation R1, f2 of relation R2) "
        "where f1.arg[i] == f2.arg[j] for specified position pairs."
    ),
    kg_approach=(
        "Join over reification: f1 rdf:subject ?x . f2 rdf:object ?x "
        "plus positional joins. 6+ triple patterns per fact pair."
    ),
    sheaf_approach=(
        "Multi-arity join: hash-join on the specified argument "
        "positions directly using the tuple store."
    ),
    is_sheaf_native=True,
    kg_simulation_note=(
        "KG simulates via multiple reification triple patterns. "
        "Each dimension of arity multiplies the triple count."
    ),
    input_params={
        "arity_r1": "int: arity of relation 1",
        "arity_r2": "int: arity of relation 2",
        "join_positions": "list[tuple[int,int]]: (pos in R1, pos in R2)",
        "num_facts": "int: dataset size",
    },
    output_schema={
        "f1_id": "str",
        "f2_id": "str",
        "join_value": "str",
    },
    tags=("high-arity", "join", "multi-arity", "optimization"),
)

C5 = ContextualWorkload(
    id="C5",
    name="Temporal Interval Query",
    category=WorkloadCategory.TEMPORAL,
    description=(
        "Find facts whose temporal interval overlaps, contains, or "
        "is contained by a query interval. Tests SheafDB's temporal "
        "indexing within the sheaf structure."
    ),
    semantic_question=(
        "Retrieve all facts with [start, end) interval that overlaps "
        "the query interval [Q_start, Q_end)."
    ),
    kg_approach=(
        "Reified temporal annotations: each fact has ex:validStart "
        "and ex:validEnd. Query uses FILTER(?start < Q_end && ?end > Q_start)."
    ),
    sheaf_approach=(
        "Temporal interval index on the sheaf: interval tree or "
        "segment tree over the fact's valid-time dimension."
    ),
    is_sheaf_native=True,
    kg_simulation_note=(
        "KG simulates with FILTER on reified temporal triples. "
        "No native interval indexing available."
    ),
    input_params={
        "num_facts": "int: dataset size",
        "num_queries": "int: number of random query intervals",
        "interval_length": "int: mean length of temporal intervals",
        "time_range": "int: total time range",
    },
    output_schema={
        "fact_id": "str",
        "start": "int",
        "end": "int",
        "overlap_type": "str",
    },
    tags=("temporal", "interval", "valid-time", "index"),
)

C6 = ContextualWorkload(
    id="C6",
    name="Temporal Aggregation",
    category=WorkloadCategory.TEMPORAL,
    description=(
        "Compute aggregate statistics over temporal windows. Tests "
        "SheafDB's ability to use sheaf structure for sliding-window "
        "and rolling computations."
    ),
    semantic_question=(
        "For each time window of size W, compute the count and "
        "average of numeric attribute across facts active in that window."
    ),
    kg_approach=(
        "For each window, execute a COUNT/AVG query with FILTER on "
        "time interval. Requires N separate queries for N windows."
    ),
    sheaf_approach=(
        "Single pass over the interval tree: windowed aggregation "
        "using the sheaf's temporal decomposition."
    ),
    is_sheaf_native=True,
    kg_simulation_note=(
        "KG issues one SPARQL query per window; cost is O(N * log M). "
        "SheafDB does O(M + N) for M facts and N windows."
    ),
    input_params={
        "num_facts": "int: dataset size",
        "window_size": "int: aggregation window size",
        "num_windows": "int: number of sliding windows",
    },
    output_schema={
        "window_id": "int",
        "window_start": "int",
        "window_end": "int",
        "fact_count": "int",
        "avg_value": "float",
    },
    tags=("temporal", "aggregation", "window", "rolling"),
)

C7 = ContextualWorkload(
    id="C7",
    name="Provenance Chain",
    category=WorkloadCategory.PROVENANCE,
    description=(
        "Given a derived fact, trace its provenance chain through "
        "source facts, transformations, and confidence scores. Tests "
        "SheafDB's native attribution tracking."
    ),
    semantic_question=(
        "For derived fact D, retrieve the chain of source facts, "
        "transformations applied, and confidence scores along each edge."
    ),
    kg_approach=(
        "PROV-O ontology: prov:wasDerivedFrom, prov:used, "
        "prov:wasGeneratedBy. Recursive SPARQL query up the derivation tree."
    ),
    sheaf_approach=(
        "Provenance sheaf: derivation as restriction maps on the "
        "attribution presheaf. Single-pass trace from D to root sources."
    ),
    is_sheaf_native=True,
    kg_simulation_note=(
        "KG uses PROV-O with recursive SPARQL property paths. "
        "Path enumeration is quadratic in chain length."
    ),
    input_params={
        "chain_length": "int (1-20): length of provenance chain",
        "num_chains": "int: number of derived facts to trace",
        "branching": "int: number of sources per transformation",
    },
    output_schema={
        "step": "int",
        "fact_id": "str",
        "source_ids": "list[str]",
        "transformation": "str",
        "confidence": "float",
    },
    tags=("provenance", "attribution", "derivation", "prov-o"),
)

C8 = ContextualWorkload(
    id="C8",
    name="Consistency Check",
    category=WorkloadCategory.CONSISTENCY,
    description=(
        "Verify whether a set of local fact assignments can be "
        "consistently extended to a global assignment. Tests SheafDB's "
        "cocycle condition and consistency sheaf."
    ),
    semantic_question=(
        "Given partial assignments on overlapping contexts, determine "
        "if there exists a global assignment that restricts to all "
        "local assignments simultaneously."
    ),
    kg_approach=(
        "No native consistency operator. Simulate via constraint "
        "satisfaction: enumerate all global assignments and check "
        "restrictions — exponential in context count."
    ),
    sheaf_approach=(
        "Consistency sheaf: compute stalk intersection and check "
        "the cocycle condition. Polynomial in the number of contexts."
    ),
    is_sheaf_native=True,
    kg_simulation_note=(
        "KG has no consistency primitive. Simulation requires "
        "exponential CSP enumeration or external constraint solver."
    ),
    input_params={
        "num_contexts": "int: number of overlapping contexts",
        "context_overlap": "float (0-1): overlap ratio",
        "consistent": "bool: whether to generate consistent data",
        "num_candidates": "int: candidate assignments per context",
    },
    output_schema={
        "is_consistent": "bool",
        "num_contexts": "int",
        "assignment_count": "int",
        "max_overlap": "int",
    },
    tags=("consistency", "cocycle", "global-section", "csp"),
)

C9 = ContextualWorkload(
    id="C9",
    name="Global Section",
    category=WorkloadCategory.GLOBAL_SECTION,
    description=(
        "Given a sheaf and a coverage condition, construct a global "
        "section from compatible local sections. Tests SheafDB's "
        "gluing and section-building capabilities."
    ),
    semantic_question=(
        "Given local assignments on a covering of the base space, "
        "construct the unique global assignment that restricts to "
        "each local assignment (if one exists)."
    ),
    kg_approach=(
        "No native global section operator. Simulate by collecting "
        "all local assignments, checking pairwise compatibility, "
        "and merging via set union — quadratic in context count."
    ),
    sheaf_approach=(
        "Gluing axiom: compute the limit of the sheaf over the "
        "covering. Direct construction via the global section functor."
    ),
    is_sheaf_native=True,
    kg_simulation_note=(
        "KG constructs the global assignment through iterative "
        "merging of compatible local assignments. O(c^2) for c contexts."
    ),
    input_params={
        "num_contexts": "int: covering size",
        "context_size": "int: assignments per context",
        "compatibility": "float (0-1): probability of compatibility",
    },
    output_schema={
        "has_global": "bool",
        "num_assignments": "int",
        "conflicts": "list[tuple[int,int]]",
        "built_section": "dict[str,str]",
    },
    tags=("global-section", "gluing", "limit", "functor"),
)

C10 = ContextualWorkload(
    id="C10",
    name="Mixed Realistic Workload",
    category=WorkloadCategory.MIXED,
    description=(
        "Flagship benchmark: a realistic multi-step query that combines "
        "contextual neighborhood, temporal constraints, provenance "
        "chain, and consistency checking. This is the primary "
        "evaluation workload for the SheafDB paper."
    ),
    semantic_question=(
        "Given a known fact F with temporal interval T, retrieve "
        "the contextual neighborhood around F (radius 2), filter by "
        "temporal overlap with T, trace the provenance of each "
        "neighbor back 3 steps, and verify that the resulting "
        "assignment is consistent across all contexts."
    ),
    kg_approach=(
        "Multi-stage pipeline: four separate SPARQL queries with "
        "intermediate result passing. Each stage is a full query lifecyle. "
        "No cross-stage optimization possible."
    ),
    sheaf_approach=(
        "Unified sheaf traversal: stalk lookup → temporal filter → "
        "provenance map follow → consistency check. All within the "
        "same sheaf walk, sharing intermediate results."
    ),
    is_sheaf_native=True,
    kg_simulation_note=(
        "KG must execute four sequential queries and combine "
        "results in application code. SheafDB executes one "
        "optimized sheaf walk with shared state."
    ),
    input_params={
        "num_facts": "int: base dataset size",
        "neighborhood_radius": "int (1-3)",
        "provenance_depth": "int (1-5)",
        "num_seeds": "int: number of seed facts to start from",
    },
    output_schema={
        "seed_id": "str",
        "neighbor_count": "int",
        "temporal_filtered": "int",
        "provenance_chains": "int",
        "is_consistent": "bool",
        "total_steps": "int",
    },
    tags=("flagship", "mixed", "multi-stage", "pipeline"),
)

ALL_CONTEXTUAL_WORKLOADS: list[ContextualWorkload] = [
    C1, C2, C3, C4, C5, C6, C7, C8, C9, C10,
]

WORKLOAD_BY_ID: dict[str, ContextualWorkload] = {
    w.id: w for w in ALL_CONTEXTUAL_WORKLOADS
}

WORKLOADS_BY_CATEGORY: dict[WorkloadCategory, list[ContextualWorkload]] = {}
for w in ALL_CONTEXTUAL_WORKLOADS:
    WORKLOADS_BY_CATEGORY.setdefault(w.category, []).append(w)
