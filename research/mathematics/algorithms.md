# Algorithms

> Pseudocode for all core operations. Complexity analysis follows in `complexity.md`.

---

## Algorithm 1: Topology Construction

```text
ConstructTopology(C)
    Input:  Context poset C = (C_set, ≤)
    Output: Finite topological space (X, T)

    X ← C_set                                    // points = contexts
    T ← ∅                                        // topology (open sets)

    for each c in C_set:
        U_c ← { d ∈ C_set | d ≤ c }              // down-set of c
        T ← T ∪ { U_c }

    // Close under finite intersection
    changed ← true
    while changed:
        changed ← false
        for each pair (U, V) in T × T:
            W ← U ∩ V
            if W ≠ ∅ and W ∉ T:
                T ← T ∪ { W }
                changed ← true

    return (X, T)
```

**Implementation:** `FiniteTopologicalSpace.__init__()`, `add_open_set()`, `intersection_closure()` in `sfdb.sheaf.topology.py`.

---

## Algorithm 2: Restriction Map Construction

```text
BuildRestrictionMap(F, c, d)
    Input:  Presheaf F, contexts c ≤ d
    Output: Restriction function ρ_{d,c}: F(d) → F(c)

    function ρ(f):
        // f = (i, s, r, [o_1, ..., o_n], d, k, m)
        o' ← []
        for each o_j in f.objects:
            if IsMeaningfulInContext(o_j, c):
                o'.append(SpecializeValue(o_j, c))
            // else: drop this object slot
        return (f.id, f.subject, f.relation, o', c, f.confidence, f.metadata)

    return ρ
```

**Implementation:** `Presheaf.restrict()` in `sfdb.sheaf.sheaf.py`.

---

## Algorithm 3: Stalk Construction

```text
ComputeStalk(F, x, T)
    Input:  Presheaf F, point x, topology T
    Output: Stalk F_x (set of germs)

    N_x ← { U ∈ T | x ∈ U }                     // neighbourhood filter
    stalk_elems ← ∅

    for each U in N_x:
        for each s in F(U):                      // sections over U
            germ ← [(s, U)]                       // equivalence class rep
            stalk_elems ← stalk_elems ∪ { germ }

    // Merge equivalent germs
    for each pair (g1, g2) in stalk_elems × stalk_elems:
        let (s1, U1) = representative(g1)
        let (s2, U2) = representative(g2)
        W ← U1 ∩ U2
        if x ∈ W and ρ_{U1,W}(s1) = ρ_{U2,W}(s2):
            Merge(g1, g2)                         // same germ

    return stalk_elems
```

**Note:** Stalk computation is primarily a theoretical construct for proofs. The implementation does not explicitly construct stalks; instead, it works directly with sections and restriction maps.

---

## Algorithm 4: Neighbourhood Expansion

```text
ExpandNeighbourhood(F, x, depth_max)
    Input:  Presheaf F, point x, max depth
    Output: Sequence of neighbourhoods B_0 ⊆ B_1 ⊆ ... ⊆ B_max

    c ← context(x)
    B_0 ← MinimalNeighbourhood(x)               // = ↓c

    for depth = 1 to depth_max:
        // Add all contexts at distance ≤ depth from c in the poset
        candidates ← { d ∈ C | d ≤ c and depth(d) = depth(c) + depth }
        B_depth ← B_{depth-1}
        for each d in candidates:
            B_depth ← B_depth ∪ ↓d
        yield B_depth
```

**Implementation:** `FiniteTopologicalSpace.neighborhoods()` in `sfdb.sheaf.topology.py`.

---

## Algorithm 5: Global Section Computation

```text
ComputeGlobalSections(F, C)
    Input:  Sheaf F over context poset C
    Output: Set of global sections Γ(C, F)

    // Phase 1: Collect local sections at leaf contexts
    leaves ← { c ∈ C | ∄ d < c }                // minimal contexts
    sections ← { (c, F(c)) for c in leaves }

    // Phase 2: Work upward by gluing
    top ← root(C)
    processed ← ∅
    queue ← leaves

    while queue is not empty:
        current ← pop(queue)
        if current = top:
            break

        parent ← immediate_supercontext(current)
        if all subcontexts of parent are processed:
            // Try to glue sections over subcontexts to parent
            sub_sections ← { (c, F(c)) for c in children(parent) }
            compatible ← true

            for each pair ((c1, s1), (c2, s2)) in sub_sections × sub_sections:
                overlap ← c1 ∧ c2
                r1 ← ρ_{c1, overlap}(s1)          // restrict s1 to overlap
                r2 ← ρ_{c2, overlap}(s2)
                if r1 ≠ r2:
                    compatible ← false

            if compatible:
                // Glue: the unique section over parent is determined
                // by the compatible family
                F(parent) ← UniqueExtension(sub_sections, parent)
                processed ← processed ∪ { parent }
                queue ← queue ∪ { parent }

    return F(top)                                 // global sections
```

**Implementation:** `Sheaf.global_sections()` in `sfdb.sheaf.sheaf.py`.

---

## Algorithm 6: Consistency Verification

```text
VerifyConsistency(F, C)
    Input:  Sheaf F over context poset C
    Output: Boolean (consistent or inconsistent)

    // Check locality: sections uniquely determined by their restrictions
    for each c in C:
        children_c ← { d ∈ C | d < c and ∄ e: d < e < c }
        for each pair (s, t) in F(c) × F(c):
            agree ← true
            for each d in children_c:
                if ρ_{c,d}(s) ≠ ρ_{c,d}(t):
                    agree ← false
                    break
            if agree and s ≠ t:
                return false                       // locality violated

    // Check gluing: compatible families extend uniquely
    for each c in C:
        children_c ← { d ∈ C | d < c and ∄ e: d < e < c }
        // Build compatible families from sub-context sections
        for each assignment (s_d ∈ F(d) for d in children_c):
            compatible ← true
            for each pair (d1, d2) in children_c × children_c:
                overlap ← d1 ∧ d2
                if ρ_{d1, overlap}(s_d1) ≠ ρ_{d2, overlap}(s_d2):
                    compatible ← false
            if compatible:
                // Verify extension exists in parent
                if ∄ s ∈ F(c) such that ∀d: ρ_{c,d}(s) = s_d:
                    return false                   // gluing fails

    return true                                    // consistent
```

**Implementation:** `Sheaf.glue()` in `sfdb.sheaf.sheaf.py`.

---

## Algorithm 7: Query Translation

```text
TranslateQuery(Q, engine_type)
    Input:  Canonical query Q = (τ, s, r, o_vec, c, k_min, n_max)
            engine_type ∈ {KG, SHEAF}
    Output: Engine-specific query object

    match (τ, engine_type):
        case (FACT, KG):
            return KGQuery(kind=LOOKUP, subject=s, predicate=r,
                          objects=o_vec)

        case (FACT, SHEAF):
            return SheafQuery(context=c, pattern=BuildPattern(s, r, o_vec))

        case (WALK, KG):
            return KGQuery(kind=PATH, start=s, relation=r, depth=n_max)

        case (WALK, SHEAF):
            return SheafQuery(context=c, start=s, relation=r,
                             max_depth=n_max)

        case (JOIN, KG):
            return KGQuery(kind=CONTEXT, entities=s_set, context=c)

        case (JOIN, SHEAF):
            return SheafQuery(context=c, entities=s_set)

        case (GLUE, both):
            // GLUE queries return global sections
            return GlobalQuery()
```

**Implementation:** `QueryEngine.execute_kg()` and `QueryEngine.execute_sheaf()` in `sfdb.query.language.py`.

---

## Algorithm 8: Local Query Execution (Sheaf)

```text
ExecuteLocalQuery(Q_sheaf, store)
    Input:  Sheaf query, SheafStore instance
    Output: Set of matching facts

    c ← Q_sheaf.context
    pattern ← Q_sheaf.pattern

    // Step 1: Get all facts in context c
    if c is specified and c ≠ *:
        facts ← store.query_context(c)
    else:
        facts ← store.all_facts()

    // Step 2: Apply pattern filter
    results ← ∅
    for each f in facts:
        if MatchPattern(f, pattern):
            if f.confidence ≥ Q_sheaf.min_confidence:
                results ← results ∪ { f }

    // Step 3: Apply limit
    if |results| > Q_sheaf.max_results:
        results ← results[0 : Q_sheaf.max_results]

    return results
```

**Implementation:** `SheafStore.query_context()`, `SheafStore.query_global()` in `sfdb.sheaf.sheaf.py`.

---

## Algorithm 9: Global Query Execution (Sheaf)

```text
ExecuteGlobalQuery(store, C)
    Input:  SheafStore, context poset C
    Output: Set of global facts (valid everywhere)

    // Compute global sections by gluing local sections
    raw_global ← ComputeGlobalSections(store.sheaf, C)

    // Map back to semantic facts
    results ← ∅
    for each section s in raw_global:
        fact ← ReconstructFact(s)                 // section → Fact
        results ← results ∪ { fact }

    return results
```

**Implementation:** Chaining of `Sheaf.global_sections()` → reconstruction → result.

---

## Algorithm 10: Complexity Analysis Framework

```text
AnalyzeComplexity(algorithm, input_size)
    Input:  Algorithm identifier, input size n
    Output: Asymptotic complexity class

    match algorithm:
        case TOPOLOGY_CONSTRUCTION:
            // Build down-sets: O(|C|^2)
            // Intersection closure: O(|T|^2 · |C|)
            return O(|C|^3) in worst case

        case FACT_INSERTION:
            // Triple decomposition: O(k) where k = arity
            // Index update: O(log N)
            return O(k + log N)

        case FACT_DELETION:
            // Index lookup: O(log N)
            // Triple removal: O(k · log N)
            return O(k · log N)

        case CONTEXT_LOOKUP:
            // Open set membership: O(1) with hash index
            // Section retrieval: O(|F(c)|)
            return O(|F(c)|)

        case RESTRICTION:
            // Filter object slots: O(k)
            // Specialize values: O(k)
            return O(k)

        case GLOBAL_SECTIONS:
            // Glue all sections upward: O(|C| · |F|^2) worst case
            // Optimized with compatibility cache: O(|C| · |F|)
            return O(|C| · |F|)

        case NEIGHBORHOOD_SEARCH:
            // Expand from minimal neighbourhood: O(|C|)
            // Collect sections: O(|F|)
            return O(|C| + |F|)

        case CONTEXT_SEARCH:
            // Find minimal open set: O(|T|) = O(|C|)
            // Retrieve facts: O(|F(c)|)
            return O(|C| + |F(c)|)

        case TEMPORAL_SEARCH:
            // Filter by temporal bounds: O(|F|)
            // Temporal index if available: O(log |F|)
            return O(|F|)

        case CONSISTENCY_VERIFICATION:
            // Check locality: O(|C| · |F|^2)
            // Check gluing: O(|C| · |F|^2)
            return O(|C| · |F|^2)
```

**Implementation:** Timing measured via `BenchmarkCollector`, `MeasuredRun`, and `Profiler` in `src/sfdb/benchmark/`.
