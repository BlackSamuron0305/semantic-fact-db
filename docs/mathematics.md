# Mathematical Notes

## Sheaf Theory for Knowledge Representation

### Motivation

Traditional knowledge graphs represent facts as triples (subject, predicate, object).
N-ary facts (e.g., "Alice gave Bob a book on Tuesday") must be decomposed into
multiple triples via reification:

```
_:stmt1 rdf:type rdf:Statement .
_:stmt1 rdf:subject alice .
_:stmt1 rdf:predicate gave .
_:stmt1 rdf:object bob .
_:stmt1 rdf:object book .
_:stmt1 dc:date "Tuesday" .
```

This decomposition loses the intrinsic structure of the event and requires
joins to reconstruct.

### Sheaf-Theoretic Alternative

A sheaf over a poset of contexts preserves the n-ary structure directly:

```
Section({gave, alice, bob, book, "Tuesday"}, context=world.2024)
```

The context poset provides:
- **Refinement**: `world.2024` ≤ `world` (the fact holds in both)
- **Restriction**: A fact in `world` is also valid in `world.2024`
- **Gluing**: Facts in `world.2024.physics` and `world.2024.biology` that agree on `world.2024` can be glued

### Formal Details

#### Presheaf Axioms

For a poset (C, ≤):

1. For each c ∈ C, F(c) is a set of facts (sections).
2. For each c₁ ≤ c₂, ρ_{c₂,c₁}: F(c₂) → F(c₁) is a restriction map.
3. ρ_{c,c} = id_{F(c)}
4. ρ_{c₃,c₁} = ρ_{c₂,c₁} ∘ ρ_{c₃,c₂} for c₁ ≤ c₂ ≤ c₃

#### Sheaf Condition (Gluing)

Given a cover {cᵢ} of c and sections sᵢ ∈ F(cᵢ) such that for all i, j:

ρ_{cᵢ, cᵢ∧cⱼ}(sᵢ) = ρ_{cⱼ, cᵢ∧cⱼ}(sⱼ)

there exists a unique s ∈ F(c) with ρ_{c,cᵢ}(s) = sᵢ for all i.

#### Locality

If s, t ∈ F(c) and ρ_{c,cᵢ}(s) = ρ_{c,cᵢ}(t) for all i in a cover of c,
then s = t.

### Computational Implications

1. **No decomposition**: N-ary facts are stored directly, eliminating
   the need for joins during reconstruction.
2. **Local queries**: A query in context c only examines F(c) and
   restrictions from super-contexts — not the entire database.
3. **Consistency via gluing**: The sheaf condition ensures that
   locally compatible facts can be combined uniquely.
4. **Global sections**: Facts that hold in all contexts are identified
   by restricting all sections to the root context.

### Comparison to RDF

| Aspect | RDF/KG | SheafDB |
|--------|--------|---------|
| Atomic unit | Triple | Section (n-ary fact + context) |
| N-ary facts | Decompose + reification | Direct representation |
| Queries | Graph traversal + joins | Restriction maps |
| Consistency | External validation | Sheaf condition |
| Context | Named graphs (optional) | Intrinsic to representation |

### Open Questions

1. Does the sheaf representation scale to millions of facts?
2. How does the choice of covering affect gluing performance?
3. Can restriction maps be learned or inferred automatically?
4. What is the optimal context hierarchy for a given domain?
