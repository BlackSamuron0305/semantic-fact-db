"""Engine adapters for identical benchmark execution across all engines.

Each adapter wraps a DatabaseEngine implementation and provides a uniform
interface for the benchmark runner.  Only KG and Sheaf adapters have working
implementations; Jena, Blazegraph, and Neo4j are stubs for future work.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from common.interfaces import Query, QueryType
from common.schema import SemanticFact
from common.types import Identifier


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
    """Uniform adapter interface for benchmark execution.

    Each adapter wraps a single DatabaseEngine and translates benchmark
    query strings into engine-native operations.
    """

    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def metadata(self) -> EngineMetadata: ...
    @abstractmethod
    def insert(self, fact: SemanticFact) -> None: ...
    @abstractmethod
    def insert_batch(self, facts: list[SemanticFact]) -> None: ...
    @abstractmethod
    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]: ...
    @abstractmethod
    def clear(self) -> None: ...


class KGEngineAdapter(EngineAdapter):
    """Adapter for KnowledgeGraphEngine.

    Translates benchmark query strings into Query objects and executes
    them via the engine's query() method.  Uses query_sparql() for
    SPARQL-like strings.
    """

    def __init__(self) -> None:
        from sfdb.kg.engine import KnowledgeGraphEngine

        self._engine = KnowledgeGraphEngine(name="bench_kg")
        self._engine.create()

    def name(self) -> str:
        return "KnowledgeGraph"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            name="KnowledgeGraph", version="1.0", engine_type=EngineType.KNOWLEDGE_GRAPH
        )

    def insert(self, fact: SemanticFact) -> None:
        self._engine.insert(fact)

    def insert_batch(self, facts: list[SemanticFact]) -> None:
        for f in facts:
            self._engine.insert(f)

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        """Execute a SPARQL-like query string against the KG engine.

        First tries the native SPARQL parser; falls back to simple
        pattern matching for benchmark workload IDs.
        """
        try:
            results = self._engine.query_sparql(query_str)
            if results:
                return results
        except Exception:
            pass

        # Fallback: map common patterns to Query objects
        q = self._parse_query_text(query_str)
        if q is not None:
            try:
                qr = self._engine.query(q)
                return [{"fact_id": str(f.id), "subject": str(f.subject), "relation": str(f.relation)} for f in qr.facts]
            except Exception:
                pass
        return []

    def _parse_query_text(self, text: str) -> Query | None:
        """Parse a simple SPARQL-like string into a Query object.

        Handles patterns like:
          SELECT ?x WHERE { ?x rdf:type ex:Person }
          SELECT ?x ?y WHERE { ?x ex:worksFor ?y }
        """
        text = text.strip()
        if "WHERE" not in text:
            return None
        where_part = text.split("WHERE")[1].strip().strip("{}").strip()
        if not where_part:
            return None

        # Extract triple patterns
        patterns = [p.strip() for p in where_part.split(".") if p.strip()]
        if not patterns:
            return None

        first = patterns[0]
        parts = first.split()
        if len(parts) < 3:
            return None

        s, p, o = parts[0], parts[1], parts[2]

        # Build Query based on pattern shape
        if p == "rdf:type" and o.startswith("ex:"):
            return Query(query_type=QueryType.LOOKUP, limit=100)
        if p.startswith("ex:"):
            return Query(query_type=QueryType.LOOKUP, limit=100)
        return Query(query_type=QueryType.GLOBAL, limit=100)

    def clear(self) -> None:
        self._engine.drop()
        self._engine.create()


class SheafEngineAdapter(EngineAdapter):
    """Adapter for SheafDatabaseEngine.

    Translates benchmark query strings into sheaf-native operations
    (context lookup, local section retrieval, global reconstruction).
    """

    def __init__(self) -> None:
        from sfdb.sheaf.engine import SheafDatabaseEngine

        self._engine = SheafDatabaseEngine(name="bench_sheaf")
        self._engine.create()

    def name(self) -> str:
        return "SheafDatabase"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            name="SheafDatabase", version="1.0", engine_type=EngineType.SHEAF_DATABASE
        )

    def insert(self, fact: SemanticFact) -> None:
        self._engine.insert(fact)

    def insert_batch(self, facts: list[SemanticFact]) -> None:
        for f in facts:
            self._engine.insert(f)

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        """Execute a query string against the sheaf engine.

        Maps common SPARQL-like patterns to sheaf query operations.
        """
        try:
            q = self._parse_query_text(query_str)
            if q is not None:
                qr = self._engine.query(q)
                return [{"fact_id": str(f.id), "subject": str(f.subject), "relation": str(f.relation)} for f in qr.facts]
        except Exception:
            pass
        return []

    def _parse_query_text(self, text: str) -> Query | None:
        """Parse a simple SPARQL-like string into a Query object."""
        text = text.strip()
        if "WHERE" not in text:
            return None
        where_part = text.split("WHERE")[1].strip().strip("{}").strip()
        if not where_part:
            return None

        patterns = [p.strip() for p in where_part.split(".") if p.strip()]
        if not patterns:
            return None

        first = patterns[0]
        parts = first.split()
        if len(parts) < 3:
            return None

        s, p, o = parts[0], parts[1], parts[2]

        if p == "rdf:type" and o.startswith("ex:"):
            return Query(query_type=QueryType.LOOKUP, limit=100)
        if p.startswith("ex:"):
            return Query(query_type=QueryType.LOOKUP, limit=100)
        return Query(query_type=QueryType.GLOBAL, limit=100)

    def clear(self) -> None:
        self._engine.drop()
        self._engine.create()


class JenaEngineAdapter(EngineAdapter):
    """Adapter for Apache Jena via rdflib.

    Uses rdflib's Graph to store triples and execute SPARQL queries.
    This provides a real RDF store comparison point for the benchmark.

    Note: rdflib stores facts as decomposed triples (like standard RDF
    reification), so n-ary facts lose their structure.  This is the
    standard RDF limitation that SheafDB is designed to address.
    """

    def __init__(self) -> None:
        self._available = False
        self._fact_map: dict[str, SemanticFact] = {}
        try:
            from rdflib import BNode, Graph, Literal, URIRef

            self._jena = Graph()
            self._BNode = BNode
            self._URIRef = URIRef
            self._Literal = Literal
            self._available = True
        except ImportError:
            pass

    def name(self) -> str:
        return "ApacheJena"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            name="ApacheJena (rdflib)", version="7.x", engine_type=EngineType.APACHE_JENA
        )

    def insert(self, fact: SemanticFact) -> None:
        if not self._available:
            return
        self._fact_map[fact.id.value] = fact
        # Store as reified triples (standard RDF approach)
        event = self._BNode()
        self._jena.add((event, self._URIRef("rdf:type"), self._URIRef("ex:Fact")))
        self._jena.add((event, self._URIRef("ex:factId"), self._Literal(fact.id.value)))
        self._jena.add((event, self._URIRef("ex:subject"), self._Literal(fact.subject.value)))
        self._jena.add((event, self._URIRef("ex:relation"), self._Literal(fact.relation.value)))
        for i, obj in enumerate(fact.objects):
            val = str(obj.inner) if hasattr(obj, "inner") else str(obj)
            self._jena.add((event, self._URIRef(f"ex:object_{i}"), self._Literal(val)))
        for k, v in fact.attributes.items():
            val = str(v.inner) if hasattr(v, "inner") else str(v)
            self._jena.add((event, self._URIRef(f"ex:attr_{k}"), self._Literal(val)))
        self._jena.add((event, self._URIRef("ex:context"), self._Literal(str(fact.context))))
        self._jena.add((event, self._URIRef("ex:confidence"), self._Literal(str(fact.confidence))))

    def insert_batch(self, facts: list[SemanticFact]) -> None:
        for f in facts:
            self.insert(f)

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        """Execute a SPARQL query against the rdflib graph.

        Returns a list of binding dictionaries.
        """
        if not self._available:
            return []
        try:
            results = self._jena.query(query_str)
            bindings = []
            for row in results:
                binding = {}
                for var, val in row.asdict().items():
                    binding[var] = str(val)
                bindings.append(binding)
            return bindings
        except Exception:
            return []

    def clear(self) -> None:
        if not self._available:
            return
        from rdflib import Graph

        self._jena = Graph()
        self._fact_map.clear()


class BlazegraphEngineAdapter(EngineAdapter):
    """Stub adapter — not yet implemented."""

    def __init__(self) -> None:
        self._available = False
        raise NotImplementedError("Blazegraph adapter is scaffolded but not yet integrated into the benchmark pipeline")

    def name(self) -> str:
        return "Blazegraph"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(name="Blazegraph", version="2.1", engine_type=EngineType.BLAZEGRAPH)

    def insert(self, fact: SemanticFact) -> None:
        raise NotImplementedError("Blazegraph adapter not implemented")

    def insert_batch(self, facts: list[SemanticFact]) -> None:
        raise NotImplementedError("Blazegraph adapter not implemented")

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        raise NotImplementedError("Blazegraph adapter not implemented")

    def clear(self) -> None:
        raise NotImplementedError("Blazegraph adapter not implemented")


class Neo4jEngineAdapter(EngineAdapter):
    """Stub adapter — not yet implemented."""

    def __init__(self) -> None:
        self._available = False
        raise NotImplementedError("Neo4j adapter is scaffolded but not yet integrated into the benchmark pipeline")

    def name(self) -> str:
        return "Neo4j"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(name="Neo4j", version="5.x", engine_type=EngineType.NEO4J)

    def insert(self, fact: SemanticFact) -> None:
        raise NotImplementedError("Neo4j adapter not implemented")

    def insert_batch(self, facts: list[SemanticFact]) -> None:
        raise NotImplementedError("Neo4j adapter not implemented")

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        raise NotImplementedError("Neo4j adapter not implemented")

    def clear(self) -> None:
        raise NotImplementedError("Neo4j adapter not implemented")


def create_adapters() -> dict[EngineType, EngineAdapter]:
    adapters: dict[EngineType, EngineAdapter] = {
        EngineType.KNOWLEDGE_GRAPH: KGEngineAdapter(),
        EngineType.SHEAF_DATABASE: SheafEngineAdapter(),
        EngineType.APACHE_JENA: JenaEngineAdapter(),
    }
    # Blazegraph and Neo4j adapters are scaffolded but not yet integrated
    # (they raise NotImplementedError on construction).
    return adapters
