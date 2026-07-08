# Sheaves and Presheaves (Baseline Reference)

## Overview
A presheaf on a topological space X assigns data to each open set (context) with restriction maps between nested sets. A sheaf adds the gluing axiom: compatible local data uniquely determines global data. This is SheafDB's mathematical foundation.

## Advantages
- Native context: open sets = contexts, restriction maps = context refinement
- Consistency: cocycle condition checks if local assignments are compatible
- Global sections: gluing axiom constructs a global view from local data
- Provenance: restriction maps track which data flows where
- Temporal: discrete topology on time dimension
- Generalizes graphs, hypergraphs, simplicial complexes

## Limitations
- Topology construction requires context hierarchy knowledge
- Restriction map computation can be O(n²) worst case
- Storage overhead: each fact stored in each stalk it appears in
- Gluing requires solving consistency constraints
- Steep learning curve for newcomers
- No standard query language (no SPARQL equivalent for sheaves)

## Implementation Difficulty: High (4/5)
SheafDB demonstrates feasibility. Key challenges: topology construction, restriction map caching, gluing algorithm optimization, global section cache invalidation.

## Potential Architecture
Finite topology + presheaf = database. Each open set = context. Each stalk = set of facts in that context. Restriction = filtering to sub-context. Already implemented in SheafDB.

## Expected Complexity
- Context lookup: O(log |O|) with index
- Restriction: O(|stalk|) 
- Gluing: O(c × s) for c contexts, s stalk size
- Consistency: O(c × s) with overlap checking

## Possible Benchmarks
Known: C1 (neighborhood), C2 (paths), C8 (consistency), C9 (global section), C10 (mixed). These are SheafDB's native workloads and the baseline for comparison.

## Verdict
SheafDB (presheaves on finite topological spaces) is the baseline. Any new model must beat it on at least some significant dimension — construction speed, query speed, storage efficiency, consistency capability, or simplicity.
