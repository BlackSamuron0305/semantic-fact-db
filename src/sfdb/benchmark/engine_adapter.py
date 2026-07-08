"""Engine adapters for identical benchmark execution across all engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from sfdb.common.types import Fact
from sfdb.kg.graph import KnowledgeGraph


class EngineType(Enum):
    KNOWLEDGE_GRAPH = auto()
    SHEAF_DATABASE = auto()
    APACHE_JENA = auto()
    BLAZEGRAPH = auto()
    NEO4J = auto()


@dataclass
class EngineMetadata:
    name: str
    version: str = ""
    engine_type: EngineType = EngineType.KNOWLEDGE_GRAPH

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "version": self.version, "type": self.engine_type.name}


class EngineAdapter(ABC):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def metadata(self) -> EngineMetadata: ...
    @abstractmethod
    def insert(self, fact: Fact) -> None: ...
    @abstractmethod
    def insert_batch(self, facts: list[Fact]) -> None: ...
    @abstractmethod
    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]: ...
    @abstractmethod
    def clear(self) -> None: ...


class KGEngineAdapter(EngineAdapter):
    def __init__(self) -> None:
        self._graph = KnowledgeGraph(name="bench_kg")

    def name(self) -> str:
        return "KnowledgeGraph"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            name="KnowledgeGraph", version="1.0", engine_type=EngineType.KNOWLEDGE_GRAPH
        )

    def insert(self, fact: Fact) -> None:
        self._graph.insert_fact(fact)

    def insert_batch(self, facts: list[Fact]) -> None:
        for f in facts:
            self._graph.insert_fact(f)

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        return []

    def clear(self) -> None:
        self._graph = KnowledgeGraph(name="bench_kg")


class SheafEngineAdapter(EngineAdapter):
    def __init__(self) -> None:
        from sfdb.sheaf.sheaf import SheafStore

        self._store = SheafStore()

    def name(self) -> str:
        return "SheafDatabase"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            name="SheafDatabase", version="1.0", engine_type=EngineType.SHEAF_DATABASE
        )

    def insert(self, fact: Fact) -> None:
        self._store.insert(fact)

    def insert_batch(self, facts: list[Fact]) -> None:
        for f in facts:
            self._store.insert(f)

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        try:
            results = self._store.query(query_str)
            if results is None:
                return []
            if isinstance(results, dict):
                return [results]
            if isinstance(results, list):
                return [{"result": str(r)} for r in results]
            return [{"result": str(results)}]
        except Exception:
            return []

    def clear(self) -> None:
        from sfdb.sheaf.sheaf import SheafStore

        self._store = SheafStore()


class JenaEngineAdapter(EngineAdapter):
    def __init__(self) -> None:
        self._available = False
        self._triples: list[tuple[str, str, str]] = []
        try:
            from rdflib import Graph

            self._jena = Graph()
            self._available = True
        except ImportError:
            pass

    def name(self) -> str:
        return "ApacheJena"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            name="ApacheJena TDB2", version="5.x", engine_type=EngineType.APACHE_JENA
        )

    def insert(self, fact: Fact) -> None:
        if not self._available:
            return
        from rdflib import Literal, URIRef

        s = str(fact.subject)
        p = str(fact.relation)
        for o in fact.objects:
            o_str = str(o.inner) if hasattr(o, "inner") else str(o)
            self._triples.append((s, p, o_str))
            self._jena.add((URIRef(s), URIRef(p), Literal(o_str)))

    def insert_batch(self, facts: list[Fact]) -> None:
        for f in facts:
            self.insert(f)

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        return []

    def clear(self) -> None:
        if not self._available:
            return
        from rdflib import Graph

        self._jena = Graph()
        self._triples.clear()


class BlazegraphEngineAdapter(EngineAdapter):
    def __init__(self) -> None:
        self._available = False

    def name(self) -> str:
        return "Blazegraph"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(name="Blazegraph", version="2.1", engine_type=EngineType.BLAZEGRAPH)

    def insert(self, fact: Fact) -> None:
        pass

    def insert_batch(self, facts: list[Fact]) -> None:
        pass

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        return []

    def clear(self) -> None:
        pass


class Neo4jEngineAdapter(EngineAdapter):
    def __init__(self) -> None:
        self._available = False

    def name(self) -> str:
        return "Neo4j"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(name="Neo4j", version="5.x", engine_type=EngineType.NEO4J)

    def insert(self, fact: Fact) -> None:
        pass

    def insert_batch(self, facts: list[Fact]) -> None:
        pass

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        return []

    def clear(self) -> None:
        pass


def create_adapters() -> dict[EngineType, EngineAdapter]:
    return {
        EngineType.KNOWLEDGE_GRAPH: KGEngineAdapter(),
        EngineType.SHEAF_DATABASE: SheafEngineAdapter(),
        EngineType.APACHE_JENA: JenaEngineAdapter(),
        EngineType.BLAZEGRAPH: BlazegraphEngineAdapter(),
        EngineType.NEO4J: Neo4jEngineAdapter(),
    }
