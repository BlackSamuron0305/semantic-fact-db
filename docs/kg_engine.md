# Knowledge Graph Engine

The `KnowledgeGraphEngine` is an RDF-style triple store serving as the baseline for comparison against the Sheaf Database. It implements dictionary encoding, SPO/POS/OPS indexing, reification for n-ary facts, SPARQL-inspired queries, and a cost-based optimizer.

## Architecture

```
┌─────────────────────────────────────────────┐
│            KnowledgeGraphEngine              │
├─────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │  Dictionary  │  │   Triple Table +     │  │
│  │  Encoding    │  │   SPO/POS/OPS Idx    │  │
│  └─────────────┘  └──────────────────────┘  │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │  Reification │  │   Query Engine       │  │
│  │  (n-ary)     │  │   (SPARQL + Plans)   │  │
│  └─────────────┘  └──────────────────────┘  │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │  Optimizer   │  │   Visualization      │  │
│  │  (CBO)       │  │   (Graphviz DOT)     │  │
│  └─────────────┘  └──────────────────────┘  │
│  ┌──────────────────────────────────────┐   │
│  │         SQLite Persistence           │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## Quick Start

```python
from sfdb.kg.engine import KnowledgeGraphEngine
from common.types import Fact, Identifier, Value

engine = KnowledgeGraphEngine()
engine.initialize()

# Insert a fact
fact = Fact(
    id=Identifier("event1"),
    type=Identifier("Event"),
    context=Identifier("default"),
    arguments={
        "subject": Value("Alice"),
        "action": Value("runs"),
    },
)
engine.insert(fact)

# Lookup
retrieved = engine.lookup(Identifier("event1"))

# SPARQL query
results = engine.query_sparql("SELECT ?s ?p ?o WHERE { ?s ?p ?o }")

# EXPLAIN plan
plan = engine.explain('SELECT ?s WHERE { ?s ?p ?o . FILTER(?o = "hello") }')
print("\n".join(plan))

# Statistics
stats = engine.statistics()
print(f"Total triples: {stats['total_triples']}")

# Visualization (Graphviz DOT format)
dot = engine.visualize_entity_graph()
```

## Modules

| Module | Description |
|--------|-------------|
| `engine.py` | Core engine: insert, lookup, delete, query, SPARQL, statistics, export/import |
| `sparql.py` | SPARQL parser (tokeniser + recursive descent) and naive executor |
| `planner.py` | Logical operators, physical plan builder, plan executor |
| `optimizer.py` | Cost estimation, join reordering, filter pushdown, EXPLAIN |
| `visualization.py` | Graphviz DOT generation for entity/predicate/event/neighborhood graphs |

## Storage Schema

### Dictionary Tables

- `entity_dictionary`: Maps entity names (strings) to integer IDs
- `predicate_dictionary`: Maps predicate names to integer IDs
- `literal_table`: Maps literal values (with datatypes) to integer IDs

### Triple Table

```
triples(subject, predicate, object, obj_type, ev_id)
```

Three indexes by default:
- `idx_spo`: (subject, predicate, object)
- `idx_pos`: (predicate, object, subject)
- `idx_ops`: (object, predicate, subject)

### Reification Table

```
reification(ev_id, pred_id, obj_id, role)
```

## Query Planning

1. **Parsing**: SPARQL string → `SparqlQuery` AST (select vars, triple patterns, filters, order, limit)
2. **Logical Planning**: AST → tree of `LogicalNode` operators (Scan/IndexSeek/Filter/Join/Project/Sort/Limit)
3. **Optimization**: Cost-based optimization (filter pushdown, join reordering, index selection)
4. **Physical Planning**: Logical operators → physical execution plan
5. **Execution**: Tree-walking interpreter materializes results

## CSV Export/Import

```python
# Export to N-Triples
engine.export("export.nt")

# Import from N-Triples
engine.import_file("export.nt")
```

## Testing

```bash
pytest tests/kg/ -v
```
