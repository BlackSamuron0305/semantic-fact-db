# Knowledge Graph Mapping — Canonical SemanticFact to RDF Triples

## Formal Definition

Let \(\mathcal{F}\) be the set of all possible `SemanticFact` instances and let \(\mathcal{T}\) be the set of all possible RDF triple stores. Define a mapping

\[
\kappa: \mathcal{F} \to \mathcal{T}
\]

that sends a single canonical fact to a finite set of triples.

### Notation

For a fact \(f \in \mathcal{F}\) we write:

- \(\mathrm{id}(f)\) — the fact's unique identifier
- \(\mathrm{subj}(f)\) — the subject entity
- \(\mathrm{rel}(f)\) — the relation type
- \(\mathrm{obj}(f)\) — the tuple of object values \((o_1, \dots, o_n)\)
- \(\mathrm{attr}(f)\) — the mapping of attribute keys to values
- \(\mathrm{ctx}(f)\) — the context string
- \(\mathrm{prov}(f)\) — the provenance record
- \(\mathrm{conf}(f)\) — the overall confidence
- \(\mathrm{temp}(f)\) — the optional temporal interval

### Mapping Rules

A `SemanticFact` is mapped to triples as follows:

1. **Event node**: An anonymous event node \(e\) (a blank node or a named node derived from \(\mathrm{id}(f)\)) is created to represent the fact itself.

2. **Type declaration**:
   \[
   (e, \text{rdf:type}, \text{sfdb:Fact})
   \]

3. **Subject triple**:
   \[
   (e, \text{sfdb:subject}, \mathrm{subj}(f))
   \]

4. **Relation triple**:
   \[
   (e, \text{sfdb:relation}, \mathrm{rel}(f))
   \]

5. **Object triples**: For each \(i = 1..n\):
   \[
   (e, \text{sfdb:object}_i, o_i)
   \]
   where \(\text{sfdb:object}_i\) is a role-specific predicate (or simply \(\text{sfdb:object}\) with position encoded in an attached triple).

6. **Attribute triples**: For each \((k, v) \in \mathrm{attr}(f)\):
   \[
   (e, \text{sfdb:attr}_k, v)
   \]

7. **Context triple**:
   \[
   (e, \text{sfdb:context}, \mathrm{ctx}(f))
   \]

8. **Provenance triples**:
   \[
   (e, \text{sfdb:provenanceSource}, \mathrm{prov}(f).\text{source})
   \]
   \[
   (e, \text{sfdb:provenanceRecordedAt}, \mathrm{prov}(f).\text{recordedAt})
   \]
   \[
   (e, \text{sfdb:provenanceConfidence}, \mathrm{prov}(f).\text{confidence})
   \]
   \[
   (e, \text{sfdb:provenanceMethod}, \mathrm{prov}(f).\text{method})
   \]

9. **Confidence triple**:
   \[
   (e, \text{sfdb:confidence}, \mathrm{conf}(f))
   \]

10. **Temporal triples** (if \(\mathrm{temp}(f) \neq \text{None}\)):
    \[
    (e, \text{sfdb:temporalStart}, \mathrm{temp}(f).\text{start})
    \]
    \[
    (e, \text{sfdb:temporalEnd}, \mathrm{temp}(f).\text{end})
    \]

The total number of triples generated is:
\[
|\kappa(f)| = 4 + n + |\mathrm{attr}(f)| + 1 + 4 + 1 + (0 \text{ or } 2)
\]

where:
- 4 = rdf:type + subject + relation + context
- \(n\) = arity (number of object slots)
- \(|\mathrm{attr}(f)|\) = number of attributes
- 1 = confidence
- 4 = provenance fields
- 0 or 2 = temporal (optional)

### Example: SIGNED Event

Consider the fact:

```python
SemanticFact(
    id=Identifier("fact-001"),
    subject=Identifier("alice"),
    relation=Identifier("signed"),
    objects=(
        Value.reference(Identifier("contract-42")),
        Value.literal("2024-03-15"),
        Value.reference(Identifier("acme-corp")),
    ),
    attributes={"regulation": Value.literal("GDPR")},
    context=Context("world.contracts.2024"),
    provenance=Provenance(source="hr-system", confidence=0.95),
    confidence=0.98,
)
```

This generates the following triples:

```
_:fact-001 rdf:type         sfdb:Fact .
_:fact-001 sfdb:subject     alice .
_:fact-001 sfdb:relation    signed .
_:fact-001 sfdb:object_1    contract-42 .
_:fact-001 sfdb:object_2    "2024-03-15" .
_:fact-001 sfdb:object_3    acme-corp .
_:fact-001 sfdb:attr_regulation "GDPR" .
_:fact-001 sfdb:context     "world.contracts.2024" .
_:fact-001 sfdb:provenanceSource         "hr-system" .
_:fact-001 sfdb:provenanceRecordedAt     "2026-07-08T..."^^xsd:dateTime .
_:fact-001 sfdb:provenanceConfidence     0.95 .
_:fact-001 sfdb:provenanceMethod         "unknown" .
_:fact-001 sfdb:confidence               0.98 .
```

### Inverse Mapping

Define \(\kappa^{-1}: \mathcal{T} \to \mathcal{F}\) on a set of triples sharing the same event node \(e\):

1. Collect all triples with subject \(e\).
2. Extract \(\mathrm{subj}(f)\) from the `sfdb:subject` triple.
3. Extract \(\mathrm{rel}(f)\) from the `sfdb:relation` triple.
4. Extract \(\mathrm{obj}(f)\) by collecting all `sfdb:object_i` predicates in order.
5. Extract \(\mathrm{attr}(f)\) from all `sfdb:attr_*` predicates.
6. Extract \(\mathrm{ctx}(f)\) from the `sfdb:context` triple.
7. Extract \(\mathrm{prov}(f)\) from the `sfdb:provenance*` triples.
8. Extract \(\mathrm{conf}(f)\) from the `sfdb:confidence` triple.
9. Extract \(\mathrm{temp}(f)\) from `sfdb:temporalStart`/`sfdb:temporalEnd` (if present).
10. Reconstruct the `SemanticFact`.

**Theorem**: \(\kappa\) is injective and \(\kappa^{-1}\) is a left inverse: \(\kappa^{-1}(\kappa(f)) = f\) for all \(f \in \mathcal{F}\). The mapping is lossless because every field of `SemanticFact` is encoded in a dedicated predicate; no information is elided.

## Advantages

- **Standard compliant**: Uses standard RDF/SPARQL infrastructure.
- **Queryable**: Individual fields can be queried directly via SPO patterns.
- **Interoperable**: Can be merged with existing RDF datasets.

## Limitations

- **Triple count explosion**: An \(n\)-ary fact generates \(O(n + |\mathrm{attr}|)\) triples; high-arity facts incur significant storage overhead.
- **Join complexity**: Reconstructing a single fact requires up to \(n + |\mathrm{attr}| + 8\) triple pattern joins.
- **No native context indexing**: Context is encoded as a triple; contextual queries require full scan or a secondary index.
- **Reification overhead**: Each fact requires a dedicated event node, which is RDF reification with its well-known performance penalties [1].

## Query Implications

| Query Type | KG Strategy | Joins Required |
|---|---|---|
| Point lookup (by entity) | Find all event nodes with matching `sfdb:subject` | 1 |
| Pattern match (subject + relation) | SPO index scan | 1 |
| Multi-way join | Chain through event nodes | O(path length) |
| Contextual query | Filter by `sfdb:context` value | 1 filter + reconstruction |
| Global section (all facts) | Full scan | 1 |

## Storage Implications

- **Indexes**: Three indexes (SPO, POS, OSP) are sufficient for all patterns.
- **Reconstruction cost**: Each fact reconstruction requires \(O(n + |\mathrm{attr}|)\) lookups.
- **Storage overhead**: Each fact's triple representation is approximately \(3\times\) to \(5\times\) larger than the canonical form due to predicate repetition.

## References

[1] H. J. ter Horst, "Completeness, decidability and complexity of entailment for RDF Schema and a semantic extension involving the OWL vocabulary," *Journal of Web Semantics*, 2005.
