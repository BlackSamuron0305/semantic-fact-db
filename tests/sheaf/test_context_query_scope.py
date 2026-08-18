"""Regression test for a CONTEXT-query performance bug.

`SheafOptimizer._classify_semilocal` used to resolve a CONTEXT query by
finding every fact whose *exact* context equalled the query context and
then fanning out through every open set each of those facts belonged
to -- including "context:world", the ancestor open set every fact in
the corpus belongs to whenever the query context is not the root. The
final result was always correct (a downstream filter narrows back down
to the target sub-tree), so this was invisible to the cross-engine
verification harness and to every prior benchmark: the synthetic
generator's balanced context tree (depth 3, branching 2) grows a
query's *own* subtree size in lockstep with total corpus size, so the
wasted work looked the same shape as genuine result-size-proportional
cost.

It surfaced when scripts/lubm_benchmark.py exercised a topology with a
very different shape -- hundreds of top-level sibling contexts (one per
LUBM university) rather than a few -- decoupling "total corpus size"
from "target subtree size": a CONTEXT query anchored on a fixed,
68-fact department went from 0.68ms to 350ms (a ~515x slowdown) as
unrelated universities were added elsewhere, while the KG-mem control's
latency stayed flat. See paper/sections/discussion.tex for the full
writeup.

The fix makes `_classify_semilocal` target the `context:<c>` open set
directly -- which is already, by construction
(`SheafDatabaseEngine._assign_open_sets`), the exact pre-materialised
sub-tree union the complexity analysis in
paper/sections/complexity.tex describes -- instead of fanning out
through ancestor open sets. This test pins that behaviour at the
optimizer level (a white-box check, since the wasted work was never
visible in the final *result*, only in how much internal work produced
it).
"""

from __future__ import annotations

from common.interfaces import Query, QueryType
from common.schema import SemanticFact
from common.types import Context, Identifier, Value
from sfdb.sheaf.engine import SheafDatabaseEngine


def _make_fact(fact_id: str, context: str) -> SemanticFact:
    return SemanticFact(
        id=Identifier(fact_id),
        subject=Identifier(f"subj_{fact_id}"),
        relation=Identifier("rel"),
        context=Context(context),
        objects=(Value.literal("x"),),
    )


class TestContextQueryScope:
    def test_classification_targets_only_the_query_context(self) -> None:
        """A CONTEXT query anchored below the root must not include the
        root's own open set (context:world) in its target set, even
        though every fact in the corpus is a member of it."""
        engine = SheafDatabaseEngine()
        engine.create()

        # Many unrelated top-level siblings, each with a small subtree --
        # the LUBM-shaped topology that exposed the bug.
        for univ_idx in range(200):
            engine.insert(_make_fact(f"root_{univ_idx}", f"world.University{univ_idx}"))
            engine.insert(_make_fact(f"leaf_{univ_idx}", f"world.University{univ_idx}.dept0"))

        assert engine._optimizer is not None
        classification = engine._optimizer.classify(
            Query(query_type=QueryType.CONTEXT, context="world.University0.dept0", limit=1000)
        )
        assert classification.target_open_sets == ["context:world.University0.dept0"]
        assert "context:world" not in classification.target_open_sets

    def test_result_still_correct_for_wide_topology(self) -> None:
        """Correctness was never the bug, but this pins it: the query
        must still return exactly the facts in the target sub-tree, not
        more and not fewer, regardless of how many unrelated sibling
        contexts exist."""
        engine = SheafDatabaseEngine()
        engine.create()

        for univ_idx in range(50):
            engine.insert(_make_fact(f"root_{univ_idx}", f"world.University{univ_idx}"))
            engine.insert(_make_fact(f"leaf_{univ_idx}", f"world.University{univ_idx}.dept0"))

        result = engine.query(
            Query(query_type=QueryType.CONTEXT, context="world.University0.dept0", limit=1000)
        )
        assert {f.id.value for f in result.facts} == {"leaf_0"}

    def test_context_query_cost_independent_of_unrelated_siblings(self) -> None:
        """The regression this bug describes in one number: querying a
        fixed-size sub-tree must not get slower as unrelated sibling
        contexts are added elsewhere. Checks open-set fan-out size
        (target_open_sets length) rather than wall-clock time, since the
        latter is too noisy for a unit test -- see
        scripts/lubm_benchmark.py for the wall-clock measurement this
        pins the mechanism behind."""
        for num_siblings in (5, 200):
            engine = SheafDatabaseEngine()
            engine.create()
            for univ_idx in range(num_siblings):
                engine.insert(_make_fact(f"root_{univ_idx}", f"world.University{univ_idx}"))
                engine.insert(_make_fact(f"leaf_{univ_idx}", f"world.University{univ_idx}.dept0"))

            assert engine._optimizer is not None
            classification = engine._optimizer.classify(
                Query(query_type=QueryType.CONTEXT, context="world.University0.dept0", limit=1000)
            )
            # Exactly one open set targeted, regardless of corpus width.
            assert len(classification.target_open_sets) == 1
