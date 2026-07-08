"""Standardised benchmark query workloads — 15 queries spanning all categories."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QueryWorkload:
    id: str
    name: str
    description: str
    text: str
    category: str = "general"
    tags: list[str] = field(default_factory=list)


def _q(name: str, text: str, desc: str, cat: str, tags: list[str] | None = None) -> QueryWorkload:
    return QueryWorkload(
        id=name, name=name, description=desc, text=text, category=cat, tags=tags or []
    )


# ---------------------------------------------------------------------------
# Q1–Q15  (SPARQL-like syntax for benchmark display / LaTeX; actual
# execution adapters may rewrite to engine-native form internally.)
# ---------------------------------------------------------------------------

benchmark_queries: list[QueryWorkload] = [
    _q("Q1", "SELECT ?x WHERE { ?x rdf:type ex:Person }", "Simple Lookup", "lookup"),
    _q("Q2", "SELECT ?x ?y WHERE { ?x ex:worksFor ?y }", "Relation Lookup", "lookup"),
    _q("Q3", "SELECT ?x ?y WHERE { ?x ex:knows ?y }", "Join (self)", "join"),
    _q(
        "Q4",
        "SELECT ?z ?p WHERE { ?z ex:memberOf ?p . ?p ex:locatedIn ex:Paris }",
        "Join (2-way)",
        "join",
    ),
    _q(
        "Q5",
        "SELECT ?a ?b WHERE { ?a ex:reportsTo ?b . ?b ex:worksFor ex:Acme }",
        "Path of length 2",
        "path",
    ),
    _q("Q6", "SELECT ?x WHERE { ?x ex:age ?o FILTER(?o > 30) }", "Range scan", "filter"),
    _q(
        "Q7",
        'SELECT ?s WHERE { ?s ex:status "active" ; ex:age ?age FILTER(?age >= 25) }',
        "Multi-filter (conjunction)",
        "filter",
    ),
    _q(
        "Q8",
        "SELECT (COUNT(?s) AS ?cnt) WHERE { ?s rdf:type ex:Person }",
        "Count aggregate",
        "aggregation",
    ),
    _q(
        "Q9",
        "SELECT (AVG(?age) AS ?avg) WHERE { ?s ex:age ?age }",
        "Average aggregate",
        "aggregation",
    ),
    _q(
        "Q10",
        "SELECT ?s ?age WHERE { ?s ex:age ?age } ORDER BY DESC(?age) LIMIT 10",
        "Ordered + Limit",
        "sort",
    ),
    _q(
        "Q11",
        "SELECT ?s WHERE { ?s ex:age ?age . ?s ex:worksFor ex:Acme } ORDER BY ?age LIMIT 5",
        "Filtered + Ordered + Limit",
        "mixed",
    ),
    _q(
        "Q12",
        "SELECT ?s ?dept WHERE { ?s ex:worksFor ?dept }",
        "All employment relationships",
        "scan",
    ),
    _q(
        "Q13",
        "SELECT ?s ?manager WHERE { ?s ex:reportsTo ?manager }",
        "All reporting relationships",
        "scan",
    ),
    _q(
        "Q14",
        'SELECT ?s ?dept WHERE { ?s ex:worksFor ?dept . ?dept ex:sector "tech" }',
        "Indirect filter via object",
        "join",
    ),
    _q(
        "Q15",
        'SELECT ?s ?age WHERE { ?s ex:age ?age . ?s ex:worksFor ?dept . ?dept ex:locatedIn ?city FILTER(?city = "London") }',
        "Multi-join + filter",
        "complex",
    ),
]


def all_workloads() -> list[QueryWorkload]:
    return list(benchmark_queries)


def by_category(cat: str) -> list[QueryWorkload]:
    return [q for q in benchmark_queries if q.category == cat]
