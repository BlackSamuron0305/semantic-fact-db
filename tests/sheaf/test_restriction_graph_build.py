"""Equivalence test for the membership-driven restriction-graph build.

The engine's `_build_restriction_edges` was rewritten from a pairwise
subset sweep over all open-set pairs (quadratic in the number of open
sets; intractable at 10^5 facts) to a membership-driven construction
that intersects the topology's point-to-open-set map. The two must
produce the identical edge set; this test recomputes the reference
edges with the original pairwise algorithm and compares.
"""

from __future__ import annotations

from common.interfaces import Query, QueryType
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts
from sfdb.sheaf.engine import SheafDatabaseEngine


def _reference_edges(engine: SheafDatabaseEngine) -> set[tuple[str, str]]:
    """The original pairwise-subset construction, kept as the oracle."""
    edges: set[tuple[str, str]] = set()
    os_list = list(engine._topology.open_sets.values())
    for u in os_list:
        for v in os_list:
            if u.name != v.name and v.is_subset_of(u) and v.points:
                edges.add((u.name, v.name))
    return edges


def test_membership_build_matches_pairwise_oracle() -> None:
    config = SyntheticConfig(num_facts=300, num_entities=30, seed=42)
    facts = generate_facts(config).facts

    engine = SheafDatabaseEngine(name="test_restriction_build")
    engine.create()
    for f in facts:
        engine.insert(f)

    # Trigger the (new) build through the ordinary query path.
    engine.query(Query(query_type=QueryType.GLOBAL, limit=10_000))

    built: set[tuple[str, str]] = {
        (source, target)
        for source, targets in engine._restriction_graph._edges.items()
        for target in targets
    }
    expected = _reference_edges(engine)

    assert built == expected, (
        f"{len(built - expected)} spurious and {len(expected - built)} missing edges "
        f"vs the pairwise oracle ({len(expected)} expected)"
    )
    assert len(expected) > 0, "empty oracle would make this test vacuous"


def test_rebuild_after_insert_stays_equivalent() -> None:
    config = SyntheticConfig(num_facts=120, num_entities=20, seed=7)
    facts = list(generate_facts(config).facts)

    engine = SheafDatabaseEngine(name="test_restriction_rebuild")
    engine.create()
    for f in facts[:100]:
        engine.insert(f)
    engine.query(Query(query_type=QueryType.GLOBAL, limit=10_000))

    # Insert more facts (marks the topology dirty), query again, re-check.
    for f in facts[100:]:
        engine.insert(f)
    engine.query(Query(query_type=QueryType.GLOBAL, limit=10_000))

    built = {
        (source, target)
        for source, targets in engine._restriction_graph._edges.items()
        for target in targets
    }
    assert built == _reference_edges(engine)
