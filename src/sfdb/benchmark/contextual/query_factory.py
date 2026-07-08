"""Parameterized query generation for contextual benchmarks."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Any


@dataclass(frozen=True)
class QueryTemplate:
    id: str
    name: str
    template: str
    params: dict[str, list[Any]] = field(default_factory=dict)
    description: str = ""

    def render(self, **kwargs: Any) -> str:
        result = self.template
        for k, v in kwargs.items():
            result = result.replace(f"{{{k}}}", str(v))
        return result

    def param_product(self) -> list[dict[str, Any]]:
        if not self.params:
            return [{}]
        keys = list(self.params.keys())
        values = list(self.params.values())
        return [dict(zip(keys, combo)) for combo in product(*values)]


T1_NEIGHBORHOOD = QueryTemplate(
    id="CTX-NBH",
    name="Contextual Neighborhood",
    template=(
        "SELECT ?fact ?s ?p ?o ?dist WHERE {{ "
        "?fact ex:neighbor ex:{entity} . "
        "?fact ex:distance ?dist . "
        "FILTER(?dist <= {radius}) "
        "}}"
    ),
    params={"entity": ["e0", "e100", "e500"], "radius": [1, 2, 3]},
    description="Fact neighborhood query parameterized by seed entity and radius.",
)

T2_HIGH_ARITY_LOOKUP = QueryTemplate(
    id="HA-LOOKUP",
    name="High-Arity Lookup",
    template=(
        "SELECT ?fact ?v0 ?v1 ?v2 ?v3 ?v4 WHERE {{ "
        "?fact rdf:type ex:{relation} . "
        "?fact ex:arg0 ?v0 . "
        "?fact ex:arg1 ?v1 . "
        "?fact ex:arg2 ?v2 . "
        "?fact ex:arg3 ?v3 . "
        "?fact ex:arg4 ?v4 . "
        "FILTER(?v0 = '{match}') "
        "}}"
    ),
    params={
        "relation": ["high_arity_5", "high_arity_8"],
        "match": ["e0", "e100"],
    },
    description="High-arity lookup with partial match on first argument.",
)

T3_TEMPORAL_INTERVAL = QueryTemplate(
    id="TEMP-INT",
    name="Temporal Interval",
    template=(
        "SELECT ?fact ?start ?end WHERE {{ "
        "?fact ex:validStart ?start . "
        "?fact ex:validEnd ?end . "
        "FILTER(?start < {q_end} && ?end > {q_start}) "
        "}}"
    ),
    params={"q_start": [0, 5000, 10000], "q_end": [10000, 20000, 50000]},
    description="Temporal interval overlap query.",
)

T4_TEMPORAL_AGG = QueryTemplate(
    id="TEMP-AGG",
    name="Temporal Aggregation",
    template=(
        "SELECT (COUNT(?fact) AS ?cnt) (AVG(?val) AS ?avg) WHERE {{ "
        "?fact ex:validStart ?start . "
        "?fact ex:validEnd ?end . "
        "?fact ex:attr ?val . "
        "FILTER(?start < {window_end} && ?end > {window_start}) "
        "}}"
    ),
    params={"window_start": [0, 5000], "window_end": [5000, 10000]},
    description="Sliding window temporal aggregation.",
)

T5_PROVENANCE = QueryTemplate(
    id="PROV",
    name="Provenance Chain",
    template=(
        "SELECT ?derived ?source ?depth ?conf WHERE {{ "
        "?derived ex:derivedFrom ?source . "
        "?derived ex:depth ?depth . "
        "?derived ex:confidence ?conf . "
        "FILTER(?depth <= {max_depth}) "
        "}} ORDER BY ?depth"
    ),
    params={"max_depth": [3, 5, 10]},
    description="Provenance chain tracing.",
)

T6_CONSISTENCY = QueryTemplate(
    id="CONSIST",
    name="Consistency Check",
    template=(
        "SELECT ?context ?entity ?value WHERE {{ "
        "?context ex:assigns ?entity . "
        "?context ex:value ?value . "
        "}} ORDER BY ?context"
    ),
    params={"": []},
    description="Consistency check: retrieve all local assignments.",
)

T7_GLOBAL_SECTION = QueryTemplate(
    id="GLOB-SEC",
    name="Global Section",
    template=(
        "SELECT ?entity ?value (COUNT(DISTINCT ?context) AS ?ctx_count) WHERE {{ "
        "?context ex:assigns ?entity . "
        "?context ex:value ?value . "
        "}} GROUP BY ?entity ?value HAVING (?ctx_count >= {min_coverage})"
    ),
    params={"min_coverage": [1, 2, 3]},
    description="Global section: find entities with consistent assignments across contexts.",
)

T8_MIXED = QueryTemplate(
    id="MIXED",
    name="Mixed Realistic",
    template=(
        "PREFIX ex: <http://example.org/>\n"
        "SELECT ?neighbor ?temporal ?provenance ?consistent WHERE {{\n"
        "  {{ SELECT ?neighbor WHERE {{ ex:{seed} ex:neighbor ?neighbor . }} }}\n"
        "  {{ SELECT ?temporal WHERE {{ ?temporal ex:validStart ?s . ?temporal ex:validEnd ?e . FILTER(?s < {t_end} && ?e > {t_start}) }} }}\n"
        "  OPTIONAL {{ ?neighbor ex:derivedFrom ?provenance . }}\n"
        "  BIND(EXISTS {{ ?neighbor ex:consistent true }} AS ?consistent)\n"
        "}}"
    ),
    params={"seed": ["e0", "e500"], "t_start": [0, 5000], "t_end": [10000, 50000]},
    description="Mixed multi-stage flagship query.",
)

ALL_TEMPLATES: list[QueryTemplate] = [
    T1_NEIGHBORHOOD,
    T2_HIGH_ARITY_LOOKUP,
    T3_TEMPORAL_INTERVAL,
    T4_TEMPORAL_AGG,
    T5_PROVENANCE,
    T6_CONSISTENCY,
    T7_GLOBAL_SECTION,
    T8_MIXED,
]


def param_grid(template_ids: list[str] | None = None) -> list[tuple[QueryTemplate, dict[str, Any]]]:
    """Generate all (template, params) combinations for the given template ids."""
    templates = [t for t in ALL_TEMPLATES if template_ids is None or t.id in template_ids]
    results: list[tuple[QueryTemplate, dict[str, Any]]] = []
    for t in templates:
        for p in t.param_product():
            results.append((t, p))
    return results


def render_query(template_id: str, **kwargs: Any) -> str:
    """Render a named template with the given parameter values."""
    for t in ALL_TEMPLATES:
        if t.id == template_id:
            return t.render(**kwargs)
    msg = f"Unknown template: {template_id}"
    raise ValueError(msg)
