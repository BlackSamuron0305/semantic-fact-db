"""Query optimizer for the sheaf database.

Optimizer rules implement a preference hierarchy:
1. Local evaluation (single stalk)
2. Semi-local evaluation (related open sets)
3. Global evaluation (full reconstruction)

The optimizer also caches reusable global sections and avoids
repeated restriction computations.
"""

from __future__ import annotations

from common.interfaces import Query, QueryType
from sfdb.sheaf.indexes import (
    ContextIndex,
    NeighborhoodIndex,
    OpenSetIndex,
    ProvenanceIndex,
    TemporalIndex,
    parse_temporal_bound,
)
from sfdb.sheaf.restriction import RestrictionGraph


class QueryClassification:
    """Classification of a query along the local→global spectrum."""

    LOCAL = "local"
    SEMI_LOCAL = "semi_local"
    GLOBAL = "global"

    def __init__(self, level: str, target_open_sets: list[str]) -> None:
        self.level = level
        self.target_open_sets = target_open_sets

    def __repr__(self) -> str:
        return f"QueryClassification({self.level}, {len(self.target_open_sets)} open sets)"


class SheafOptimizer:
    """Query optimizer for the sheaf database.

    Classifies queries, selects optimal open sets, and manages the
    global section cache.
    """

    def __init__(
        self,
        openset_index: OpenSetIndex,
        context_index: ContextIndex,
        neighborhood_index: NeighborhoodIndex,
        temporal_index: TemporalIndex,
        provenance_index: ProvenanceIndex,
        restriction_graph: RestrictionGraph,
    ) -> None:
        self._openset_index = openset_index
        self._context_index = context_index
        self._neighborhood_index = neighborhood_index
        self._temporal_index = temporal_index
        self._provenance_index = provenance_index
        self._restriction_graph = restriction_graph
        self._cache_hits = 0
        self._cache_misses = 0

    def classify(self, query: Query) -> QueryClassification:
        """Classify a query as local, semi-local, or global.

        A query is **local** if its subject matches a specific entity
        that exists in a single stalk (direct point lookup).

        A query is **semi-local** if it can be answered from a
        related open set (same context, temporal window, provenance).

        A query is **global** if it requires full topology traversal
        (no constraints, MIXED type).
        """
        if query.query_type in (QueryType.LOOKUP,):
            opensets = self._classify_lookup(query)
            if opensets:
                return QueryClassification(QueryClassification.LOCAL, opensets[:1])

        if query.query_type in (QueryType.CONTEXT, QueryType.TEMPORAL, QueryType.PROVENANCE):
            opensets = self._classify_semilocal(query)
            if opensets:
                return QueryClassification(QueryClassification.SEMI_LOCAL, opensets)

        if query.query_type in (QueryType.NEIGHBORHOOD,):
            opensets = self._classify_neighborhood(query)
            if opensets:
                return QueryClassification(QueryClassification.SEMI_LOCAL, opensets)

        if query.query_type in (QueryType.GLOBAL, QueryType.MIXED, QueryType.AGGREGATION):
            opensets = list(self._openset_index._sets.keys())
            return QueryClassification(QueryClassification.GLOBAL, opensets)

        opensets = list(self._openset_index._sets.keys())
        level = QueryClassification.GLOBAL if len(opensets) > 5 else QueryClassification.SEMI_LOCAL
        return QueryClassification(level, opensets[:5])

    def _classify_lookup(self, query: Query) -> list[str]:
        result: list[str] = []
        if query.subject is not None:
            sid = query.subject.value
            opensets = self._openset_index.get_open_sets_for(sid)
            result.extend(opensets)
            entity_oset = f"entity:{sid}"
            if entity_oset in self._openset_index._sets:
                result.append(entity_oset)
        return list(set(result))

    def _classify_semilocal(self, query: Query) -> list[str]:
        result: list[str] = []
        if query.query_type == QueryType.CONTEXT and query.context:
            for fid in self._context_index.get_fact_ids(query.context):
                result.extend(self._openset_index.get_open_sets_for(fid))
        if query.query_type == QueryType.TEMPORAL and (query.temporal_start or query.temporal_end):
            for fid in self._temporal_candidate_fact_ids(query):
                result.extend(self._openset_index.get_open_sets_for(fid))
        if query.query_type == QueryType.PROVENANCE:
            for fid in self._provenance_index.get_by_source(query.context):
                result.extend(self._openset_index.get_open_sets_for(fid))
        return list(set(result))

    def _temporal_candidate_fact_ids(self, query: Query) -> set[str]:
        """Fact ids that could possibly satisfy a TEMPORAL query's range.

        A range bounded on both ends is narrowed to the year buckets it
        spans -- cheap, and already exact enough to be a tight candidate
        set. A range open on one end cannot be narrowed by year bucket (no
        later, or no earlier, year can be ruled out), so it is resolved
        directly against the flat, binary-searchable start/end arrays
        instead of falling back to every bucket the index has ever
        created.
        """
        if query.temporal_start and query.temporal_end:
            start_year = int(query.temporal_start[:4])
            end_year = int(query.temporal_end[:4])
            ids: set[str] = set()
            for year in range(start_year, end_year + 1):
                ids.update(self._temporal_index.get_fact_ids(str(year)))
            return ids
        if query.temporal_start:
            return set(self._temporal_index.facts_ending_after(parse_temporal_bound(query.temporal_start)))
        assert query.temporal_end is not None
        return set(self._temporal_index.facts_starting_before(parse_temporal_bound(query.temporal_end)))

    def _classify_neighborhood(self, query: Query) -> list[str]:
        result: list[str] = []
        if query.subject is not None:
            for fid in self._neighborhood_index.get_fact_ids(query.subject.value):
                result.extend(self._openset_index.get_open_sets_for(fid))
        return list(set(result))

    def cache_hit(self, fact_id: str) -> None:
        self._cache_hits += 1

    def cache_miss(self) -> None:
        self._cache_misses += 1

    def cache_hit_rate(self) -> float:
        total = self._cache_hits + self._cache_misses
        return self._cache_hits / total if total else 0.0

    def optimize(self, query: Query, classification: QueryClassification) -> list[str]:
        """Return the optimal set of open set names to query."""
        if classification.level == QueryClassification.LOCAL:
            return classification.target_open_sets[:1]
        candidates = list(classification.target_open_sets)
        seen: set[str] = set()
        deduped: list[str] = []
        for name in candidates:
            if name and name not in seen:
                deduped.append(name)
                seen.add(name)
        return deduped[:10]
