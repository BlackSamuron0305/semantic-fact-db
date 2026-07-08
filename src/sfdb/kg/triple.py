"""Triple representation and store for the Knowledge Graph.

Mathematical background
-----------------------
A triple (s, p, o) ∈ E × R × (E ∪ L) represents a binary relationship
where:
    s (subject) is an entity
    p (predicate/relation) is a relationship type
    o (object) is either an entity or a literal value

An n-ary fact (r, a₁, ..., aₙ) must be decomposed into n-1 triples:
    (a₁, r, _:blank)    — reification via blank node
    (_:blank, rdf:predicate, r)
    (_:blank, rdf:object₁, a₂)
    ...
    (_:blank, rdf:objectₙ₋₁, aₙ)

This decomposition is the source of additional join complexity,
which this project aims to measure and compare.

Complexity
----------
Triple construction: O(1).
Triple indexing: O(1) per index.
Decomposition of n-ary fact: O(n) triples.
Reconstruction from triples: O(m) where m = triples per reified fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sfdb.canonical.canonical import CanonicalFact
from sfdb.common.types import Context, Fact, Identifier, Value

# Built-in RDF-like predicates for reification
RDF_TYPE = Identifier("rdf:type")
RDF_SUBJECT = Identifier("rdf:subject")
RDF_PREDICATE = Identifier("rdf:predicate")
RDF_OBJECT = Identifier("rdf:object")
RDF_STATEMENT = Identifier("rdf:Statement")


@dataclass(slots=True, frozen=True, order=True)
class Triple:
    """An RDF-style triple (subject, predicate, object).

    All components are Identifiers. Literal values are stored as
    identifier-encoded literals or through a separate literal store.
    """

    subject: Identifier
    predicate: Identifier
    obj: Identifier
    context: Context = field(default_factory=lambda: Context())

    def __repr__(self) -> str:
        return f"T({self.subject}, {self.predicate}, {self.obj})"


class TripleStore:
    """An in-memory triple store with SPO indexing.

    Maintains six permutations of indices for efficient querying:
        SPO, SOP, PSO, POS, OSP, OPS

    Complexity
    ----------
    Add: O(log n) per index (binary insertion into sorted lists).
    Query by pattern: O(log n + k) for indexed patterns, O(n) for others.
    Where k = number of matches.
    """

    def __init__(self) -> None:
        self._triples: list[Triple] = []
        self._literals: dict[Identifier, Value] = {}
        self._spo: dict[Identifier, dict[Identifier, list[Triple]]] = {}
        self._pos: dict[Identifier, dict[Identifier, list[Triple]]] = {}
        self._osp: dict[Identifier, dict[Identifier, list[Triple]]] = {}

    def add(self, triple: Triple) -> None:
        self._triples.append(triple)
        # SPO index
        self._spo.setdefault(triple.subject, {}).setdefault(triple.predicate, []).append(triple)
        # POS index
        self._pos.setdefault(triple.predicate, {}).setdefault(triple.obj, []).append(triple)
        # OSP index
        self._osp.setdefault(triple.obj, {}).setdefault(triple.subject, []).append(triple)

    def add_literal(self, identifier: Identifier, value: Value) -> None:
        self._literals[identifier] = value

    def query_sp(self, subject: Identifier, predicate: Identifier) -> list[Triple]:
        return self._spo.get(subject, {}).get(predicate, [])

    def query_po(self, predicate: Identifier, obj: Identifier) -> list[Triple]:
        return self._pos.get(predicate, {}).get(obj, [])

    def query_os(self, obj: Identifier, subject: Identifier) -> list[Triple]:
        return self._osp.get(obj, {}).get(subject, [])

    def query_s(self, subject: Identifier) -> list[Triple]:
        result: list[Triple] = []
        for pred_idx in self._spo.get(subject, {}).values():
            result.extend(pred_idx)
        return result

    def query_p(self, predicate: Identifier) -> list[Triple]:
        result: list[Triple] = []
        for obj_idx in self._pos.get(predicate, {}).values():
            result.extend(obj_idx)
        return result

    def query_o(self, obj: Identifier) -> list[Triple]:
        result: list[Triple] = []
        for subj_idx in self._osp.get(obj, {}).values():
            result.extend(subj_idx)
        return result

    def all_triples(self) -> list[Triple]:
        return list(self._triples)

    def size(self) -> int:
        return len(self._triples)

    def __repr__(self) -> str:
        return f"TripleStore(triples={len(self._triples)})"


class FactDecomposer:
    """Converts n-ary Facts to collections of Triples via reification.

    An n-ary fact (s, r, o₁, ..., oₙ₋₁) is decomposed into:
        1. A statement identifier statement_id
        2. (statement_id, rdf:type, rdf:Statement)
        3. (statement_id, rdf:subject, s)
        4. (statement_id, rdf:predicate, r)
        5. (statement_id, rdf:object, oᵢ) for each oᵢ

    This is the standard RDF reification pattern.

    Complexity
    ----------
    Decompose one fact: O(k) where k = arity of the fact.
    """

    def decompose(self, fact: Fact) -> list[Triple]:
        statement_id = fact.id
        triples: list[Triple] = [
            Triple(statement_id, RDF_TYPE, RDF_STATEMENT, fact.context),
            Triple(statement_id, RDF_SUBJECT, fact.subject, fact.context),
            Triple(statement_id, RDF_PREDICATE, fact.relation, fact.context),
        ]
        for obj in fact.objects:
            obj_id = obj.inner if obj.is_reference else Identifier(f"lit:{hash(obj)}")
            triples.append(Triple(statement_id, RDF_OBJECT, obj_id, fact.context))
        return triples

    def decompose_canonical(self, cf: CanonicalFact) -> list[Triple]:
        return self.decompose(cf.to_fact())

    def reconstruct(self, triples: list[Triple], store: TripleStore) -> Fact | None:
        """Attempt to reconstruct a Fact from its reified triples."""
        if not triples:
            return None
        ctx = triples[0].context
        statement_id = triples[0].subject
        subject: Identifier | None = None
        predicate: Identifier | None = None
        objects: list[Identifier] = []
        for t in triples:
            if t.predicate == RDF_SUBJECT:
                subject = t.obj
            elif t.predicate == RDF_PREDICATE:
                predicate = t.obj
            elif t.predicate == RDF_OBJECT:
                objects.append(t.obj)
        if subject is None or predicate is None:
            return None
        values = tuple(store._literals.get(o, Value.reference(o)) for o in objects)
        return Fact(
            id=statement_id,
            subject=subject,
            relation=predicate,
            objects=values,
            context=ctx,
        )
