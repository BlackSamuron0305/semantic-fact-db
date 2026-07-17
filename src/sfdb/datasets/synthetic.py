"""Synthetic dataset generation for controlled experiments.

Generates random semantic facts with controlled properties:
    - Number of entities
    - Number of relations
    - Arity distribution (how many objects per fact)
    - Context depth distribution
    - Graph structure (for walk queries)

The synthetic datasets allow us to isolate specific factors and
measure their impact on both representations.

Complexity
----------
Generation: O(n · k) where n = number of facts, k = avg arity.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from common.schema import SemanticFact
from common.types import Context, Identifier, Provenance, SemanticType, TemporalInfo, Value

# Fixed timestamp for deterministic generation
_FIXED_TS: datetime = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
_TEMPORAL_ORIGIN: datetime = datetime(2020, 1, 1, 0, 0, 0, tzinfo=UTC)
_TEMPORAL_SPAN_DAYS = 365 * 6


@dataclass(slots=True, frozen=True)
class SyntheticConfig:
    """Configuration for synthetic dataset generation.

    Parameters
    ----------
    num_entities: Number of distinct entities.
    num_relations: Number of distinct relation types.
    num_facts: Number of facts to generate.
    min_arity: Minimum number of object slots per fact.
    max_arity: Maximum number of object slots per fact.
    arity_distribution: Distribution of arities over
        [min_arity, max_arity]. If None, uniform.
    context_depth: Maximum context depth.
    context_branching: Number of sub-contexts per context level.
    entity_skew: Zipf exponent for entity selection (0 = uniform,
        larger = more skewed towards low-index entities, mirroring the
        degree skew of real knowledge-graph entities).
    temporal_fraction: Fraction of facts given a temporal validity
        interval.
    seed: Random seed.
    """

    num_entities: int = 100
    num_relations: int = 10
    num_facts: int = 1000
    min_arity: int = 3
    max_arity: int = 8
    arity_distribution: tuple[float, ...] | None = None
    context_depth: int = 3
    context_branching: int = 2
    entity_skew: float = 1.2
    temporal_fraction: float = 0.4
    seed: int = 42

    def __post_init__(self) -> None:
        if self.min_arity < 1 or self.min_arity > self.max_arity:
            raise ValueError("min_arity must be >= 1 and <= max_arity")
        if self.arity_distribution is not None:
            expected_len = self.max_arity - self.min_arity + 1
            if len(self.arity_distribution) != expected_len:
                raise ValueError(
                    f"arity_distribution must have length {expected_len} "
                    f"(max_arity - min_arity + 1)"
                )
            if abs(sum(self.arity_distribution) - 1.0) > 1e-6:
                raise ValueError("arity_distribution must sum to 1.0")


def _zipf_weights(n: int, skew: float) -> list[float]:
    """Un-normalised Zipf-like weights favouring low-index items.

    weight(i) = 1 / (i + 1) ** skew, i = 0..n-1. skew == 0 gives a
    uniform distribution.
    """
    return [1.0 / (i + 1) ** skew for i in range(n)]


@dataclass(slots=True)
class SyntheticDataset:
    """A generated synthetic dataset.

    Attributes
    ----------
    config: The configuration used.
    entities: Generated entity identifiers.
    relations: Generated relation identifiers.
    contexts: Generated contexts.
    facts: Generated facts.
    """

    config: SyntheticConfig
    entities: list[Identifier] = field(default_factory=list)
    relations: list[Identifier] = field(default_factory=list)
    contexts: list[Context] = field(default_factory=list)
    facts: list[SemanticFact] = field(default_factory=list)

    @property
    def num_facts(self) -> int:
        return len(self.facts)

    @property
    def avg_arity(self) -> float:
        if not self.facts:
            return 0.0
        return sum(f.arity() for f in self.facts) / len(self.facts)

    @property
    def num_entities(self) -> int:
        return len(self.entities)

    @property
    def num_relations(self) -> int:
        return len(self.relations)


def generate_entities(config: SyntheticConfig, _rng: random.Random) -> list[Identifier]:
    """Generate entity identifiers."""
    return [Identifier(f"entity_{i}") for i in range(config.num_entities)]


def generate_relations(config: SyntheticConfig, _rng: random.Random) -> list[Identifier]:
    """Generate relation identifiers."""
    return [Identifier(f"relation_{i}") for i in range(config.num_relations)]


def generate_contexts(
    config: SyntheticConfig,
    rng: random.Random,
    prefix: str = "ctx",
    depth: int = 0,
) -> list[Context]:
    """Generate a tree of contexts recursively."""
    if depth >= config.context_depth:
        return []
    contexts: list[Context] = []
    for i in range(config.context_branching):
        path = f"{prefix}.{i}" if prefix != "ctx" else f"ctx.{i}"
        ctx = Context(path)
        contexts.append(ctx)
        contexts.extend(generate_contexts(config, rng, path, depth + 1))
    return contexts


def generate_facts(config: SyntheticConfig) -> SyntheticDataset:
    """Generate a complete synthetic dataset.

    Produces facts with controlled arity distribution, random entity
    and relation assignments, and a context hierarchy.
    """
    rng = random.Random(config.seed)
    dataset = SyntheticDataset(config=config)

    dataset.entities = generate_entities(config, rng)
    dataset.relations = generate_relations(config, rng)
    dataset.contexts = generate_contexts(config, rng)
    # Always include root context
    root_ctx = Context("world")
    if root_ctx not in dataset.contexts:
        dataset.contexts.append(root_ctx)

    # Zipf-like skew: a small head of entities is referenced far more
    # often than the tail, mirroring the degree distribution of real
    # knowledge-graph entities rather than a uniform draw.
    entity_weights = _zipf_weights(len(dataset.entities), config.entity_skew)

    arity_choices = list(range(config.min_arity, config.max_arity + 1))

    for i in range(config.num_facts):
        subject = rng.choices(dataset.entities, weights=entity_weights, k=1)[0]
        relation = rng.choice(dataset.relations)
        context = rng.choice(dataset.contexts)

        # Determine arity
        if config.arity_distribution:
            arity = rng.choices(
                arity_choices,
                weights=config.arity_distribution,
                k=1,
            )[0]
        else:
            arity = rng.choice(arity_choices)

        # Generate object values
        objects: list[Value] = []
        for _ in range(arity):
            if rng.random() < 0.5:
                # Entity reference
                obj_entity = rng.choices(dataset.entities, weights=entity_weights, k=1)[0]
                objects.append(Value.reference(obj_entity))
            else:
                # Literal value
                obj_type = rng.choice(
                    [
                        SemanticType.ATTRIBUTE,
                        SemanticType.QUANTITY,
                    ]
                )
                if obj_type == SemanticType.QUANTITY:
                    objects.append(Value.literal(rng.randint(0, 100)))
                else:
                    objects.append(Value.literal(f"val_{rng.randint(0, 100)}"))

        temporal = None
        if rng.random() < config.temporal_fraction:
            start_offset = rng.randint(0, _TEMPORAL_SPAN_DAYS)
            start = _TEMPORAL_ORIGIN + timedelta(days=start_offset)
            duration = rng.randint(1, 365 * 2)
            temporal = TemporalInfo(start=start, end=start + timedelta(days=duration))

        fact = SemanticFact(
            id=Identifier(f"fact_{i}"),
            subject=subject,
            relation=relation,
            objects=tuple(objects),
            context=context,
            confidence=rng.uniform(0.5, 1.0),
            provenance=Provenance(source="synthetic", method="generated", recorded_at=_FIXED_TS),
            temporal=temporal,
        )
        dataset.facts.append(fact)

    return dataset


def generate_random_graph(
    num_nodes: int,
    edge_density: float,
    seed: int = 42,
) -> list[SemanticFact]:
    """Generate a random graph as facts.

    Creates a set of facts representing edges in a random graph.
    Useful for testing walk and join queries.

    Parameters
    ----------
    num_nodes: Number of nodes in the graph.
    edge_density: Probability of an edge between any two nodes.
    seed: Random seed.

    Returns
    -------
    List of facts, each representing an edge.
    """
    rng = random.Random(seed)
    nodes = [Identifier(f"node_{i}") for i in range(num_nodes)]
    edge_rel = Identifier("connected_to")
    facts: list[SemanticFact] = []

    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if rng.random() < edge_density:
                fact = SemanticFact(
                    id=Identifier(),
                    subject=nodes[i],
                    relation=edge_rel,
                    objects=(Value.reference(nodes[j]),),
                    context=Context("world"),
                    provenance=Provenance(source="synthetic", method="generated", recorded_at=_FIXED_TS),
                )
                facts.append(fact)

    return facts
