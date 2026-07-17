"""Indexes for the sheaf database.

Each index maps a key type to the set of fact IDs (points) relevant
to that key.  Unlike the KG's triple indexes, sheaf indexes map
semantic keys directly to LocalSections without decomposition.

Indexes:
- OpenSetIndex:   open set name → fact IDs (primary index)
- StalkIndex:     point ID → stalk
- RestrictionIndex:  (source, target) → restriction count
- ContextIndex:   context string → fact IDs
- NeighborhoodIndex:  entity ref → fact IDs
- TemporalIndex:  year → fact IDs
- ProvenanceIndex:  source/method → fact IDs
- GlobalSectionCache: fact ID → GlobalSection
"""

from __future__ import annotations

from collections import defaultdict

from common.schema import SemanticFact
from sfdb.sheaf.presheaf import GlobalSection, LocalSection, Stalk


class OpenSetIndex:
    """Maps open set names to the fact IDs they contain.

    Primary index used by the query planner to locate sections.
    """

    def __init__(self) -> None:
        self._sets: dict[str, set[str]] = {}
        self._sets_by_fact: dict[str, set[str]] = defaultdict(set)

    def add(self, open_set_name: str, fact_id: str) -> None:
        if open_set_name not in self._sets:
            self._sets[open_set_name] = set()
        self._sets[open_set_name].add(fact_id)
        self._sets_by_fact[fact_id].add(open_set_name)

    def get_fact_ids(self, open_set_name: str) -> frozenset[str]:
        return frozenset(self._sets.get(open_set_name, set()))

    def get_open_sets_for(self, fact_id: str) -> list[str]:
        return list(self._sets_by_fact.get(fact_id, ()))

    def remove(self, fact_id: str) -> None:
        for name in self._sets_by_fact.pop(fact_id, ()):
            self._sets[name].discard(fact_id)

    def count(self) -> int:
        return sum(len(ids) for ids in self._sets.values())

    def __repr__(self) -> str:
        return f"OpenSetIndex({len(self._sets)} sets, {self.count()} entries)"


class StalkIndex:
    """Maps point IDs to their Stalks.

    A stalk F_x contains all LocalSections whose fact ID is *x*,
    accessible from any open set containing *x*.
    """

    def __init__(self) -> None:
        self._stalks: dict[str, Stalk] = {}

    def get_or_create(self, point_id: str) -> Stalk:
        if point_id not in self._stalks:
            self._stalks[point_id] = Stalk(point_id)
        return self._stalks[point_id]

    def get(self, point_id: str) -> Stalk | None:
        return self._stalks.get(point_id)

    def add_section(self, section: LocalSection) -> None:
        stalk = self.get_or_create(section.fact.id.value)
        stalk.add_section(section)

    def remove(self, point_id: str) -> None:
        self._stalks.pop(point_id, None)

    def count(self) -> int:
        return len(self._stalks)

    def all_stalks(self) -> list[Stalk]:
        return list(self._stalks.values())

    def __repr__(self) -> str:
        total_sections = sum(s.section_count for s in self._stalks.values())
        return f"StalkIndex({self.count()} stalks, {total_sections} sections)"


class RestrictionIndex:
    """Tracks restriction map metadata.

    Records how many times each restriction (source → target) has
    been applied, enabling cache-hit analysis.
    """

    def __init__(self) -> None:
        self._applied: dict[tuple[str, str], int] = defaultdict(int)
        self._timing: dict[tuple[str, str], int] = {}

    def record(self, source: str, target: str, time_ns: int = 0) -> None:
        key = (source, target)
        self._applied[key] += 1
        if time_ns > 0:
            self._timing[key] = self._timing.get(key, 0) + time_ns

    def application_count(self, source: str, target: str) -> int:
        return self._applied.get((source, target), 0)

    def total_applications(self) -> int:
        return sum(self._applied.values())

    def avg_time_ns(self, source: str, target: str) -> float:
        key = (source, target)
        cnt = self._applied.get(key, 0)
        t = self._timing.get(key, 0)
        return t / cnt if cnt else 0.0

    def __repr__(self) -> str:
        return f"RestrictionIndex({self.total_applications()} total applications)"


class ContextIndex:
    """Maps context strings to fact IDs.

    Enables context-scoped queries without full set enumeration.
    """

    def __init__(self) -> None:
        self._ctx_to_facts: dict[str, set[str]] = defaultdict(set)
        self._fact_to_ctxs: dict[str, set[str]] = defaultdict(set)

    def add(self, context_str: str, fact_id: str) -> None:
        self._ctx_to_facts[context_str].add(fact_id)
        self._fact_to_ctxs[fact_id].add(context_str)

    def get_fact_ids(self, context_str: str) -> frozenset[str]:
        return frozenset(self._ctx_to_facts.get(context_str, set()))

    def get_contexts(self, fact_id: str) -> list[str]:
        return list(self._fact_to_ctxs.get(fact_id, set()))

    def remove(self, fact_id: str) -> None:
        for ctxs in self._fact_to_ctxs.pop(fact_id, set()):
            self._ctx_to_facts.get(ctxs, set()).discard(fact_id)

    def count(self) -> int:
        return sum(len(ids) for ids in self._ctx_to_facts.values())

    def __repr__(self) -> str:
        return f"ContextIndex({len(self._ctx_to_facts)} contexts, {self.count()} entries)"


class NeighborhoodIndex:
    """Maps entity references to fact IDs.

    Enables entity adjacency queries — find all facts that reference
    a given entity.
    """

    def __init__(self) -> None:
        self._entity_to_facts: dict[str, set[str]] = defaultdict(set)

    def add(self, entity_ref: str, fact_id: str) -> None:
        self._entity_to_facts[entity_ref].add(fact_id)

    def index_fact(self, fact: SemanticFact) -> None:
        self._entity_to_facts[fact.subject.value].add(fact.id.value)
        for obj in fact.objects:
            if obj.is_reference and obj.inner is not None:
                self._entity_to_facts[str(obj.inner)].add(fact.id.value)

    def get_fact_ids(self, entity_ref: str) -> frozenset[str]:
        return frozenset(self._entity_to_facts.get(entity_ref, set()))

    def remove(self, fact_id: str) -> None:
        for ids in self._entity_to_facts.values():
            ids.discard(fact_id)

    def count(self) -> int:
        return sum(len(ids) for ids in self._entity_to_facts.values())

    def __repr__(self) -> str:
        return f"NeighborhoodIndex({len(self._entity_to_facts)} entities, {self.count()} entries)"


class TemporalIndex:
    """Maps temporal intervals to fact IDs.

    Supports year-based and range-based temporal queries.
    """

    def __init__(self) -> None:
        self._year_to_facts: dict[str, set[str]] = defaultdict(set)

    def add(self, year: str, fact_id: str) -> None:
        self._year_to_facts[year].add(fact_id)

    def index_fact(self, fact: SemanticFact) -> None:
        if fact.temporal is not None and fact.temporal.start is not None:
            self._year_to_facts[str(fact.temporal.start.year)].add(fact.id.value)
        else:
            self._year_to_facts["atemporal"].add(fact.id.value)

    def get_fact_ids(self, year: str) -> frozenset[str]:
        return frozenset(self._year_to_facts.get(year, set()))

    def years(self) -> list[str]:
        return list(self._year_to_facts.keys())

    def count(self) -> int:
        return sum(len(ids) for ids in self._year_to_facts.values())

    def __repr__(self) -> str:
        return f"TemporalIndex({len(self._year_to_facts)} years, {self.count()} entries)"


class ProvenanceIndex:
    """Maps provenance sources and methods to fact IDs."""

    def __init__(self) -> None:
        self._source_to_facts: dict[str, set[str]] = defaultdict(set)
        self._method_to_facts: dict[str, set[str]] = defaultdict(set)

    def index_fact(self, fact: SemanticFact) -> None:
        self._source_to_facts[fact.provenance.source].add(fact.id.value)
        self._method_to_facts[fact.provenance.method].add(fact.id.value)

    def get_by_source(self, source: str) -> frozenset[str]:
        return frozenset(self._source_to_facts.get(source, set()))

    def get_by_method(self, method: str) -> frozenset[str]:
        return frozenset(self._method_to_facts.get(method, set()))

    def count(self) -> int:
        return sum(len(ids) for ids in self._source_to_facts.values())

    def __repr__(self) -> str:
        return f"ProvenanceIndex({len(self._source_to_facts)} sources, {self.count()} entries)"


class GlobalSectionCache:
    """Cache for computed global sections.

    Avoids recomputing global sections unless open sets change.
    """

    def __init__(self) -> None:
        self._sections: dict[str, GlobalSection] = {}
        self._version: int = 0

    def invalidate(self) -> None:
        self._sections.clear()
        self._version += 1

    def add(self, section: GlobalSection) -> None:
        self._sections[section.fact.id.value] = section

    def get(self, fact_id: str) -> GlobalSection | None:
        return self._sections.get(fact_id)

    def has(self, fact_id: str) -> bool:
        return fact_id in self._sections

    def list_all(self) -> list[GlobalSection]:
        return list(self._sections.values())

    def count(self) -> int:
        return len(self._sections)

    def version(self) -> int:
        return self._version

    def __repr__(self) -> str:
        return f"GlobalSectionCache({self.count()} cached, version {self._version})"
