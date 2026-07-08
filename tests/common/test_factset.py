"""Tests for FactSet operations."""

from sfdb.common.types import Fact, FactSet, Identifier


class TestFactSet:
    def test_empty(self) -> None:
        fs = FactSet()
        assert len(fs) == 0

    def test_add(self) -> None:
        fs = FactSet()
        fact = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r"))
        fs.add(fact)
        assert len(fs) == 1
        assert fact in fs

    def test_remove(self) -> None:
        fs = FactSet()
        fact = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r"))
        fs.add(fact)
        fs.remove(fact)
        assert len(fs) == 0
        assert fact not in fs

    def test_union(self) -> None:
        f1 = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r1"))
        f2 = Fact(id=Identifier("f2"), subject=Identifier("s"), relation=Identifier("r2"))
        fs1 = FactSet([f1])
        fs2 = FactSet([f2])
        merged = fs1.union(fs2)
        assert len(merged) == 2

    def test_intersection(self) -> None:
        f1 = Fact(id=Identifier("f1"), subject=Identifier("s"), relation=Identifier("r1"))
        f2 = Fact(id=Identifier("f2"), subject=Identifier("s"), relation=Identifier("r2"))
        fs1 = FactSet([f1, f2])
        fs2 = FactSet([f2])
        common = fs1.intersection(fs2)
        assert len(common) == 1
        assert f2 in common
