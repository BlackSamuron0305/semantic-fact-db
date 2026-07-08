"""Tests for the sheaf database implementation."""

from sfdb.common.types import Context, Fact, Identifier, Value
from sfdb.sheaf.sheaf import ContextPoset, GluingError, Presheaf, Section, Sheaf, SheafStore


class TestContextPoset:
    def test_add_and_contains(self) -> None:
        poset = ContextPoset()
        c = Context("a.b")
        poset.add(c)
        assert poset.contains(c)
        assert not poset.contains(Context("x.y"))

    def test_root(self) -> None:
        poset = ContextPoset()
        poset.add(Context("a.b"))
        poset.add(Context("a"))
        assert poset.root == Context("a")

    def test_cover(self) -> None:
        poset = ContextPoset()
        poset.add(Context("world"))
        poset.add(Context("world.2024"))
        poset.add(Context("world.2024.science"))
        cover = poset.cover(Context("world"))
        assert Context("world.2024") in cover

    def test_join(self) -> None:
        poset = ContextPoset()
        c1 = Context("a.b.c")
        c2 = Context("a.b.d")
        result = poset.join(c1, c2)
        assert result == Context("a.b")

    def test_meet(self) -> None:
        poset = ContextPoset()
        c1 = Context("a.b")
        c2 = Context("a.b.c")
        assert poset.meet(c1, c2) == Context("a.b.c")  # The deeper one


class TestPresheaf:
    def test_assign_and_retrieve(self) -> None:
        sheaf = Presheaf()
        fact = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r"))
        section = Section(fact=fact, context=Context("world"))
        sheaf.assign(section)
        sections = sheaf.sections_over(Context("world"))
        assert len(sections) == 1
        assert sections[0].fact == fact

    def test_sections_local_to(self) -> None:
        sheaf = Presheaf()
        fact = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r"))
        sheaf.assign(Section(fact=fact, context=Context("world.2024")))

        # Should find the fact when querying from a broader context
        local = sheaf.sections_local_to(Context("world.2024"))
        assert len(local) == 1

    def test_restrict(self) -> None:
        sheaf = Presheaf()
        fact = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r"))
        section = Section(fact=fact, context=Context("world"))
        restricted = sheaf.restrict(section, Context("world.2024"))
        assert restricted is not None
        assert restricted.context == Context("world.2024")

    def test_restrict_wrong_direction(self) -> None:
        sheaf = Presheaf()
        fact = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r"))
        section = Section(fact=fact, context=Context("world.2024"))
        # Cannot restrict to a broader context
        restricted = sheaf.restrict(section, Context("world"))
        assert restricted is None


class TestSheaf:
    def test_glue_valid(self) -> None:
        sheaf = Sheaf()
        ctx = Context("world")

        # Create two sub-contexts
        c1 = Context("world.2024")
        c2 = Context("world.2025")

        fact = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r"))
        sheaf.assign(Section(fact=fact, context=c1))
        sheaf.assign(Section(fact=fact, context=c2))

        # Both agree on overlap (same fact), so gluing should work
        covering = {
            c1: Section(fact=fact, context=c1),
            c2: Section(fact=fact, context=c2),
        }
        glued = sheaf.glue(ctx, covering)
        assert glued.context == ctx
        assert glued.fact.subject == fact.subject

    def test_glue_conflict(self) -> None:
        sheaf = Sheaf()
        # c2 is a sub-context of c1, so the overlap is c2.
        c1 = Context("world")  # broader
        c2 = Context("world.2024")  # narrower — this is the overlap

        fact1 = Fact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            objects=(Value.literal(1),),
        )
        fact2 = Fact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            objects=(Value.literal(2),),
        )

        covering = {
            c1: Section(fact=fact1, context=c1),
            c2: Section(fact=fact2, context=c2),
        }

        import pytest

        with pytest.raises(GluingError):
            sheaf.glue(Context("world"), covering)

    def test_global_sections(self) -> None:
        sheaf = Sheaf()
        fact = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r"))
        sheaf.assign(Section(fact=fact, context=Context("world")))
        globals_ = sheaf.global_sections()
        assert len(globals_) == 1


class TestSheafStore:
    def test_insert_and_query(self) -> None:
        store = SheafStore()
        fact = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r"))
        store.insert(fact)
        facts = store.query_context(Context("world"))
        assert len(facts) == 1

    def test_query_global(self) -> None:
        store = SheafStore()
        fact = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r"))
        store.insert(fact)
        globals_ = store.query_global()
        assert len(globals_) == 1
