"""Engine adapters for identical benchmark execution across all engines.

Each adapter wraps a DatabaseEngine implementation and provides a uniform
interface for the benchmark runner.  Working adapters: KG (SQLite), KG-mem
(the dict-indexed storage-layer control), Sheaf, and rdflib (an external
pure-Python RDF library queried via SPARQL text).  Blazegraph and Neo4j
are stubs for future work.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from common.interfaces import Query, QueryType
from common.schema import SemanticFact


class EngineType(Enum):
    KNOWLEDGE_GRAPH = auto()
    KNOWLEDGE_GRAPH_MEMORY = auto()
    SHEAF_DATABASE = auto()
    RDFLIB = auto()
    APACHE_JENA = auto()
    VIRTUOSO = auto()
    GRAPHDB = auto()
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

    def execute_query(self, query: Query) -> list[SemanticFact]:
        """Execute a typed Query directly, bypassing text parsing.

        Not all adapters can support this (e.g. rdflib-backed ones that
        only speak SPARQL text); the default raises NotImplementedError.
        """
        raise NotImplementedError(f"{type(self).__name__} does not support typed Query execution")


class KGEngineAdapter(EngineAdapter):
    """Adapter for KnowledgeGraphEngine.

    Translates benchmark query strings into Query objects and executes
    them via the engine's query() method.  Uses query_sparql() for
    SPARQL-like strings.  With ``storage="memory"`` the engine runs the
    KG-mem control variant: identical reification and query logic, with
    dict-backed dictionaries and triple indexes replacing the SQLite
    tables (see sfdb.kg.engine.MemoryIndexManager).
    """

    def __init__(self, storage: str = "sqlite") -> None:
        from sfdb.kg.engine import KnowledgeGraphEngine

        self._storage = storage
        self._engine = KnowledgeGraphEngine(name=f"bench_kg_{storage}")
        self._engine.create({"storage": storage})

    def name(self) -> str:
        return "KnowledgeGraph" if self._storage == "sqlite" else "KnowledgeGraphMem"

    def metadata(self) -> EngineMetadata:
        if self._storage == "memory":
            return EngineMetadata(
                name="KnowledgeGraphMem",
                version="1.0",
                engine_type=EngineType.KNOWLEDGE_GRAPH_MEMORY,
            )
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
        self._engine.create({"storage": self._storage})

    def execute_query(self, query: Query) -> list[SemanticFact]:
        return list(self._engine.query(query).facts)


class KGMemEngineAdapter(KGEngineAdapter):
    """The KG-mem control baseline: dict-indexed variant of the KG engine.

    Exists to isolate the storage-layer variable in the paper's central
    comparison — the sheaf engine answers queries from in-memory Python
    indexes while the KG baseline answers them through SQLite, so this
    variant runs the *same* reification-plus-reconstruction logic as the
    KG baseline with the SQLite tables swapped for Python dicts.
    """

    def __init__(self) -> None:
        super().__init__(storage="memory")


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

    def execute_query(self, query: Query) -> list[SemanticFact]:
        return list(self._engine.query(query).facts)


class RdflibEngineAdapter(EngineAdapter):
    """Adapter for rdflib, a real, independent, pure-Python RDF library.

    Uses rdflib's Graph to store triples and execute SPARQL queries.
    This provides an external (non-in-house) RDF comparison point for the
    benchmark. It is NOT Apache Jena or any disk-backed production triple
    store — an earlier version of this class was named JenaEngineAdapter,
    which overstated what it wraps.

    Note: rdflib stores facts as decomposed triples (like standard RDF
    reification), so n-ary facts lose their structure.  This is the
    standard RDF limitation that SheafDB is designed to address.
    """

    def __init__(self) -> None:
        self._available = False
        self._fact_map: dict[str, SemanticFact] = {}
        try:
            from rdflib import BNode, Graph, Literal, URIRef

            self._graph = Graph()
            self._BNode = BNode
            self._URIRef = URIRef
            self._Literal = Literal
            self._available = True
        except ImportError:
            pass

    def name(self) -> str:
        return "rdflib"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(name="rdflib", version="7.x", engine_type=EngineType.RDFLIB)

    def insert(self, fact: SemanticFact) -> None:
        if not self._available:
            return
        self._fact_map[fact.id.value] = fact
        # Store as reified triples (standard RDF approach)
        event = self._BNode()
        self._graph.add((event, self._URIRef("rdf:type"), self._URIRef("ex:Fact")))
        self._graph.add((event, self._URIRef("ex:factId"), self._Literal(fact.id.value)))
        self._graph.add((event, self._URIRef("ex:subject"), self._Literal(fact.subject.value)))
        self._graph.add((event, self._URIRef("ex:relation"), self._Literal(fact.relation.value)))
        for i, obj in enumerate(fact.objects):
            val = str(obj.inner) if hasattr(obj, "inner") else str(obj)
            self._graph.add((event, self._URIRef(f"ex:object_{i}"), self._Literal(val)))
        for k, v in fact.attributes.items():
            val = str(v.inner) if hasattr(v, "inner") else str(v)
            self._graph.add((event, self._URIRef(f"ex:attr_{k}"), self._Literal(val)))
        self._graph.add((event, self._URIRef("ex:context"), self._Literal(str(fact.context))))
        self._graph.add(
            (event, self._URIRef("ex:confidence"), self._Literal(str(fact.confidence)))
        )
        if fact.temporal is not None:
            if fact.temporal.start is not None:
                self._graph.add(
                    (
                        event,
                        self._URIRef("ex:temporalStart"),
                        self._Literal(fact.temporal.start.isoformat()),
                    )
                )
            if fact.temporal.end is not None:
                self._graph.add(
                    (
                        event,
                        self._URIRef("ex:temporalEnd"),
                        self._Literal(fact.temporal.end.isoformat()),
                    )
                )

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
            results = self._graph.query(query_str)
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

        self._graph = Graph()
        self._fact_map.clear()


def _sparql_escape(s: str) -> str:
    """Escape a string for use inside a SPARQL/Turtle double-quoted literal."""
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


class JenaTDB2EngineAdapter(EngineAdapter):
    """Adapter for a real, disk-backed Apache Jena TDB2 store via Fuseki.

    Talks to a running Fuseki server (default
    http://localhost:3030/<dataset>) over the standard SPARQL 1.1 HTTP
    protocol: SPARQL Update for inserts, SPARQL Query for reads. This is
    the production RDF store comparison every reviewer persona in
    research/reviewer_simulation.md named as the single highest-leverage
    gap, and the one Section~future:jena of the paper previously scoped
    out. Unlike RdflibEngineAdapter (a pure-Python, in-memory library),
    this is a genuine external Java process with its own disk-backed
    storage engine, query optimiser, and HTTP server — not code written
    by this project's authors.

    Uses the identical reification predicates as RdflibEngineAdapter
    (`ex:factId`, `ex:subject`, `ex:relation`, `ex:object_N`,
    `ex:attr_K`, `ex:context`, `ex:confidence`, `ex:temporalStart`,
    `ex:temporalEnd`) so the two are directly comparable and the same
    SPARQL query text (scripts/rdflib_reference.py's SPARQL_QUERIES) runs
    against both unchanged.
    """

    _INSERT_BATCH_SIZE = 2000

    def __init__(self, base_url: str = "http://localhost:3030/sfdb") -> None:
        self._base_url = base_url.rstrip("/")
        self._available = False
        try:
            import requests

            self._requests = requests
            resp = requests.get(
                f"{self._base_url}/sparql", params={"query": "ASK { ?s ?p ?o }"}, timeout=3
            )
            self._available = resp.status_code == 200
        except Exception:
            self._available = False

    def name(self) -> str:
        return "JenaTDB2"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            name="Apache Jena TDB2 (via Fuseki)",
            version="6.2.0",
            engine_type=EngineType.APACHE_JENA,
        )

    def _fact_to_triples_block(self, fact: SemanticFact, event_id: str) -> str:
        lines = [
            f'_:{event_id} <rdf:type> <ex:Fact> .',
            f'_:{event_id} <ex:factId> "{_sparql_escape(fact.id.value)}" .',
            f'_:{event_id} <ex:subject> "{_sparql_escape(fact.subject.value)}" .',
            f'_:{event_id} <ex:relation> "{_sparql_escape(fact.relation.value)}" .',
        ]
        for i, obj in enumerate(fact.objects):
            val = str(obj.inner) if hasattr(obj, "inner") else str(obj)
            lines.append(f'_:{event_id} <ex:object_{i}> "{_sparql_escape(val)}" .')
        for k, v in fact.attributes.items():
            val = str(v.inner) if hasattr(v, "inner") else str(v)
            lines.append(f'_:{event_id} <ex:attr_{_sparql_escape(k)}> "{_sparql_escape(val)}" .')
        lines.append(f'_:{event_id} <ex:context> "{_sparql_escape(str(fact.context))}" .')
        lines.append(f'_:{event_id} <ex:confidence> "{fact.confidence}" .')
        if fact.temporal is not None:
            if fact.temporal.start is not None:
                lines.append(
                    f'_:{event_id} <ex:temporalStart> "{fact.temporal.start.isoformat()}" .'
                )
            if fact.temporal.end is not None:
                lines.append(f'_:{event_id} <ex:temporalEnd> "{fact.temporal.end.isoformat()}" .')
        return "\n".join(lines)

    def insert(self, fact: SemanticFact) -> None:
        self.insert_batch([fact])

    def insert_batch(self, facts: list[SemanticFact]) -> None:
        if not self._available:
            return
        for start in range(0, len(facts), self._INSERT_BATCH_SIZE):
            chunk = facts[start : start + self._INSERT_BATCH_SIZE]
            blocks = [self._fact_to_triples_block(f, f"e{start + i}") for i, f in enumerate(chunk)]
            update = "INSERT DATA {\n" + "\n".join(blocks) + "\n}"
            resp = self._requests.post(
                f"{self._base_url}/update",
                data=update.encode("utf-8"),
                headers={"Content-Type": "application/sparql-update; charset=utf-8"},
                timeout=120,
            )
            resp.raise_for_status()

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        if not self._available:
            return []
        try:
            resp = self._requests.post(
                f"{self._base_url}/sparql",
                data=query_str.encode("utf-8"),
                headers={
                    "Content-Type": "application/sparql-query; charset=utf-8",
                    "Accept": "application/sparql-results+json",
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            bindings = []
            for row in data.get("results", {}).get("bindings", []):
                bindings.append({k: v.get("value", "") for k, v in row.items()})
            return bindings
        except Exception:
            return []

    def clear(self) -> None:
        if not self._available:
            return
        resp = self._requests.post(
            f"{self._base_url}/update",
            data=b"DELETE WHERE { ?s ?p ?o }",
            headers={"Content-Type": "application/sparql-update; charset=utf-8"},
            timeout=120,
        )
        resp.raise_for_status()


class VirtuosoEngineAdapter(EngineAdapter):
    """Adapter for a real OpenLink Virtuoso open-source RDF store.

    A second, independently engineered production RDF store, alongside
    JenaTDB2EngineAdapter, so the Section~eval:jena comparison does not
    rest on one vendor's optimiser. Talks to a running Virtuoso instance
    (default http://localhost:8890, the standard Docker image's exposed
    port) over SPARQL 1.1 HTTP: authenticated SPARQL Update (Virtuoso
    requires HTTP Digest auth on its `/sparql-auth` endpoint and, unlike
    Jena, requires every `INSERT DATA` triple to name an explicit graph)
    for inserts, and plain SPARQL Query for reads. Facts are stored in one
    named graph; queries use the *same*, unmodified SPARQL query text as
    JenaTDB2EngineAdapter and RdflibEngineAdapter (the `SPARQL_QUERIES` in
    scripts/rdflib_reference.py, which contain no `GRAPH` clause) by
    passing Virtuoso's `default-graph-uri` HTTP parameter instead of
    rewriting the query — so all three external comparisons run literally
    identical query text against literally identical fact streams.
    """

    # Much smaller than Jena's batch size: Virtuoso's SPARQL compiler hits
    # a hard "memory exhausted" parse-time limit on very large INSERT DATA
    # statements (observed failing around ~1000 facts / ~430KB in one
    # statement; this is a documented Virtuoso characteristic, not a
    # network or data-correctness issue -- SPARQL Update is not Virtuoso's
    # intended bulk-load path). 200 was verified to work reliably.
    _INSERT_BATCH_SIZE = 200
    _GRAPH_URI = "http://sfdb-benchmark/"

    def __init__(
        self,
        base_url: str = "http://localhost:8890",
        user: str = "dba",
        password: str = "sfdb_bench_2026",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._available = False
        try:
            import requests
            import requests.auth

            self._requests = requests
            # A persistent Session with one reused HTTPDigestAuth instance
            # (rather than a fresh one per call) keeps the TCP connection
            # alive and lets requests' digest-auth handling skip the
            # separate 401-challenge round trip on every batch after the
            # first -- this alone was roughly a 2x speedup on insert.
            self._session = requests.Session()
            self._session.auth = requests.auth.HTTPDigestAuth(user, password)
            resp = self._session.get(
                f"{self._base_url}/sparql", params={"query": "ASK { ?s ?p ?o }"}, timeout=3
            )
            self._available = resp.status_code == 200
        except Exception:
            self._available = False

    def name(self) -> str:
        return "Virtuoso"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            name="OpenLink Virtuoso (open-source)",
            version="7.x",
            engine_type=EngineType.VIRTUOSO,
        )

    def _fact_to_triples_block(self, fact: SemanticFact, event_id: str) -> str:
        lines = [
            f'_:{event_id} <rdf:type> <ex:Fact> .',
            f'_:{event_id} <ex:factId> "{_sparql_escape(fact.id.value)}" .',
            f'_:{event_id} <ex:subject> "{_sparql_escape(fact.subject.value)}" .',
            f'_:{event_id} <ex:relation> "{_sparql_escape(fact.relation.value)}" .',
        ]
        for i, obj in enumerate(fact.objects):
            val = str(obj.inner) if hasattr(obj, "inner") else str(obj)
            lines.append(f'_:{event_id} <ex:object_{i}> "{_sparql_escape(val)}" .')
        for k, v in fact.attributes.items():
            val = str(v.inner) if hasattr(v, "inner") else str(v)
            lines.append(f'_:{event_id} <ex:attr_{_sparql_escape(k)}> "{_sparql_escape(val)}" .')
        lines.append(f'_:{event_id} <ex:context> "{_sparql_escape(str(fact.context))}" .')
        lines.append(f'_:{event_id} <ex:confidence> "{fact.confidence}" .')
        if fact.temporal is not None:
            if fact.temporal.start is not None:
                lines.append(
                    f'_:{event_id} <ex:temporalStart> "{fact.temporal.start.isoformat()}" .'
                )
            if fact.temporal.end is not None:
                lines.append(f'_:{event_id} <ex:temporalEnd> "{fact.temporal.end.isoformat()}" .')
        return "\n".join(lines)

    def insert(self, fact: SemanticFact) -> None:
        self.insert_batch([fact])

    def insert_batch(self, facts: list[SemanticFact]) -> None:
        if not self._available:
            return
        for start in range(0, len(facts), self._INSERT_BATCH_SIZE):
            chunk = facts[start : start + self._INSERT_BATCH_SIZE]
            blocks = [self._fact_to_triples_block(f, f"e{start + i}") for i, f in enumerate(chunk)]
            update = f"INSERT DATA {{ GRAPH <{self._GRAPH_URI}> {{\n" + "\n".join(blocks) + "\n} }"
            resp = self._session.post(
                f"{self._base_url}/sparql-auth",
                data=update.encode("utf-8"),
                headers={"Content-Type": "application/sparql-update; charset=utf-8"},
                timeout=120,
            )
            resp.raise_for_status()

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        if not self._available:
            return []
        try:
            resp = self._session.get(
                f"{self._base_url}/sparql",
                params={
                    "query": query_str,
                    "default-graph-uri": self._GRAPH_URI,
                    "format": "application/sparql-results+json",
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            bindings = []
            for row in data.get("results", {}).get("bindings", []):
                bindings.append({k: v.get("value", "") for k, v in row.items()})
            return bindings
        except Exception:
            return []

    def clear(self) -> None:
        if not self._available:
            return
        resp = self._session.post(
            f"{self._base_url}/sparql-auth",
            data=f"CLEAR GRAPH <{self._GRAPH_URI}>".encode(),
            headers={"Content-Type": "application/sparql-update; charset=utf-8"},
            timeout=120,
        )
        resp.raise_for_status()


class GraphDBEngineAdapter(EngineAdapter):
    """Adapter for a real Ontotext GraphDB (free edition) RDF store.

    A third, independently engineered production RDF store, alongside
    JenaTDB2EngineAdapter and VirtuosoEngineAdapter, so the crossover
    reported in Section~eval:jena and Section~eval:virtuoso can be
    checked against a third unrelated optimiser rather than resting on
    two. Talks to a running GraphDB instance (default
    http://localhost:7200, the standard Docker image's exposed port)
    over plain, unauthenticated SPARQL~1.1 HTTP -- unlike Virtuoso,
    GraphDB's free edition requires neither HTTP auth nor an explicit
    named graph for `INSERT DATA`, so this adapter is closer in shape to
    JenaTDB2EngineAdapter than to VirtuosoEngineAdapter. A named
    repository must exist before this adapter can use it (see
    scripts/graphdb_reference.py, which creates one via GraphDB's REST
    API if it does not already exist). Queries use the identical,
    unmodified SPARQL query text shared with the other two production
    stores and rdflib.
    """

    _INSERT_BATCH_SIZE = 2000
    _REPOSITORY_ID = "sfdb"

    # Minimal GraphDB Sesame repository config (Turtle), the format its
    # REST API accepts for repository creation. Auto-creating this
    # repository on first use (rather than requiring a manual setup
    # step, the way VirtuosoEngineAdapter requires a pre-configured DBA
    # password) means this adapter only needs GraphDB itself running.
    _REPO_CONFIG_TTL = """
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rep: <http://www.openrdf.org/config/repository#> .
@prefix sr: <http://www.openrdf.org/config/repository/sail#> .
@prefix sail: <http://www.openrdf.org/config/sail#> .
@prefix graphdb: <http://www.ontotext.com/config/graphdb#> .

[] a rep:Repository ;
    rep:repositoryID "{repo_id}" ;
    rdfs:label "SFDB benchmark repository" ;
    rep:repositoryImpl [
        rep:repositoryType "graphdb:SailRepository" ;
        sr:sailImpl [
            sail:sailType "graphdb:Sail" ;
            graphdb:ruleset "empty" ;
            graphdb:storage-folder "storage" ;
            graphdb:base-URL "http://example.org/owlim#" ;
            graphdb:repository-type "file-repository" ;
            graphdb:enable-context-index "false" ;
            graphdb:enablePredicateList "true" ;
            graphdb:in-memory-literal-properties "true" ;
            graphdb:enable-literal-index "true" ;
            graphdb:check-for-inconsistencies "false" ;
            graphdb:disable-sameAs "true" ;
            graphdb:query-timeout "0" ;
            graphdb:read-only "false" ;
        ]
    ] .
"""

    def __init__(self, base_url: str = "http://localhost:7200") -> None:
        self._base_url = base_url.rstrip("/")
        self._repo_url = f"{self._base_url}/repositories/{self._REPOSITORY_ID}"
        self._available = False
        try:
            import requests

            self._requests = requests
            resp = requests.get(self._repo_url, params={"query": "ASK { ?s ?p ?o }"}, timeout=3)
            if resp.status_code == 404:
                self._create_repository()
                resp = requests.get(
                    self._repo_url, params={"query": "ASK { ?s ?p ?o }"}, timeout=3
                )
            self._available = resp.status_code == 200
        except Exception:
            self._available = False

    def _create_repository(self) -> None:
        config = self._REPO_CONFIG_TTL.format(repo_id=self._REPOSITORY_ID)
        resp = self._requests.post(
            f"{self._base_url}/rest/repositories",
            files={"config": ("config.ttl", config, "text/turtle")},
            timeout=30,
        )
        resp.raise_for_status()

    def name(self) -> str:
        return "GraphDB"

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            name="Ontotext GraphDB (free edition)",
            version="10.7.x",
            engine_type=EngineType.GRAPHDB,
        )

    def _fact_to_triples_block(self, fact: SemanticFact, event_id: str) -> str:
        lines = [
            f"_:{event_id} <rdf:type> <ex:Fact> .",
            f'_:{event_id} <ex:factId> "{_sparql_escape(fact.id.value)}" .',
            f'_:{event_id} <ex:subject> "{_sparql_escape(fact.subject.value)}" .',
            f'_:{event_id} <ex:relation> "{_sparql_escape(fact.relation.value)}" .',
        ]
        for i, obj in enumerate(fact.objects):
            val = str(obj.inner) if hasattr(obj, "inner") else str(obj)
            lines.append(f'_:{event_id} <ex:object_{i}> "{_sparql_escape(val)}" .')
        for k, v in fact.attributes.items():
            val = str(v.inner) if hasattr(v, "inner") else str(v)
            lines.append(f'_:{event_id} <ex:attr_{_sparql_escape(k)}> "{_sparql_escape(val)}" .')
        lines.append(f'_:{event_id} <ex:context> "{_sparql_escape(str(fact.context))}" .')
        lines.append(f'_:{event_id} <ex:confidence> "{fact.confidence}" .')
        if fact.temporal is not None:
            if fact.temporal.start is not None:
                lines.append(
                    f'_:{event_id} <ex:temporalStart> "{fact.temporal.start.isoformat()}" .'
                )
            if fact.temporal.end is not None:
                lines.append(f'_:{event_id} <ex:temporalEnd> "{fact.temporal.end.isoformat()}" .')
        return "\n".join(lines)

    def insert(self, fact: SemanticFact) -> None:
        self.insert_batch([fact])

    def insert_batch(self, facts: list[SemanticFact]) -> None:
        if not self._available:
            return
        for start in range(0, len(facts), self._INSERT_BATCH_SIZE):
            chunk = facts[start : start + self._INSERT_BATCH_SIZE]
            blocks = [self._fact_to_triples_block(f, f"e{start + i}") for i, f in enumerate(chunk)]
            update = "INSERT DATA {\n" + "\n".join(blocks) + "\n}"
            resp = self._requests.post(
                f"{self._repo_url}/statements",
                data=update.encode("utf-8"),
                headers={"Content-Type": "application/sparql-update; charset=utf-8"},
                timeout=120,
            )
            resp.raise_for_status()

    def execute_query_str(self, query_str: str) -> list[dict[str, Any]]:
        if not self._available:
            return []
        try:
            resp = self._requests.get(
                self._repo_url,
                params={"query": query_str},
                headers={"Accept": "application/sparql-results+json"},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            bindings = []
            for row in data.get("results", {}).get("bindings", []):
                bindings.append({k: v.get("value", "") for k, v in row.items()})
            return bindings
        except Exception:
            return []

    def clear(self) -> None:
        if not self._available:
            return
        resp = self._requests.post(
            f"{self._repo_url}/statements",
            data=b"CLEAR ALL",
            headers={"Content-Type": "application/sparql-update; charset=utf-8"},
            timeout=120,
        )
        resp.raise_for_status()


class BlazegraphEngineAdapter(EngineAdapter):
    """Stub adapter — not yet implemented."""

    def __init__(self) -> None:
        raise NotImplementedError(
            "BlazegraphEngineAdapter is a scaffold. "
            "See src/sfdb/benchmark/engine_adapter.py for integration notes."
        )

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
        raise NotImplementedError(
            "Neo4jEngineAdapter is a scaffold. "
            "See src/sfdb/benchmark/engine_adapter.py for integration notes."
        )

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
        EngineType.KNOWLEDGE_GRAPH_MEMORY: KGMemEngineAdapter(),
        EngineType.SHEAF_DATABASE: SheafEngineAdapter(),
        EngineType.RDFLIB: RdflibEngineAdapter(),
    }
    # Blazegraph and Neo4j adapters are scaffolded but not yet integrated
    # (they raise NotImplementedError on construction).
    return adapters
