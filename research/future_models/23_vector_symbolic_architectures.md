# Higher-Order Distributed Representation / Vector-Symbolic Architectures

## Overview
Vector-symbolic architectures (VSAs, also known as hyperdimensional computing) use high-dimensional vectors (e.g., 10,000-D) with algebraic operations: binding (circular convolution), bundling (addition), permutation (role-filler binding). For databases: concepts = vectors, facts = bound tuples.

## Advantages
- **Extreme parallelism** — all operations are vector-wide
- Binding enables associative memory (fact → retrieval)
- Fixed-width representation (10k floats regardless of DB size)
- Robust to noise and missing data
- Near-perfect retrieval for moderate-sized KBs
- Operations are simple (addition, multiplication, permutation)
- Hardware-friendly (FPGA, neuromorphic)

## Limitations
- **Approximate retrieval** — capacity is limited (∼10⁴ concepts in 10k-D)
- Catastrophic interference as capacity approaches limit
- No exact answers — only closest-match retrieval
- No context representation (flattened into vector)
- No consistency checking
- No provenance
- No temporal model
- Binding is O(d log d) for convolution — O(d) for XOR-based VSAs
- Capacity depends on vector dimension and sparsity

## Comparison to SheafDB
VSAs are the polar opposite of SheafDB: massively parallel, approximate, holistic vs. structured, exact, compositional. VSAs fail on every requirement that motivates SheafDB (exact retrieval, context, consistency, provenance, global sections). They are not a competitor for semantic database applications.

## Implementation Difficulty: Low (2/5)
Simple to implement (array operations). Mature libraries exist (Torchhd, VSA-Engine).

## Architecture
- Map each entity, relation, value to a random high-D vector
- Encode fact as binding (circular convolution) of role and filler vectors
- Store facts by bundling (element-wise addition) into a single vector
- Query = unbind and compare against concept vectors
- Context = additional bound terms

## Expected Complexity
- Encoding: O(d) per binding
- Storage: O(d) constant (single vector for entire DB!)
- Query: O(d) unbinding + O(|Vocabulary| × d) nearest neighbor
- Capacity: ∼d/2 concepts in d-dimensional VSA

## Verdict
VSAs are an interesting cognitive architecture but cannot replace SheafDB for exact semantic storage. The approximate, holistic nature is fundamentally incompatible with the exact consistency guarantees required for semantic databases. An interesting demonstration: even the most efficient approximate model cannot match SheafDB's exact retrieval and consistency features.
