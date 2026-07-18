"""Unit tests for the flat, binary-searchable temporal index.

These exercise TemporalIndex.facts_ending_after / facts_starting_before
directly, independent of the query planner, since they back the fix for
the open-ended TEMPORAL range case described in the paper's discussion
of threats to validity.
"""

from __future__ import annotations

from datetime import UTC, datetime

from common.schema import SemanticFact
from common.types import Context, Identifier, Provenance, TemporalInfo
from sfdb.sheaf.indexes import TemporalIndex, parse_temporal_bound


def _dt(year: int, month: int = 1, day: int = 1) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


def _fact(fid: str, start: datetime | None, end: datetime | None) -> SemanticFact:
    temporal = None if start is None else TemporalInfo(start=start, end=end)
    return SemanticFact(
        id=Identifier(f"fact_{fid}"),
        subject=Identifier("e1"),
        relation=Identifier("rel"),
        objects=(),
        context=Context("world"),
        confidence=1.0,
        provenance=Provenance(source="test", method="test"),
        temporal=temporal,
    )


class TestParseTemporalBound:
    def test_bare_year(self) -> None:
        assert parse_temporal_bound("2024") == _dt(2024)

    def test_full_iso(self) -> None:
        assert parse_temporal_bound("2024-06-15T00:00:00+00:00") == datetime(2024, 6, 15, tzinfo=UTC)


class TestTemporalIndexFacetEndingAfter:
    def test_bounded_fact_included_when_end_after_bound(self) -> None:
        idx = TemporalIndex()
        idx.index_fact(_fact("a", _dt(2021), _dt(2023)))
        assert "fact_a" in idx.facts_ending_after(_dt(2022))

    def test_bounded_fact_excluded_when_end_before_bound(self) -> None:
        idx = TemporalIndex()
        idx.index_fact(_fact("a", _dt(2018), _dt(2019)))
        assert "fact_a" not in idx.facts_ending_after(_dt(2022))

    def test_open_ended_fact_always_included(self) -> None:
        idx = TemporalIndex()
        idx.index_fact(_fact("a", _dt(2010), None))
        assert "fact_a" in idx.facts_ending_after(_dt(2099))

    def test_atemporal_fact_never_included(self) -> None:
        idx = TemporalIndex()
        idx.index_fact(_fact("a", None, None))
        assert "fact_a" not in idx.facts_ending_after(_dt(1900))

    def test_binary_search_matches_linear_scan_across_many_facts(self) -> None:
        idx = TemporalIndex()
        expected: set[str] = set()
        bound = _dt(2015)
        for year in range(2000, 2030):
            fid = f"y{year}"
            end = _dt(year + 1) if year % 3 else None  # every third fact is open-ended
            idx.index_fact(_fact(fid, _dt(year), end))
            if end is None or end > bound:
                expected.add(f"fact_{fid}")
        assert idx.facts_ending_after(bound) == frozenset(expected)


class TestTemporalIndexFactsStartingBefore:
    def test_fact_included_when_start_before_bound(self) -> None:
        idx = TemporalIndex()
        idx.index_fact(_fact("a", _dt(2010), _dt(2012)))
        assert "fact_a" in idx.facts_starting_before(_dt(2020))

    def test_fact_excluded_when_start_after_bound(self) -> None:
        idx = TemporalIndex()
        idx.index_fact(_fact("a", _dt(2025), _dt(2026)))
        assert "fact_a" not in idx.facts_starting_before(_dt(2020))

    def test_fact_excluded_when_start_equals_bound(self) -> None:
        idx = TemporalIndex()
        idx.index_fact(_fact("a", _dt(2020), _dt(2021)))
        assert "fact_a" not in idx.facts_starting_before(_dt(2020))
