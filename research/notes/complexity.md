# Complexity Analysis

This document analyses the computational complexity of the canonical
semantic model and its mappings to KG and Sheaf representations.

## Storage Complexity

### SemanticFact (canonical)
Each SemanticFact stores:
- id: O(1) fixed-size UUID string
- subject, relation: O(1) each
- objects tuple: O(k) where k = arity
- attributes dict: O(m) where m = number of attributes
- context: O(d) where d = path depth
- provenance: O(1)
- metadata: O(p) where p = metadata entries

Total: O(k + m + d + p) per fact.

### KG representation (hypothesis)
Reifying an n-ary fact produces O(n + m) triples.  Each triple is
stored with three index entries (SPO, POS, OSP).  Storage is
O(triple_count) but with 3x index amplification.

### Sheaf representation (hypothesis)
Each fact is stored once in its maximal context, with thin pointers to
sub-contexts via restriction maps.  Storage is O(facts) + O(restrictions)
where restrictions grow with context depth.

## Construction Complexity

### SemanticFact
O(k + m + p) to construct: copy tuple for objects, build dicts for
attributes and metadata.

### KG insertion
Inserting a fact into KG requires:
1. Decompose into triples: O(n) where n = arity + attribute count.
2. Index each triple: O(1) per triple via hash.
Total: O(n).

### Sheaf insertion
Inserting a fact into SheafDB requires:
1. Store at maximal context: O(1).
2. Update restriction maps for sub-contexts: O(d) where d = depth.
Total: O(d).

## Lookup Complexity

### SemanticFact (canonical)
No indexed storage; lookup requires scanning O(|F|) facts by default.

### KG subject lookup
O(log N + k) with SPO index, where N = total triples, k = result size.

### Sheaf context lookup
O(log |C| + k) with context index, where |C| = number of contexts,
k = sections in that context.

## Consistency Checking Complexity

### Global section computation
Starting from minimal contexts and gluing upward requires:
- O(|F|) to collect all local sections.
- O(|F|^2) worst-case pairwise compatibility checks.
- O(|C|) gluing steps.

Hypothesis: In practice, with a forest-structured context poset, the
compatibility checks are O(|F| log |C|).

## Hypotheses (not proofs)

The following are empirical hypotheses to be tested by the benchmark
framework:

1. H_Storage:  SheafDB storage scales as O(N * d) vs KG O(N * n * 3)
   for N facts, average arity n, context depth d.

2. H_Lookup: For contextual queries, SheafDB lookup time is O(log C + k)
   vs KG O(log T + r) where r = triples retrieved.

3. H_Join: For n-ary queries, KG join cost grows as O(r^{j}) where j =
   number of joins, while SheafDB direct retrieval is O(k).

4. H_Consistency: Global section computation cost is dominated by
   pairwise compatibility checks, with complexity O(|F|^2) worst-case
   but O(|F| log |C|) for natural hierarchies.

These hypotheses are stated without proof and are the subject of the
benchmark experiments.