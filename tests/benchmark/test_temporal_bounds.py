"""Regression tests for the unbounded-TEMPORAL query semantics.

An earlier version of the paper suite passed a bare year ("2023") as the
start of its "unbounded" temporal query. Both engines share a bare-year
convenience shorthand that silently re-bounds such a query to the single
year [2023-01-01, 2024-01-01), so the suite measured a re-bounded query
while describing it as open-ended. These tests pin the corrected
behaviour: the suite's unbounded query must parse to a genuinely open
end, and both engines must agree that it matches a superset of the
re-bounded variant.
"""

from __future__ import annotations

from datetime import UTC, datetime

from common.interfaces import Query, QueryType
from sfdb.benchmark.engine_adapter import KGEngineAdapter, SheafEngineAdapter
from sfdb.benchmark.paper_suite import TEMPORAL_UNBOUNDED_QUERY_START
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts
from sfdb.kg.engine import _temporal_query_bounds as kg_bounds
from sfdb.sheaf.query import _temporal_query_bounds as sheaf_bounds

ISO_START = "2023-01-01T00:00:00+00:00"


class TestTemporalQueryBounds:
    def test_bare_year_shorthand_is_bounded(self) -> None:
        for bounds in (kg_bounds, sheaf_bounds):
            _q_start, q_end = bounds("2023", None)
            assert q_end == datetime(2024, 1, 1, tzinfo=UTC)

    def test_iso_start_with_no_end_is_truly_unbounded(self) -> None:
        for bounds in (kg_bounds, sheaf_bounds):
            q_start, q_end = bounds(ISO_START, None)
            assert q_start == datetime(2023, 1, 1, tzinfo=UTC)
            assert q_end is None

    def test_paper_suite_unbounded_query_is_unbounded(self) -> None:
        for bounds in (kg_bounds, sheaf_bounds):
            _q_start, q_end = bounds(TEMPORAL_UNBOUNDED_QUERY_START, None)
            assert q_end is None, (
                "The paper suite's TEMPORAL_UNBOUNDED query start must not "
                "trigger the bare-year re-bounding shorthand"
            )


class TestUnboundedSupersetsWindow:
    def test_engines_agree_and_unbounded_is_a_superset(self) -> None:
        config = SyntheticConfig(num_facts=300, num_entities=30, seed=42)
        facts = generate_facts(config).facts

        unbounded = Query(
            query_type=QueryType.TEMPORAL,
            temporal_start=TEMPORAL_UNBOUNDED_QUERY_START,
            temporal_end=None,
            limit=10_000,
        )
        window = Query(
            query_type=QueryType.TEMPORAL,
            temporal_start="2023",
            temporal_end=None,  # bare-year shorthand: re-bounds to [2023, 2024)
            limit=10_000,
        )

        counts: dict[str, tuple[int, int]] = {}
        for name, adapter in (("kg", KGEngineAdapter()), ("sheaf", SheafEngineAdapter())):
            adapter.insert_batch(list(facts))
            unbounded_ids = {str(f.id) for f in adapter.execute_query(unbounded)}
            window_ids = {str(f.id) for f in adapter.execute_query(window)}
            assert window_ids <= unbounded_ids, f"{name}: window result not a subset"
            counts[name] = (len(unbounded_ids), len(window_ids))

        assert counts["kg"] == counts["sheaf"]
        kg_unbounded, kg_window = counts["kg"]
        assert kg_unbounded > kg_window, (
            "The truly unbounded query should match strictly more facts than "
            "the re-bounded single-year window on the 6-year synthetic span"
        )
