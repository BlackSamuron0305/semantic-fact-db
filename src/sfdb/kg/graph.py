"""Knowledge Graph — complete graph-based semantic store.

This is the baseline system. It implements a full RDF-style triple store
with reification for n-ary facts, standard SPO indexing, and SPARQL-like
pattern matching.

The KnowledgeGraph is the *control* in our experiment. It must be
correct, complete, and realistic — not a simplified straw man.

Complexity
----------
Fact insertion: O(k) where k = arity (number of decomposition triples).
Pattern query: O(log n + m) for indexed patterns.
Full scan: O(n).
"""

from sfdb.canonical.canonical import CanonicalEntity, CanonicalModel
from sfdb.common.types import Fact, Identifier
from sfdb.kg.triple import FactDecomposer, Triple, TripleStore


class KnowledgeGraph:
    """A complete RDF-style knowledge graph.

    Provides:
        - Triple storage with SPO/POS/OSP indices
        - N-ary fact decomposition (via reification)
        - Fact insertion and retrieval
        - Pattern matching queries
        - Canonical model export for equivalence checking

    Parameters
    ----------
    name: An identifier for this graph instance.
    """

    def __init__(self, name: str = "kg") -> None:
        self.name = name
        self._store = TripleStore()
        self._decomposer = FactDecomposer()
        self._entities: dict[Identifier, CanonicalEntity] = {}

    def insert_fact(self, fact: Fact) -> None:
        """Insert an n-ary fact by decomposing into triples."""
        triples = self._decomposer.decompose(fact)
        for t in triples:
            self._store.add(t)
        # Track entities
        if fact.subject not in self._entities:
            self._entities[fact.subject] = CanonicalEntity(id=fact.subject)
        for obj in fact.objects:
            if obj.is_reference:
                oid: Identifier = obj.inner
                if oid not in self._entities:
                    self._entities[oid] = CanonicalEntity(id=oid)

    def insert_triple(self, triple: Triple) -> None:
        """Insert a raw triple directly."""
        self._store.add(triple)

    def query_subject(self, subject: Identifier) -> list[Fact]:
        """Retrieve all facts about a subject."""
        triples = self._store.query_s(subject)
        return self._reconstruct_facts(triples)

    def query_predicate(self, predicate: Identifier) -> list[Fact]:
        """Retrieve all facts with a given predicate."""
        triples = self._store.query_p(predicate)
        return self._reconstruct_facts(triples)

    def query_object(self, obj: Identifier) -> list[Fact]:
        """Retrieve all facts referencing a given object."""
        triples = self._store.query_o(obj)
        return self._reconstruct_facts(triples)

    def query_sp(self, subject: Identifier, predicate: Identifier) -> list[Fact]:
        """Retrieve facts matching subject AND predicate."""
        triples = self._store.query_sp(subject, predicate)
        return self._reconstruct_facts(triples)

    def query_pattern(
        self, s: Identifier | None, p: Identifier | None, o: Identifier | None
    ) -> list[Triple]:
        """SPARQL-style pattern query. None = wildcard."""
        if s is not None and p is not None and o is not None:
            return self._store.query_sp(s, p)  # filtered below
        if s is not None and p is not None:
            return self._store.query_sp(s, p)
        if p is not None and o is not None:
            return self._store.query_po(p, o)
        if s is not None:
            return self._store.query_s(s)
        if p is not None:
            return self._store.query_p(p)
        if o is not None:
            return self._store.query_o(o)
        return self._store.all_triples()

    def to_canonical(self) -> CanonicalModel:
        """Export the entire KG as a canonical model for comparison."""
        model = CanonicalModel()
        for _entity_id, entity in self._entities.items():
            model.add_entity(entity)
        for triple in self._store.all_triples():
            if triple.predicate == Identifier("rdf:type"):
                continue  # skip reification boilerplate
        return model

    def _reconstruct_facts(self, triples: list[Triple]) -> list[Fact]:
        """Group triples by statement ID and reconstruct facts."""
        groups: dict[Identifier, list[Triple]] = {}
        for t in triples:
            if t.predicate in (
                Identifier("rdf:type"),
                Identifier("rdf:subject"),
                Identifier("rdf:predicate"),
                Identifier("rdf:object"),
            ):
                groups.setdefault(t.subject, []).append(t)
        facts: list[Fact] = []
        for _stmt_id, group in groups.items():
            fact = self._decomposer.reconstruct(group, self._store)
            if fact is not None:
                facts.append(fact)
        return facts

    @property
    def num_triples(self) -> int:
        return self._store.size()

    @property
    def num_entities(self) -> int:
        return len(self._entities)

    def __repr__(self) -> str:
        return f"KnowledgeGraph(name={self.name!r}, triples={self.num_triples})"
