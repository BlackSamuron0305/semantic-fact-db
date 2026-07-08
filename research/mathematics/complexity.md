# Complexity Analysis

This document analyses the computational complexity of SheafDB operations.
All analyses are under the standard RAM model with uniform cost for
basic operations (hash lookup, pointer dereference, arithmetic).

**Notation:**
- $N$ = number of facts in the knowledge state.
- $k$ = arity of a fact (number of object slots).
- $|\mathcal{C}|$ = number of contexts.
- $d$ = depth of a context in the poset.
- $T$ = number of triples in KG representation.
- $R$ = number of restriction maps.
- $n$ = result size (number of returned facts).

---

## Axiomatic Complexity Classes

### Fact Construction

Constructing a `Fact` requires building the object tuple:
- Time: $O(k)$
- Space: $O(k + m)$ where $m$ = metadata size

### Fact Insertion

**KG (baseline):**
1. Decompose into $2 + k$ reified triples: $O(k)$.
2. Insert each triple into SPO/POS/OSP indices: $O(k \log T)$ hash.
Total: $O(k + \log T)$ amortized.

**Sheaf:**
1. Store fact in its assigned context section: $O(1)$ hash insert.
2. Register fact with open sets: $O(|\mathcal{T}|)$ worst case,
   $O(d)$ amortized (where $d$ = depth, since context chain is known).
Total: $O(d)$ amortized, $O(|\mathcal{C}|)$ worst case.

### Fact Deletion

**KG:**
1. Look up reified triples: $O(\log T)$.
2. Remove $2 + k$ triples from three indices: $O(k \log T)$.
Total: $O(k \log T)$.

**Sheaf:**
1. Remove from context section: $O(1)$ hash delete.
2. Remove from all open sets containing the fact: $O(|\mathcal{C}|)$ worst case.
Total: $O(|\mathcal{C}|)$ worst case.

---

## Query Complexity

### Context Lookup

**KG:** Subject-predicate-object index scan.
- Time: $O(\log T + n)$ where $n$ = facts matching the pattern.

**Sheaf:** Direct open set lookup.
- Time: $O(|\mathcal{C}| + n)$ to find the open set, then $O(n)$ to collect
  sections. With a context-to-open-set index: $O(\log |\mathcal{C}| + n)$.

### Restriction

Given a fact $f$ with arity $k$ and contexts $c \leq d$:

1. Filter object slots meaningful in $c$: $O(k)$.
2. Specialize values: $O(k)$.
Total: $O(k)$.

This is independent of $N$: restriction operates on individual facts.

### Global Sections (Gluing)

The algorithm processes the context poset bottom-up:

1. **Leaf collection:** Scan all facts to identify those at minimal
   (most specific) contexts: $O(N)$.

2. **Bottom-up gluing:** For each non-leaf context $c$, check all
   sub-context pairs:
   - Number of contexts: $|\mathcal{C}|$.
   - Number of sections per context: up to $N$.
   - Pairwise compatibility checks per level: $O(N^2)$ worst case.
   - With overlap caching: $O(N \log |\mathcal{C}|)$ expected.

3. **Worst case:** $O(|\mathcal{C}| \cdot N^2)$ for a fully-connected
   context lattice with incompatible sections.
   **Expected case:** $O(N \log |\mathcal{C}|)$ for tree-structured
   contexts with most sections being compatible.

### Neighborhood Search

Given a point $x$ with minimal neighbourhood $\mathcal{B}(x)$:

1. Compute $\mathcal{B}(x) = \downarrow \alpha(x)$: $O(1)$ with context index.
2. Expand outward by adding parent contexts: $O(d)$ steps.
3. Collect sections in each neighbourhood: $O(n)$ cumulative.

Total: $O(d + n)$.

### Temporal Search

If facts carry temporal bounds:

1. **No temporal index:** $O(N)$ full scan to filter by interval overlap.
2. **With temporal index** (e.g., interval tree): $O(\log N + n)$.

---

## Space Complexity

| Component | KG | Sheaf | Notes |
|-----------|----|-------|-------|
| Per fact | $O(k \cdot 3)$ triples + indices | $O(1)$ section + $O(d)$ restriction entries | KG has 3x index amplification |
| Context poset | $O(1)$ (not stored) | $O(|\mathcal{C}|^2)$ for topology | Sheaf stores the poset explicitly |
| Restriction maps | N/A | $O(R) \leq O(|\mathcal{C}| \cdot N)$ | Upper bound, typically much less |
| Indices | $O(T)$ via SPO/POS/OSP | $O(N + |\mathcal{C}|)$ via context hash | KG uses more indices |

---

## Summary Table

| Operation | Knowledge Graph | Sheaf Database |
|-----------|----------------|----------------|
| Insert | $O(k \log T)$ | $O(d)$ |
| Delete | $O(k \log T)$ | $O(|\mathcal{C}|)$ |
| Context Lookup | $O(\log T + n)$ | $O(\log |\mathcal{C}| + n)$ |
| Restriction | N/A (triple-oriented) | $O(k)$ |
| Global Sections | N/A (no gluing) | $O(|\mathcal{C}| \cdot N^2)$ worst, $O(N \log |\mathcal{C}|)$ expected |
| Neighborhood Search | $O(\log T + n)$ | $O(d + n)$ |
| Temporal Search | $O(\log T + n)$ | $O(N)$ without index, $O(\log N + n)$ with index |
| Consistency Check | N/A | $O(|\mathcal{C}| \cdot N^2)$ |
| Storage per fact | $O(k \cdot 3)$ | $O(1 + d)$ |

---

## Empirical Verification

These asymptotic bounds are tested empirically by the benchmark framework.
See `docs/benchmarking.md` for the experimental methodology and
`paper/sections/evaluation.tex` for results.

**Hypotheses to be tested:**
1. SheafDB insertion is $O(d)$ vs KG's $O(k \log T)$ for contexts of depth $d$.
2. SheafDB contextual queries are faster than KG pattern queries for highly
   nested contexts.
3. KG joins outperform SheafDB gluing for non-contextual queries.
4. The expected-case $O(N \log |\mathcal{C}|)$ gluing complexity holds for
   tree-structured context hierarchies.
