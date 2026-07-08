"""Contextual benchmark data generators — high-arity, temporal, provenance."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from sfdb.common.types import Context, Fact


@dataclass
class ContextualConfig:
    seed: int = 42
    num_entities: int = 1000
    num_relations: int = 20
    high_arity_relations: list[int] = field(default_factory=lambda: [3, 5, 8, 12])
    num_high_arity_facts: int = 10000
    num_temporal_facts: int = 10000
    num_provenance_facts: int = 5000
    num_contextual_facts: int = 10000
    temporal_range: tuple[int, int] = (0, 100000)
    temporal_interval_mean: int = 1000
    provenance_max_depth: int = 10
    provenance_branching: int = 2
    contextual_radius: int = 3
    graph_density: float = 0.01
    consistency_overlap: float = 0.3

    def __post_init__(self):
        assert self.num_entities > 0
        assert self.num_relations > 0
        assert all(a >= 2 for a in self.high_arity_relations)
        assert 0 <= self.graph_density <= 1
        assert 0 <= self.consistency_overlap <= 1


@dataclass
class ContextualDataset:
    config: ContextualConfig
    facts: list[Fact] = field(default_factory=list)
    high_arity_facts: list[Fact] = field(default_factory=list)
    temporal_facts: list[Fact] = field(default_factory=list)
    provenance_facts: list[Fact] = field(default_factory=list)
    contextual_facts: list[Fact] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    relations: list[str] = field(default_factory=list)

    @property
    def all_facts(self) -> list[Fact]:
        return (
            self.facts
            + self.high_arity_facts
            + self.temporal_facts
            + self.provenance_facts
            + self.contextual_facts
        )

    @property
    def total_facts(self) -> int:
        return len(self.all_facts)


def _make_entities(config: ContextualConfig, rng: random.Random) -> list[str]:
    return [f"e{i:06d}" for i in range(config.num_entities)]


def _make_relations(config: ContextualConfig, rng: random.Random) -> list[str]:
    base = [f"r{i:03d}" for i in range(config.num_relations)]
    for a in config.high_arity_relations:
        base.append(f"high_arity_{a}")
    base.extend(["temporal_rel", "derived_from", "provenance_rel", "context_rel"])
    return base


def generate_high_arity_facts(
    arity: int,
    num_facts: int,
    entities: list[str],
    rng: random.Random,
    base_id: int = 0,
) -> list[Fact]:
    rel = f"high_arity_{arity}"
    facts: list[Fact] = []
    for i in range(num_facts):
        args = tuple(rng.choice(entities) for _ in range(arity))
        fid = base_id + i
        facts.append(Fact(
            id=f"ha_{arity}_{fid:08d}",
            subject=args[0],
            relation=rel,
            objects=args,
            context=Context("default"),
            confidence=1.0,
            metadata={"arity": arity},
        ))
    return facts


def generate_temporal_facts(
    num_facts: int,
    entities: list[str],
    relations: list[str],
    time_range: tuple[int, int],
    interval_mean: int,
    rng: random.Random,
    base_id: int = 0,
) -> list[Fact]:
    facts: list[Fact] = []
    t_start, t_end = time_range
    for i in range(num_facts):
        fid = base_id + i
        start = rng.randint(t_start, t_end)
        length = max(1, int(rng.gauss(interval_mean, interval_mean * 0.3)))
        end = min(t_end, start + length)
        entity = rng.choice(entities)
        rel = rng.choice(relations)
        obj = rng.choice(entities)
        facts.append(Fact(
            id=f"temporal_{fid:08d}",
            subject=entity,
            relation=rel,
            objects=(obj,),
            context=Context("temporal"),
            confidence=1.0,
            metadata={"start": start, "end": end, "attr": rng.gauss(50, 15)},
        ))
    return facts


def generate_provenance_facts(
    num_source_facts: int,
    num_derived: int,
    relations: list[str],
    entities: list[str],
    max_depth: int,
    branching: int,
    rng: random.Random,
    base_id: int = 0,
) -> list[Fact]:
    sources: list[Fact] = []
    for i in range(num_source_facts):
        fid = base_id + i
        sources.append(Fact(
            id=f"prov_src_{fid:08d}",
            subject=rng.choice(entities),
            relation=rng.choice(relations),
            objects=(rng.choice(entities),),
            context=Context("provenance"),
            confidence=1.0,
            metadata={"confidence": 1.0, "depth": 0},
        ))

    derived: list[Fact] = []
    frontier: list[Fact] = list(sources)
    offset = num_source_facts
    for depth in range(1, max_depth + 1):
        next_frontier: list[Fact] = []
        num_at_depth = max(1, num_derived // (2 ** depth))
        for _ in range(num_at_depth):
            if not frontier:
                break
            parents = rng.sample(frontier, min(branching, len(frontier)))
            fid = offset + len(derived)
            parent_conf = parents[0].metadata.get("confidence", 0.85)
            confidence = min(1.0, max(0.01, rng.gauss(0.85, 0.1) * parent_conf))
            derived.append(Fact(
                id=f"prov_derived_{fid:08d}",
                subject=rng.choice(entities),
                relation="derived_from",
                objects=(parents[0].subject,),
                context=Context("provenance"),
                confidence=confidence,
                metadata={
                    "parents": [p.id for p in parents],
                    "depth": depth,
                    "transformation": rng.choice(["sum", "avg", "max", "min", "concat"]),
                },
            ))
            next_frontier.append(derived[-1])
        frontier = next_frontier
        offset += len(derived)
    return sources + derived


def generate_contextual_graph(
    num_facts: int,
    entities: list[str],
    relations: list[str],
    density: float,
    rng: random.Random,
    base_id: int = 0,
) -> list[Fact]:
    facts: list[Fact] = []
    for i in range(num_facts):
        fid = base_id + i
        s = rng.choice(entities)
        p = rng.choice(relations)
        o = rng.choice(entities)
        facts.append(Fact(
            id=f"ctx_{fid:08d}",
            subject=s,
            relation=p,
            objects=(o,),
            context=Context("contextual"),
            confidence=1.0,
            metadata={},
        ))
        if rng.random() < density:
            mid = rng.choice(entities)
            facts.append(Fact(
                id=f"ctx_{fid:08d}_chain",
                subject=o,
                relation=rng.choice(relations),
                objects=(mid,),
                context=Context("contextual"),
                confidence=1.0,
                metadata={},
            ))
    return facts


def generate_contextual_dataset(config: ContextualConfig) -> ContextualDataset:
    rng = random.Random(config.seed)
    entities = _make_entities(config, rng)
    relations = _make_relations(config, rng)
    ds = ContextualDataset(config=config, entities=entities, relations=relations)
    base_id = 0

    for arity in config.high_arity_relations:
        per_arity = config.num_high_arity_facts // len(config.high_arity_relations)
        ha = generate_high_arity_facts(arity, per_arity, entities, rng, base_id)
        ds.high_arity_facts.extend(ha)
        base_id += len(ha)

    temp = generate_temporal_facts(
        config.num_temporal_facts, entities, relations,
        config.temporal_range, config.temporal_interval_mean, rng, base_id,
    )
    ds.temporal_facts = temp
    base_id += len(temp)

    prov = generate_provenance_facts(
        config.num_temporal_facts // 2, config.num_provenance_facts,
        relations, entities,
        config.provenance_max_depth, config.provenance_branching, rng, base_id,
    )
    ds.provenance_facts = prov
    base_id += len(prov)

    ctx = generate_contextual_graph(
        config.num_contextual_facts, entities, relations,
        config.graph_density, rng, base_id,
    )
    ds.contextual_facts = ctx

    return ds
