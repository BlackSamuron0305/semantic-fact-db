# Architecture Overview

## System Architecture

```
+------------------------------------------------------------------+
|                         Query Language                            |
|                    (representation-agnostic)                      |
+------------------------------------------------------------------+
                            |
                            v
+------------------------------------------------------------------+
|                     Canonical Semantic Model                      |
|                    (SemanticFact dataclass)                       |
|                    - validation                                   |
|                    - serialization (JSON/Parquet/MessagePack)     |
+------------------------------------------------------------------+
                            |
                            v
+-----------------------------------+-------------------------------+
|           Query Planner           |      Configuration System     |
|  (logical plan -> physical plans) |   (YAML / env / CLI)         |
+-----------------------------------+-------------------------------+
                            |
                            v
+------------------+------------------+----------------------------+
|  Knowledge Graph |  Sheaf Database  |  Simplicial Database        |
|  (RDF baseline)  |  (primary)       |  (secondary)                |
+------------------+------------------+----------------------------+
|  SPO/POS/OSP     |  Context/Stalk   |  Simplex/Incidence          |
|  indexes         |  Restriction/    |  Boundary/Dimension         |
|                  |  Neighbourhood   |  indexes                    |
+------------------+------------------+----------------------------+
                            |
                            v
+------------------------------------------------------------------+
|                      Execution Engine                             |
|                    (common query interface)                       |
+------------------------------------------------------------------+
                            |
                            v
+------------------------------------------------------------------+
|                    Canonical Results                              |
|              (verifiable, comparable, benchmarkable)               |
+------------------------------------------------------------------+
```

## Module Responsibilities

### Parser
Parses a query string into a LogicalPlan.  Representation-agnostic.
Input: query text.  Output: LogicalPlan.

### Validator
Checks SemanticFact invariants (immutability, identifier uniqueness,
confidence bounds, temporal consistency).  Operates on the canonical
model only.

### Serializer
Converts SemanticFact to/from bytes.  Supports JSON (human-readable),
Parquet (columnar), and MessagePack (compact binary).  Deterministic
and lossless.

### Importer
Bulk-loads data from external formats (JSON, RDF/XML, Turtle, CSV)
into the canonical model.  Returns a list of SemanticFact instances.

### Exporter
Exports canonical facts to various output formats.  Symmetric to the
Importer.

### Storage (Logical Layer)
Defines the schema, types, and constraints for each engine.  Maps
SemanticFact fields to engine-specific data structures.  Provides
the CRUD interface that the execution engine calls.

### Indexes
Maintains auxiliary data structures for fast lookup:

- **KG**: SPO, POS, OSP indexes.
- **SheafDB**: Context Index, Stalk Index, Restriction Index,
  Neighbourhood Index, Global Section Cache.
- **SimplicialDB**: Simplex Index, Incidence Matrix, Boundary
  Operator, Dimension Index.

All indexes are engine-private and not exposed through the common API.

### Query Planner
Transforms a Query (logical) into an ExecutionPlan (physical).  The
same logical query produces different physical plans for each engine.

### Query Optimizer
Applies cost-based optimisation rules to the physical plan.  Each
engine has its own optimizer with engine-specific cost models.

### Execution Engine
Executes a physical plan against the storage engine.  Returns a
QueryResult containing canonical SemanticFact instances.

### Statistics
Tracks cardinalities, index sizes, operation counts.  Used by the
optimizer for cost estimation and by the benchmark for reporting.

### Visualisation
Generates plots (latency, memory, storage, scaling) from benchmark
results.  Uses matplotlib.  Not part of the critical query path.

### Benchmark Runner
Orchestrates benchmark execution across all engines.  Collects
metrics (latency, memory, CPU).  Verifies semantic equivalence.
Generates benchmark reports.

### Paper Generator
Produces LaTeX output with embedded tables and figures from
benchmark results.  Not part of the runtime.

## Database Engines

### Knowledge Graph (KG)
- **Type**: Baseline / control group.
- **Storage**: TripleStore with SPO/POS/OSP hash indexes.
- **Facts**: N-ary facts are decomposed via reification into binary
  triples.
- **Queries**: Graph traversal and join-based.
- **Optimiser**: Standard RDF query optimisation (triple pattern
  reordering, selectivity estimation).

### Sheaf Database (SheafDB)
- **Type**: Primary research contribution.
- **Storage**: SheafStore with context-indexed sections.
- **Facts**: Stored directly as n-ary sections without decomposition.
- **Queries**: Restriction-map-based localisation + gluing for global
  sections.
- **Optimiser**: Context selectivity estimation, restriction pushdown.

### Simplicial Database (SimplicialDB)
- **Type**: Secondary mathematical approach.
- **Storage**: SimplicialSet with incidence matrices and boundary
  operators.
- **Facts**: Stored as simplices (n-simplex for arity-n fact).
- **Queries**: Face / degeneracy operations, boundary computation,
  homology computation.
- **Optimiser**: Dimension pruning, face-map caching.

## Common API (DatabaseEngine)

Every engine implements the same ABC:

| Method               | Description                              |
|----------------------|------------------------------------------|
| `create(config)`     | Initialise storage and indexes           |
| `drop()`             | Destroy all data                         |
| `insert(fact)`       | Store a SemanticFact                     |
| `update(id, fact)`   | Replace a fact                           |
| `delete(id)`         | Remove a fact                            |
| `query(query)`       | Execute a logical query                  |
| `explain(query)`     | Return execution plan (no execution)     |
| `statistics()`       | Return engine statistics                 |
| `verify()`           | Run consistency checks                   |
| `export(fmt)`        | Export all facts as bytes               |
| `import(data, fmt)`  | Import facts from bytes                 |

## Query Pipeline

```
User Query (string)
       |
       v
   +--------+
   | Parser |  representation-agnostic
   +--------+
       |
       v
   +----------+
   | Logical  |  QueryPattern / Query type
   | Plan     |
   +----------+
       |
       v
   +-----------+
   | Optimizer |  cost-based; engine-specific
   +-----------+
       |
       v
   +-----------+
   | Physical  |  ExecutionPlan (engine-native operations)
   | Plan      |
   +-----------+
       |
       v
   +----------------+
   | Execution      |  runs against storage engine
   | Engine         |
   +----------------+
       |
       v
   +-----------------+
   | CanonicalResult |  list of SemanticFact instances
   +-----------------+
       |
       v
   +----------+
   | Validate |  verify invariants on results
   +----------+
       |
       v
   +-----------------+
   | Benchmark       |  collect metrics, compare engines
   | Collection      |
   +-----------------+
```

## Storage Layers

### Logical Layer
- Schema definitions.
- Type validation.
- Constraint enforcement (referential integrity, uniqueness).
- Mapping from SemanticFact to logical rows / sections / simplices.

### Physical Layer
- Index structures (B-tree, hash table, adjacency list).
- Data layout (row-major, column-major, adjacency).
- Buffer management (page caching, write-ahead logging).
- Compression.

### Persistence Layer
- Serialisation format (JSON, Parquet, MessagePack).
- File I/O.
- Import / export.

## Indexes

### KG Indexes
- **SPO**: subject -> predicate -> object mapping.
- **POS**: predicate -> object -> subject mapping.
- **OSP**: object -> subject -> predicate mapping.
- Optional: 6-way (all permutations of SPO).

### SheafDB Indexes
- **Context Index**: context -> list of sections.
- **Stalk Index**: entity -> contexts where it appears.
- **Restriction Index**: (broad context, narrow context) -> restriction
  map.
- **Neighbourhood Index**: context -> adjacent contexts (parents,
  children).
- **Global Section Cache**: cached result of gluing all local sections.

### SimplicialDB Indexes
- **Simplex Index**: simplex id -> vertices.
- **Incidence Matrix**: (n-1)-simplex -> list of n-simplices that
  contain it.
- **Boundary Operator**: pre-computed `partial_n` for each dimension.
- **Dimension Index**: dimension -> list of simplices.

## Query Types

| Type          | Description                                      |
|---------------|--------------------------------------------------|
| LOOKUP        | Retrieve a specific fact by ID or pattern        |
| PATH          | Traverse relations from a starting entity        |
| CONTEXT       | Retrieve all facts in a given context            |
| TEMPORAL      | Filter facts by temporal validity                |
| AGGREGATION   | Count, sum, or group facts                       |
| MIXED         | Combination of multiple query types               |
| PROVENANCE    | Filter or trace by provenance                    |
| NEIGHBOURHOOD | Find facts within k steps of an entity           |
| CONSISTENCY   | Check for contradictions across contexts          |
| GLOBAL        | Retrieve all facts valid in the root context     |

## Exception Hierarchy

```
SFDBError
├── StorageError
│   └── IndexError
├── ConsistencyError
│   ├── ReferentialIntegrityError
│   └── GluingError
├── QueryError
│   ├── QueryParseError
│   └── QueryExecutionError
├── ValidationError
├── SerializationError
├── BenchmarkError
└── ConfigError
```

## Benchmark Pipeline

```
+------------------+
| Synthetic Data   |  generate_facts(), generate_random_graph()
+------------------+
         |
         v
+------------------+
| Insert into all  |  same SemanticFacts -> each engine
| engines          |
+------------------+
         |
         v
+------------------+
| Warm-up runs     |  configurable count
+------------------+
         |
         v
+------------------+
| Measured runs    |  collect latency, memory, CPU
+------------------+
         |
         v
+------------------+
| Verify semantic  |  compare canonical results
| equivalence      |
+------------------+
         |
         v
+------------------+
| Collect metrics  |  aggregate across runs
+------------------+
         |
         v
+------------------+
| Generate report  |  tables, figures, LaTeX
+------------------+
```