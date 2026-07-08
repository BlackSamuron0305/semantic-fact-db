"""Unit tests for the common type system.

Tests cover construction, equality, ordering, and hashing
of all base types.
"""

from sfdb.common.types import Context, Fact, Identifier, SemanticType, Value


class TestIdentifier:
    def test_construction(self) -> None:
        id1 = Identifier("test")
        assert id1.value == "test"

    def test_auto_generation(self) -> None:
        id1 = Identifier()
        id2 = Identifier()
        assert id1 != id2  # Distinct auto-generated IDs

    def test_equality(self) -> None:
        assert Identifier("a") == Identifier("a")
        assert Identifier("a") != Identifier("b")

    def test_ordering(self) -> None:
        assert Identifier("a") < Identifier("b")
        assert Identifier("b") > Identifier("a")

    def test_hashing(self) -> None:
        s = {Identifier("a"), Identifier("a"), Identifier("b")}
        assert len(s) == 2


class TestValue:
    def test_literal_string(self) -> None:
        v = Value.literal("hello")
        assert v.is_literal
        assert v.inner == "hello"
        assert v.type_hint == SemanticType.ATTRIBUTE

    def test_literal_int(self) -> None:
        v = Value.literal(42)
        assert v.is_literal
        assert v.inner == 42
        assert v.type_hint == SemanticType.QUANTITY

    def test_literal_bool(self) -> None:
        v = Value.literal(True)
        assert v.is_literal
        assert v.inner is True

    def test_reference(self) -> None:
        eid = Identifier("entity_1")
        v = Value.reference(eid)
        assert v.is_reference
        assert v.inner == eid

    def test_equality(self) -> None:
        assert Value.literal(1) == Value.literal(1)
        assert Value.literal(1) != Value.literal(2)


class TestContext:
    def test_construction(self) -> None:
        c = Context("a.b.c")
        assert c.segments == ("a", "b", "c")
        assert c.depth == 3

    def test_subcontext(self) -> None:
        broad = Context("world")
        narrow = Context("world.2024")
        assert narrow.is_subcontext(broad)
        assert not broad.is_subcontext(narrow)

    def test_ordering(self) -> None:
        broad = Context("world")
        narrow = Context("world.2024")
        assert narrow < broad
        assert broad > narrow

    def test_equality(self) -> None:
        assert Context("a.b") == Context("a.b")
        assert Context("a.b") != Context("a.c")


class TestFact:
    def test_construction(self) -> None:
        fact = Fact(
            id=Identifier("f1"),
            subject=Identifier("alice"),
            relation=Identifier("knows"),
            objects=(Value.reference(Identifier("bob")),),
        )
        assert fact.id.value == "f1"
        assert fact.arity() == 1

    def test_confidence_validation(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            Fact(
                id=Identifier("f1"),
                subject=Identifier("s"),
                relation=Identifier("r"),
                confidence=1.5,
            )
        with pytest.raises(ValueError):
            Fact(
                id=Identifier("f1"),
                subject=Identifier("s"),
                relation=Identifier("r"),
                confidence=-0.1,
            )

    def test_ordering(self) -> None:
        f1 = Fact(id=Identifier("a"), subject=Identifier("s"), relation=Identifier("r"))
        f2 = Fact(id=Identifier("b"), subject=Identifier("s"), relation=Identifier("r"))
        facts = sorted([f2, f1])
        assert facts[0].id == f1.id

    def test_frozen(self) -> None:
        fact = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r"))
        import pytest

        with pytest.raises(AttributeError):
            fact.subject = Identifier("x")  # type: ignore
