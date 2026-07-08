"""Query engine for the Knowledge Graph.

Implements pattern matching and basic graph traversal queries
that serve as the baseline for comparison against the Sheaf DB.

Query types
-----------
1. Subject lookup: all facts about entity e
2. Predicate lookup: all facts with relation r
3. SP pattern: facts matching (s, p)
4. Walk: traverse from entity along relation to connected entities
5. Join: find entities connected through intermediate entities

Complexity
----------
Subject lookup: O(log n + k) where k = number of facts about subject.
Join: O(n · m) worst case for unfiltered joins.
Walk: O(d) where d = degree of the starting entity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sfdb.common.types import Context, Fact, Identifier
from sfdb.kg.graph import KnowledgeGraph


@dataclass(slots=True, frozen=True)
class KGQuery:
    """A query against the Knowledge Graph.

    Parameters
    ----------
    subject: Subject to match (None = wildcard).
    predicate: Predicate to match (None = wildcard).
    obj: Object to match (None = wildcard).
    context: Optional context filter.
    limit: Maximum results to return (0 = unlimited).
    """

    subject: Identifier | None = None
    predicate: Identifier | None = None
    obj: Identifier | None = None
    context: Context | None = None
    limit: int = 0


@dataclass(slots=True)
class KGQueryResult:
    """The result of a KG query.

    Attributes
    ----------
    facts: Matching facts (reconstructed from triples).
    triples: Raw matching triples.
    num_triples_scanned: How many triples were examined.
    num_triples_returned: How many triples matched.
    """

    facts: list[Fact] = field(default_factory=list)
    triples: list[Any] = field(default_factory=list)
    num_triples_scanned: int = 0
    num_triples_returned: int = 0


class KGQueryEngine:
    """Query engine executing KGQuery against a KnowledgeGraph."""

    def __init__(self, graph: KnowledgeGraph) -> None:
        self._graph = graph

    def execute(self, query: KGQuery) -> KGQueryResult:
        """Execute a query and return results."""
        all_triples = self._graph.query_pattern(query.subject, query.predicate, query.obj)
        result = KGQueryResult()
        result.triples = all_triples
        result.num_triples_scanned = self._graph.num_triples
        result.num_triples_returned = len(all_triples)
        # Reconstruct facts from matching triples
        result.facts = self._graph._reconstruct_facts(all_triples)
        return result

    def walk(self, start: Identifier, relation: Identifier, max_depth: int = 1) -> list[Fact]:
        """Traverse the graph from *start* along *relation*.

        Breadth-first traversal up to max_depth.
        """
        visited: set[Identifier] = {start}
        current: set[Identifier] = {start}
        results: list[Fact] = []

        for _ in range(max_depth):
            next_set: set[Identifier] = set()
            for entity in current:
                facts = self._graph.query_sp(entity, relation)
                results.extend(facts)
                for fact in facts:
                    for obj in fact.objects:
                        if obj.is_reference:
                            oid = obj.inner
                            if oid not in visited:
                                visited.add(oid)
                                next_set.add(oid)
            current = next_set
            if not current:
                break

        return results

    def join(self, entities: list[Identifier], relation: Identifier) -> list[Fact]:
        """Find facts where *relation* connects any pair in *entities*."""
        results: list[Fact] = []
        entity_set = set(entities)
        for e in entities:
            facts = self._graph.query_sp(e, relation)
            for fact in facts:
                for obj in fact.objects:
                    if obj.is_reference and obj.inner in entity_set:
                        results.append(fact)
                        break
        return results
