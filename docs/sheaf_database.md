# Sheaf Database Engine

## Overview

The Sheaf Database Engine (`SheafDatabaseEngine`) implements the `DatabaseEngine` ABC using finite sheaf theory. Unlike the Knowledge Graph engine which decomposes facts into triples, the sheaf engine stores each `SemanticFact` as a complete `LocalSection` in a sheaf over a finite topological space.

## Architecture

### Topological Space (X, τ)

- **X**: finite set of points (SemanticFact IDs)
- **τ**: collection of open subsets closed under finite intersection
- Open sets group facts by shared semantic properties (entity, event, context, temporal, provenance)

### Sheaf F: τ^op → Set

- Each open set U ∈ τ maps to the set F(U) of LocalSections defined on U
- Restriction maps ρ_{V,U}: F(V) → F(U) for U ⊆ V
- Global sections are elements of F(X) — sections defined on the entire space

### Open Set Types

| Type | Naming | Purpose |
|------|--------|---------|
| Event | `event:{fact_id}` | Singleton per fact |
| Entity | `entity:{id}` | Groups facts by subject/referenced entity |
| Temporal | `temporal:{year}` | Groups facts by time |
| Context | `context:{path}` | Groups facts by context hierarchy |
| Provenance | `provenance:{source\|method}` | Groups facts by source |

## Query Execution

Queries are classified along a local→global spectrum:

1. **Local** — retrieve facts from a single open set (entity lookup)
2. **Semi-local** — restrict to related open sets (context, temporal, provenance)
3. **Global** — compute global sections via gluing

## Key Components

- **FiniteTopologicalSpace**: stores points and open sets, supports intersection closure
- **Presheaf/Sheaf**: maps open sets to sections; supports restriction and gluing
- **Stalk**: direct limit of sections over neighborhoods of a point
- **RestrictionGraph**: DAG of restriction edges between open sets
- **ConsistencyChecker**: verifies locality, gluing, and composition axioms
- **TopologyBuilder**: builds topology from SemanticFacts using configurable strategies
- **Indexes**: OpenSetIndex, StalkIndex, ContextIndex, NeighborhoodIndex, TemporalIndex, ProvenanceIndex, GlobalSectionCache

## Persistence

SQLite backend with tables:
- `sections`: fact_id, json_data, open_set_name, context, subject, relation, provenance_source, temporal_year, confidence
- `topology_metadata`: key-value metadata
- `restriction_maps`: source/target pairs with application counts
