"""Research notebook for the Semantic Fact Database.

This is a computational notebook (Python script) that documents the
research process. It can be run as a script or imported for interactive use.

Usage:
    uv run python research/notebook.py

The notebook demonstrates:
    1. Basic system setup and the common data model
    2. KG triple decomposition and reconstruction
    3. Sheaf section assignment and restriction
    4. Canonical model equivalence proof
    5. Benchmarks
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sfdb.benchmark.runner import BenchmarkConfig, BenchmarkRunner
from sfdb.common.types import Context, Fact, Identifier, Value
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts
from sfdb.kg.graph import KnowledgeGraph
from sfdb.kg.triple import FactDecomposer
from sfdb.query.language import Query, QueryPattern, QueryType
from sfdb.sheaf.sheaf import SheafStore
from sfdb.utils.logging import setup_logging

setup_logging()
logger = logging.getLogger("notebook")


def section_1_data_model() -> None:
    """Section 1: The common data model."""
    print("=" * 60)
    print("SECTION 1: Common Data Model")
    print("=" * 60)

    # Create entities
    alice = Identifier("alice")
    bob = Identifier("bob")
    knows = Identifier("knows")
    works_at = Identifier("works_at")
    acme = Identifier("acme_corp")

    # Create a binary fact
    fact1 = Fact(
        id=Identifier("fact_1"),
        subject=alice,
        relation=knows,
        objects=(Value.reference(bob),),
        context=Context("world"),
    )
    print(f"Binary fact: {fact1}")

    # Create an n-ary fact
    fact2 = Fact(
        id=Identifier("fact_2"),
        subject=alice,
        relation=works_at,
        objects=(
            Value.reference(acme),
            Value.literal("Engineer"),
            Value.literal(2024),
        ),
        context=Context("world"),
    )
    print(f"N-ary fact (arity={fact2.arity()}): {fact2}")

    # Demonstrate context
    narrow = Context("world.2024.engineering")
    broad = Context("world")
    print(f"Context ordering: {narrow} < {broad}: {narrow < broad}")


def section_2_kg_decomposition() -> None:
    """Section 2: KG triple decomposition and reconstruction."""
    print("\n" + "=" * 60)
    print("SECTION 2: KG Triple Decomposition")
    print("=" * 60)

    # Create an n-ary fact
    fact = Fact(
        id=Identifier("fact_works_at"),
        subject=Identifier("alice"),
        relation=Identifier("works_at"),
        objects=(
            Value.reference(Identifier("acme_corp")),
            Value.literal("Engineer"),
        ),
        context=Context("world"),
    )

    # Decompose to triples
    decomposer = FactDecomposer()
    triples = decomposer.decompose(fact)
    print(f"Original fact arity: {fact.arity()}")
    print(f"Decomposed into {len(triples)} triples:")
    for t in triples:
        print(f"  {t}")

    # Insert into KG and reconstruct
    kg = KnowledgeGraph()
    kg.insert_fact(fact)
    print(f"\nKG has {kg.num_triples} triples, {kg.num_entities} entities")

    # Reconstruct
    retrieved = kg.query_subject(Identifier("alice"))
    print(f"Reconstructed {len(retrieved)} facts about alice")


def section_3_sheaf_operations() -> None:
    """Section 3: Sheaf section operations."""
    print("\n" + "=" * 60)
    print("SECTION 3: Sheaf Operations")
    print("=" * 60)

    store = SheafStore()

    # Insert facts at different contexts
    fact_world = Fact(
        id=Identifier("f_phys"),
        subject=Identifier("electron"),
        relation=Identifier("has_charge"),
        objects=(Value.literal(-1),),
        context=Context("world"),
    )
    fact_2024 = Fact(
        id=Identifier("f_phys_2024"),
        subject=Identifier("electron"),
        relation=Identifier("has_charge"),
        objects=(Value.literal(-1.0000000001),),
        context=Context("world.2024.physics"),
    )

    store.insert(fact_world)
    store.insert(fact_2024)

    # Query by context
    world_facts = store.query_context(Context("world"))
    physics_facts = store.query_context(Context("world.2024.physics"))

    print(f"Facts in 'world': {len(world_facts)}")
    print(f"Facts in 'world.2024.physics': {len(physics_facts)}")

    # Global sections
    global_facts = store.query_global()
    print(f"Global sections: {len(global_facts)}")


def section_4_equivalence_check() -> None:
    """Section 4: Verify semantic equivalence between KG and Sheaf."""
    print("\n" + "=" * 60)
    print("SECTION 4: Semantic Equivalence Check")
    print("=" * 60)

    # Insert the same fact into both systems
    fact = Fact(
        id=Identifier("equivalence_test"),
        subject=Identifier("alice"),
        relation=Identifier("knows"),
        objects=(Value.reference(Identifier("bob")),),
        context=Context("world"),
    )

    # KG
    kg = KnowledgeGraph()
    kg.insert_fact(fact)
    kg_facts = kg.query_subject(Identifier("alice"))

    # Sheaf
    sheaf = SheafStore()
    sheaf.insert(fact)
    sheaf_facts = sheaf.query_context(Context("world"))

    kg_ids = {f.id for f in kg_facts}
    sheaf_ids = {f.id for f in sheaf_facts}

    print(f"KG fact IDs: {kg_ids}")
    print(f"Sheaf fact IDs: {sheaf_ids}")
    print(f"Semantically equivalent: {kg_ids == sheaf_ids}")


def section_5_benchmark_demo() -> None:
    """Section 5: Run a small benchmark."""
    print("\n" + "=" * 60)
    print("SECTION 5: Benchmark Demo (small dataset)")
    print("=" * 60)

    # Generate small dataset
    config = SyntheticConfig(num_entities=20, num_facts=50, seed=42)
    dataset = generate_facts(config)
    print(f"Generated {len(dataset.facts)} facts")

    # Create a query
    query = Query(
        type=QueryType.FACT,
        pattern=QueryPattern(subject=Identifier("entity_0")),
    )

    # Run benchmark
    bench_config = BenchmarkConfig(
        name="demo",
        queries=(query,),
        num_runs=2,
        seed=42,
    )
    runner = BenchmarkRunner(bench_config)
    runner.initialize(dataset.facts)
    result = runner.run()

    print(f"KG avg latency: {result.to_dict()['kg']['avg_latency_ms']:.2f} ms")
    print(f"Sheaf avg latency: {result.to_dict()['sheaf']['avg_latency_ms']:.2f} ms")
    print(f"Semantically equivalent: {result.semantically_equivalent}")


if __name__ == "__main__":
    section_1_data_model()
    section_2_kg_decomposition()
    section_3_sheaf_operations()
    section_4_equivalence_check()
    section_5_benchmark_demo()
    print("\nAll research notebook sections complete.")
