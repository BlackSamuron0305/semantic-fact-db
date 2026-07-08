"""Dataset loaders for LUBM, DBpedia, YAGO, Wikidata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sfdb.common.types import Context, Fact, Identifier, Value
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts


def load_dataset(
    name: str = "synthetic",
    path: str = "",
    **kwargs: Any,
) -> list[Fact]:
    if name == "synthetic" or not path:
        num_facts = kwargs.get("num_facts", 1000)
        num_entities = kwargs.get("num_entities", 100)
        seed = kwargs.get("seed", 42)
        ds = generate_facts(
            SyntheticConfig(num_facts=num_facts, num_entities=num_entities, seed=seed)
        )
        return ds.facts

    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".json":
        return _load_json(p)
    if ext == ".jsonl":
        return _load_jsonl(p)
    if ext == ".ttl":
        return _load_turtle(p)
    if ext == ".nt":
        return _load_ntriples(p)
    return _load_json(p)


def _load_json(path: Path) -> list[Fact]:
    data = json.loads(path.read_text())
    facts: list[Fact] = []
    for i, item in enumerate(data if isinstance(data, list) else [data]):
        f = Fact(
            id=Identifier(f"fact_{i}"),
            subject=Identifier(str(item.get("subject", f"entity_{i}"))),
            relation=Identifier(str(item.get("relation", "related_to"))),
            objects=tuple(Value.literal(str(o)) for o in item.get("objects", [f"obj_{i}"])),
            context=Context(str(item.get("context", "world"))),
            confidence=float(item.get("confidence", 1.0)),
        )
        facts.append(f)
    return facts


def _load_jsonl(path: Path) -> list[Fact]:
    facts: list[Fact] = []
    for i, line in enumerate(path.read_text().strip().split("\n")):
        if not line.strip():
            continue
        item = json.loads(line)
        f = Fact(
            id=Identifier(f"fact_{i}"),
            subject=Identifier(str(item.get("subject", f"entity_{i}"))),
            relation=Identifier(str(item.get("relation", "related_to"))),
            objects=tuple(Value.literal(str(o)) for o in item.get("objects", [f"obj_{i}"])),
            context=Context(str(item.get("context", "world"))),
            confidence=float(item.get("confidence", 1.0)),
        )
        facts.append(f)
    return facts


def _load_turtle(path: Path) -> list[Fact]:
    facts: list[Fact] = []
    try:
        import rdflib

        g = rdflib.Graph()
        g.parse(str(path), format="turtle")
        for i, (s, p, o) in enumerate(g):
            f = Fact(
                id=Identifier(f"fact_{i}"),
                subject=Identifier(str(s)),
                relation=Identifier(str(p)),
                objects=(Value.literal(str(o)),),
                context=Context("world"),
            )
            facts.append(f)
    except ImportError:
        pass
    return facts


def _load_ntriples(path: Path) -> list[Fact]:
    facts: list[Fact] = []
    try:
        import rdflib

        g = rdflib.Graph()
        g.parse(str(path), format="nt")
        for i, (s, p, o) in enumerate(g):
            f = Fact(
                id=Identifier(f"fact_{i}"),
                subject=Identifier(str(s)),
                relation=Identifier(str(p)),
                objects=(Value.literal(str(o)),),
                context=Context("world"),
            )
            facts.append(f)
    except ImportError:
        pass
    return facts
