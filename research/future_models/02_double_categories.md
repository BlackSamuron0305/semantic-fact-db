# Double Categories

## Overview
A double category has two types of morphisms: horizontal (facts) and vertical (contexts). This naturally captures the fact-context duality.

## Advantages
- Both facts and context transformations as first-class citizens
- Horizontal composition = fact chaining
- Vertical composition = context refinement
- Grid cells = fact-within-context
- Exchange law = context-change commutes with fact-composition

## Limitations
- Requires both compositions to satisfy compatibility (exchange law)
- No native consistency checking
- Global section construction not defined
- Implementation must track two composition structures
- Complexity can exceed sheaf structure for no clear benefit

## Implementation Difficulty: Very High (4/5)
Double categories require careful bookkeeping of two compositional dimensions. No standard storage engine uses this. The exchange law adds constraints not present in sheaves.

## Comparison to SheafDB
SheafDB's sheaf on a topological space already captures one dimension (context restriction). Double categories would add fact composition along contexts but at the cost of increased implementation complexity. For most use cases, a single category dimension suffices.

## Expected Complexity
- Horizontal composition: O(h) for h-hop chains
- Vertical composition: O(v) for v-level context hierarchy
- Exchange law verification: O(h × v)

## Possible Benchmarks
- Context-refinement chain traversal
- Fact composition across context boundaries
- Exchange law verification cost
