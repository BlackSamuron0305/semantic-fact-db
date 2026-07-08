# Sheaf Mapping — Canonical SemanticFact to Sheaf Sections

## Formal Definition

Let \(\mathcal{F}\) be the set of all possible `SemanticFact` instances and let \(\mathcal{S}\) be the set of all possible sheaf stores over a context poset \(C\). Define a mapping

\[
\sigma: \mathcal{F} \to \mathcal{S}
\]

that sends a single canonical fact to a local section in its maximal context.

### Notation

For a fact \(f \in \mathcal{F}\) we use the same notation as in `kg_mapping.md`. Additionally, let:

- \(C\) be the finite poset of contexts, partially ordered by specificity: \(c_1 \leq c_2\) iff \(c_1\) is a sub-context (more specific) of \(c_2\).
- The root context is \(c_0 = \text{"world"}\), the broadest scope.
- Contexts are dot-separated paths: \(\text{"world.contracts.2024"}\) subsumes \(\text{"world.contracts"}\) which subsumes \(\text{"world"}\).

### Presheaf Construction

Define a presheaf \(P: C^{\mathrm{op}} \to \mathbf{Set}\) as follows:

- For each context \(c \in C\), \(P(c)\) is the set of `SemanticFact` instances whose context is exactly \(c\). These are the *local sections* at \(c\).
- For each pair \(c_1 \leq c_2\) (i.e., \(c_1\) is a sub-context of \(c_2\)), define the restriction map:

\[
\rho_{c_2, c_1}: P(c_2) \to P(c_1)
\]

by:

\[
\rho_{c_2, c_1}(f) = \begin{cases}
f & \text{if } \mathrm{ctx}(f) \text{ is in the sub-context hierarchy of } c_1 \\
\text{undefined} & \text{otherwise}
\end{cases}
\]

In the implementation, restriction is not a deep copy; it is a view on the same underlying fact. The restriction map returns the fact unchanged because a fact valid in a broader context remains valid in any sub-context. This satisfies the sheaf locality condition trivially: if two sections agree on all sub-contexts, they are identical.

### Sheaf Condition Verification

**Locality**: Suppose \(s, t \in P(c)\) and for every cover \(\{c_i\}\) of \(c\) we have \(\rho_{c,c_i}(s) = \rho_{c,c_i}(t)\). Since \(\rho\) is either identity or undefined, this implies \(s = t\) in all contexts where both are defined.

**Gluing**: Let \(\{c_i\}\) be a cover of \(c\) and let \(s_i \in P(c_i)\) be sections such that for all \(i, j\), \(\rho_{c_i, c_i \land c_j}(s_i) = \rho_{c_j, c_i \land c_j}(s_j)\). Define \(s \in P(c)\) as:

\[
s = \bigcup_i s_i
\]

provided no two \(s_i\) assign conflicting values to the same identifier field. The uniqueness follows from the fact that `SemanticFact` is an immutable value type: if two sections agree on overlaps, their union is well-defined.

### Mapping Rules

The mapping \(\sigma\) sends a fact \(f\) to a sheaf store as follows:

1. **Context assignment**: The fact is stored as a section in the context \(\mathrm{ctx}(f)\) within the poset \(C\).

2. **Sub-context propagation**: The fact is also implicitly present in all sub-contexts of \(\mathrm{ctx}(f)\) via restriction. No explicit duplication occurs; restriction is a logical view.

3. **Cover computation**: The set of contexts that cover \(\mathrm{ctx}(f)\) is computed from the poset. A cover is a set of sub-contexts whose join equals \(\mathrm{ctx}(f)\) and whose pairwise meets are maximal.

4. **Stalk construction**: At each context \(c \in C\), the stalk \(\mathcal{F}_c\) is the set of all facts whose context is \(c\) or a super-context of \(c\). Stalks are not precomputed; they are evaluated on demand by collecting sections from the context and all ancestors in the poset.

5. **Global section**: A global section is a consistent assignment of a fact to every context in the poset. In practice, global sections are computed by gluing compatible local sections along their overlaps.

### Example: SIGNED Event

The same SIGNED fact from `kg_mapping.md`:

```python
SemanticFact(
    id=Identifier("fact-001"),
    subject=Identifier("alice"),
    relation=Identifier("signed"),
    objects=(...),
    attributes={"regulation": Value.literal("GDPR")},
    context=Context("world.contracts.2024"),
    ...
)
```

is stored as a section in the context `"world.contracts.2024"`:

```
Section(fact-001, "world.contracts.2024")
```

Restriction to sub-contexts:
```
ρ("world.contracts.2024", "world.contracts.2024.Q1")(fact-001) = fact-001  (view)
ρ("world.contracts.2024", "world.contracts.2024.Q2")(fact-001) = fact-001  (view)
```

Gluing: If another fact with the same `id` exists in `"world.contracts.2024.Q1"` with different confidence, the gluing fails — a consistency violation is raised.

### Inverse Mapping

Define \(\sigma^{-1}: \mathcal{S} \to \mathcal{F}\) by:

For a given section \(s\) in context \(c\), reconstruct the `SemanticFact` by reading the fact data stored at the section. Since a section IS a `SemanticFact` (the presheaf stores canonical facts directly), the inverse is:

\[
\sigma^{-1}(s) = s
\]

**Theorem**: \(\sigma\) is injective and \(\sigma^{-1}\) is a left inverse: \(\sigma^{-1}(\sigma(f)) = f\) for all \(f \in \mathcal{F}\). The mapping is lossless because the fact is stored verbatim as a section; no decomposition or transformation occurs.

## Comparison with KG Mapping

| Property | KG Mapping (\(\kappa\)) | Sheaf Mapping (\(\sigma\)) |
|---|---|---|
| Storage form | Decomposed into \(O(n + 8)\) triples | Stored verbatim as canonical fact |
| Reconstruction | \(O(n + 8)\) triple pattern joins | O(1) direct read |
| Context support | Triple filter (scan) | Native poset indexing |
| Consistency check | Requires SPARQL CONSTRUCT | Built-in gluing check |
| Storage overhead | \(3\times\)–\(5\times\) canonical size | 1\(\times\) canonical size |
| Query cost (contextual) | Full index scan | Sub-poset traversal only |

## Open Sets and Their Meaning

In the sheaf model, each context \(c \in C\) corresponds to an open set in the Alexandrov topology on \(C\). The open sets are exactly the upward-closed subsets: if \(c \in U\) and \(c \leq c'\) then \(c' \in U\). For semantic facts:

- An open set corresponds to a "scope of validity": all contexts that subsume a given context.
- A local section at \(c\) is a fact that is valid in the open set of all sub-contexts of \(c\).
- The intersection of two open sets corresponds to the greatest lower bound (meet) of two contexts.
- A cover of \(c\) is a collection of sub-contexts whose join equals \(c\).

## Restriction Maps in Practice

Restriction maps are implemented as lazy views:

```python
def restrict(fact: SemanticFact, target: Context) -> SemanticFact | None:
    if fact.context <= target:  # fact's context is a sub-context of target
        return fact
    return None
```

No data movement occurs. The restriction check is a string prefix comparison on the dot-separated context paths.

## Stalks in Practice

The stalk at context \(c\) is the set of all facts whose context is \(c\) or a sub-context of \(c\). Stalk evaluation:

```python
def stalk(c: Context, store: SheafStore) -> list[SemanticFact]:
    return [f for f in store.all_sections()
            if f.context <= c or c in f.context.ancestors()]
```

This is a linear scan in the naive implementation; indexes on context prefix can reduce it to \(O(\log |C|)\) lookup.

## References

[1] S. Mac Lane and I. Moerdijk, *Sheaves in Geometry and Logic*. Springer, 1992.
[2] P. T. Johnstone, *Sketches of an Elephant: A Topos Theory Compendium*. Oxford University Press, 2002.
[3] R. H. G. H.  Tan, "Sheaf-theoretic data models," *Category Theory and Computer Science*, 2004.
