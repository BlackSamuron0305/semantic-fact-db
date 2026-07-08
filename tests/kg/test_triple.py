"""Tests for triple representation and decomposition."""

from sfdb.common.types import Fact, Identifier, Value
from sfdb.kg.triple import RDF_STATEMENT, RDF_TYPE, FactDecomposer, Triple, TripleStore


class TestTriple:
    def test_construction(self) -> None:
        t = Triple(
            subject=Identifier("s"),
            predicate=Identifier("p"),
            obj=Identifier("o"),
        )
        assert t.subject.value == "s"
        assert t.predicate.value == "p"

    def test_ordering(self) -> None:
        t1 = Triple(Identifier("a"), Identifier("p"), Identifier("o"))
        t2 = Triple(Identifier("b"), Identifier("p"), Identifier("o"))
        assert t1 < t2


class TestTripleStore:
    def test_add_and_query(self) -> None:
        store = TripleStore()
        t = Triple(Identifier("s"), Identifier("p"), Identifier("o"))
        store.add(t)
        results = store.query_sp(Identifier("s"), Identifier("p"))
        assert len(results) == 1
        assert results[0].obj == Identifier("o")

    def test_subject_query(self) -> None:
        store = TripleStore()
        store.add(Triple(Identifier("s1"), Identifier("p1"), Identifier("o1")))
        store.add(Triple(Identifier("s1"), Identifier("p2"), Identifier("o2")))
        results = store.query_s(Identifier("s1"))
        assert len(results) == 2

    def test_predicate_query(self) -> None:
        store = TripleStore()
        store.add(Triple(Identifier("s1"), Identifier("p1"), Identifier("o1")))
        store.add(Triple(Identifier("s2"), Identifier("p1"), Identifier("o2")))
        results = store.query_p(Identifier("p1"))
        assert len(results) == 2


class TestFactDecomposer:
    def test_decompose_binary(self) -> None:
        decomposer = FactDecomposer()
        fact = Fact(
            id=Identifier("f1"),
            subject=Identifier("alice"),
            relation=Identifier("knows"),
            objects=(Value.reference(Identifier("bob")),),
        )
        triples = decomposer.decompose(fact)
        # Each fact becomes: type + subject + predicate + (1 object) = 4 triples
        assert len(triples) == 4

        # Check structural triples
        assert triples[0].predicate == RDF_TYPE
        assert triples[0].obj == RDF_STATEMENT

    def test_decompose_ternary(self) -> None:
        decomposer = FactDecomposer()
        fact = Fact(
            id=Identifier("f1"),
            subject=Identifier("alice"),
            relation=Identifier("gave"),
            objects=(
                Value.reference(Identifier("bob")),
                Value.reference(Identifier("book")),
            ),
        )
        triples = decomposer.decompose(fact)
        # type + subject + predicate + 2 objects = 5 triples
        assert len(triples) == 5

    def test_reconstruct(self) -> None:
        decomposer = FactDecomposer()
        store = TripleStore()
        original = Fact(
            id=Identifier("f1"),
            subject=Identifier("alice"),
            relation=Identifier("knows"),
            objects=(Value.reference(Identifier("bob")),),
        )
        triples = decomposer.decompose(original)
        for t in triples:
            store.add(t)
        reconstructed = decomposer.reconstruct(triples, store)
        assert reconstructed is not None
        assert reconstructed.subject == original.subject
        assert reconstructed.relation == original.relation
