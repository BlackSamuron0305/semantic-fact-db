"""Topology builder — constructs finite topologies from SemanticFacts.

Given a set of SemanticFacts, the topology builder creates a
FiniteTopologicalSpace whose open sets group facts by shared
semantic properties:

- **Event topology**: each fact defines its own minimal open set
- **Entity topology**: facts sharing a subject/object entity
- **Temporal topology**: facts overlapping a time window
- **Contextual topology**: facts in related contexts
- **Provenance topology**: facts from the same provenance source
- **Neighborhood topology**: facts connected by entity reference
"""

from __future__ import annotations

from collections import defaultdict
from enum import Enum, auto

from common.schema import SemanticFact
from sfdb.sheaf.topology import FiniteTopologicalSpace, OpenSet


class TopologyStrategy(Enum):
    """Strategy for building the finite topology from facts."""

    EVENT_CENTRIC = auto()
    ENTITY_CENTRIC = auto()
    TEMPORAL = auto()
    CONTEXTUAL = auto()
    PROVENANCE = auto()
    NEIGHBORHOOD = auto()
    FULL = auto()


class TopologyBuilder:
    """Constructs a FiniteTopologicalSpace from SemanticFacts.

    Usage::

        builder = TopologyBuilder(strategy=TopologyStrategy.FULL)
        topology = builder.build(facts)

    The FULL strategy creates open sets of every kind and takes the
    intersection closure.
    """

    def __init__(self, strategy: TopologyStrategy = TopologyStrategy.FULL) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> TopologyStrategy:
        return self._strategy

    def build(self, facts: list[SemanticFact]) -> FiniteTopologicalSpace:
        """Build a finite topology from a list of SemanticFacts.

        Returns a FiniteTopologicalSpace with open sets determined
        by the chosen strategy.
        """
        topology = FiniteTopologicalSpace()

        empty_set = OpenSet("∅", frozenset())
        topology.add_open_set(empty_set)

        all_points: set[str] = set()
        for fact in facts:
            all_points.add(fact.id.value)

        universe = OpenSet("𝕌", frozenset(all_points))
        topology.add_open_set(universe)

        strategy = self._strategy
        if strategy == TopologyStrategy.EVENT_CENTRIC or strategy == TopologyStrategy.FULL:
            self._build_event_sets(topology, facts)
        if strategy == TopologyStrategy.ENTITY_CENTRIC or strategy == TopologyStrategy.FULL:
            self._build_entity_sets(topology, facts)
        if strategy == TopologyStrategy.TEMPORAL or strategy == TopologyStrategy.FULL:
            self._build_temporal_sets(topology, facts)
        if strategy == TopologyStrategy.CONTEXTUAL or strategy == TopologyStrategy.FULL:
            self._build_context_sets(topology, facts)
        if strategy == TopologyStrategy.PROVENANCE or strategy == TopologyStrategy.FULL:
            self._build_provenance_sets(topology, facts)
        if strategy == TopologyStrategy.NEIGHBORHOOD or strategy == TopologyStrategy.FULL:
            self._build_neighborhood_sets(topology, facts)

        topology.intersection_closure()
        return topology

    def _build_event_sets(
        self, topology: FiniteTopologicalSpace, facts: list[SemanticFact]
    ) -> None:
        """Each fact gets its own event open set (atomic event neighborhood).

        Rationale: each semantic fact is a complete event.  The event
        open set is the smallest possible neighborhood — it contains
        only that single fact.
        """
        for fact in facts:
            os = OpenSet(
                name=f"event:{fact.id.value}",
                points=frozenset({fact.id.value}),
                metadata={"type": "event", "relation": fact.relation.value},
            )
            topology.add_open_set(os)

    def _build_entity_sets(
        self, topology: FiniteTopologicalSpace, facts: list[SemanticFact]
    ) -> None:
        """Group facts by subject entity.

        Rationale: facts about the same entity belong together.  An
        entity open set collects all facts whose subject is a given
        entity, enabling entity-centric queries.
        """
        entity_groups: dict[str, set[str]] = defaultdict(set)
        for fact in facts:
            entity_groups[fact.subject.value].add(fact.id.value)
            for obj in fact.objects:
                if obj.is_reference and obj.inner is not None:
                    entity_groups[str(obj.inner)].add(fact.id.value)
        for entity_id, fact_ids in entity_groups.items():
            os = OpenSet(
                name=f"entity:{entity_id}",
                points=frozenset(fact_ids),
                metadata={"type": "entity", "entity_id": entity_id},
            )
            topology.add_open_set(os)

    def _build_temporal_sets(
        self, topology: FiniteTopologicalSpace, facts: list[SemanticFact]
    ) -> None:
        """Group facts by temporal proximity.

        Rationale: facts valid during the same time window form a
        temporal neighborhood.  Facts without temporal info are
        assigned to an "atemporal" open set.
        """
        temporal_groups: dict[str, set[str]] = defaultdict(set)
        atemporal: set[str] = set()
        for fact in facts:
            if fact.temporal is not None and fact.temporal.start is not None:
                year = str(fact.temporal.start.year)
                temporal_groups[year].add(fact.id.value)
            else:
                atemporal.add(fact.id.value)
        for year, fact_ids in temporal_groups.items():
            os = OpenSet(
                name=f"temporal:{year}",
                points=frozenset(fact_ids),
                metadata={"type": "temporal", "year": year},
            )
            topology.add_open_set(os)
        if atemporal:
            topology.add_open_set(
                OpenSet(
                    name="temporal:atemporal",
                    points=frozenset(atemporal),
                    metadata={"type": "temporal", "year": "none"},
                )
            )

    def _build_context_sets(
        self, topology: FiniteTopologicalSpace, facts: list[SemanticFact]
    ) -> None:
        """Group facts by context.

        Rationale: facts in the same context (or sub-context) form a
        contextual neighborhood.  Contexts form a poset, giving a
        natural restriction structure.
        """
        context_groups: dict[str, set[str]] = defaultdict(set)
        for fact in facts:
            ctx_str = str(fact.context)
            context_groups[ctx_str].add(fact.id.value)
            parts = ctx_str.split(".")
            for i in range(1, len(parts)):
                parent = ".".join(parts[:i])
                context_groups[parent].add(fact.id.value)
        for ctx_name, fact_ids in context_groups.items():
            os = OpenSet(
                name=f"context:{ctx_name}",
                points=frozenset(fact_ids),
                metadata={"type": "context", "context": ctx_name},
            )
            topology.add_open_set(os)

    def _build_provenance_sets(
        self, topology: FiniteTopologicalSpace, facts: list[SemanticFact]
    ) -> None:
        """Group facts by provenance source.

        Rationale: facts from the same source share trust assumptions,
        extraction methods, and quality characteristics.
        """
        source_groups: dict[str, set[str]] = defaultdict(set)
        method_groups: dict[str, set[str]] = defaultdict(set)
        for fact in facts:
            source_groups[fact.provenance.source].add(fact.id.value)
            method_groups[fact.provenance.method].add(fact.id.value)
        for source, fact_ids in source_groups.items():
            os = OpenSet(
                name=f"provenance:source:{source}",
                points=frozenset(fact_ids),
                metadata={"type": "provenance", "source": source},
            )
            topology.add_open_set(os)
        for method, fact_ids in method_groups.items():
            os = OpenSet(
                name=f"provenance:method:{method}",
                points=frozenset(fact_ids),
                metadata={"type": "provenance", "method": method},
            )
            topology.add_open_set(os)

    def _build_neighborhood_sets(
        self, topology: FiniteTopologicalSpace, facts: list[SemanticFact]
    ) -> None:
        """Build open sets by entity reference connectivity.

        Rationale: facts that reference the same entities are
        topologically close.  This creates neighborhoods based on
        the semantic graph structure.
        """
        all_points = {f.id.value for f in facts}
        neighborhood = OpenSet(
            name="neighborhood:all",
            points=frozenset(all_points),
            metadata={"type": "neighborhood"},
        )
        topology.add_open_set(neighborhood)
        fact_map = {f.id.value: f for f in facts}
        for fid, fact in fact_map.items():
            connected: set[str] = {fid}
            for obj in fact.objects:
                if obj.is_reference and obj.inner is not None:
                    ref_id = str(obj.inner)
                    connected.add(ref_id)
            for other_fid, other_fact in fact_map.items():
                if other_fid == fid:
                    continue
                for obj in other_fact.objects:
                    if (
                        obj.is_reference
                        and obj.inner is not None
                        and str(obj.inner) == fact.subject.value
                    ):
                        connected.add(other_fid)
            if len(connected) > 1:
                os = OpenSet(
                    name=f"neighborhood:entity:{fact.subject.value[:8]}",
                    points=frozenset(connected),
                    metadata={"type": "neighborhood", "center": fact.subject.value},
                )
                topology.add_open_set(os)
