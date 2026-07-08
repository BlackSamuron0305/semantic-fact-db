# Tensor Representations (Sparse Tensor Databases)

## Overview
Represent facts as entries in a sparse tensor. Dimensions: entity × entity × ... × relation × context × time. Query via tensor contraction (Einstein summation). Storage: compressed sparse fiber (CSF) or coordinate list (COO).

## Advantages
- Naturally high-dimensional (arity = tensor order)
- Tensor contraction subsumes join, selection, projection
- Highly parallelizable (GPU, TPU, distributed)
- COO/CSF storage is compact for sparse data
- Rich literature from scientific computing and ML
- Multilinear algebra provides decomposition (CP, Tucker, Tensor Train)
- Approximate query via low-rank approximation

## Limitations
- Sparse tensor operations can be memory-intensive
- Tensor contractions for complex queries are expensive (exponential in order)
- No context representation (context is just another dimension)
- No consistency checking
- No global section construction
- Fiber-based operations (reshape, permute) are NP-hard to optimize
- Path queries require iterative tensor operations (slow)
- Provenance is ad-hoc

## Comparison to SheafDB
Tensor databases excel at high-arity fact storage and parallelizable bulk operations. They match SheafDB's high-arity capability but lack context-awareness (context is flat, not hierarchical). Construction is faster (no topology). For bulk ML/AI workloads (not in current benchmark), tensors dominate. For contextual semantic queries, SheafDB's restriction maps are faster than tensor slice operations.

## Implementation Difficulty: Medium (3/5)
Mature libraries (PyTorch sparse, TensorFlow, SciPy sparse, SPLATT, TACO). The challenge is encoding semantics into tensor dimensions and designing efficient contraction plans.

## Potential Architecture
- Encode entities, relations, positions as tensor indices
- Facts = non-zero entries with values (confidence, source)
- Context = ordered pair of indices (start, end) or an additional dimension
- Query = einsum string (e.g., "ij,jk->ik" for graph traversal)
- Temporal = time dimension with stride-based slicing

## Expected Complexity
- Storage: O(nnz) for non-zeros
- Contraction: O(nnz₁ × nnz₂) naive, O(nnz₁ log nnz₂) sorted
- Slice (context = dimension filter): O(log nnz)
- CP decomposition: O(nnz × rank) per iteration
- Path query (iterated contraction): O(|path| × nnz)

## Possible Benchmarks
- High-arity fact insertion (tensor assembly)
- Contraction plan quality
- GPU vs. CPU throughput
- Context slicing cost
- Path query vs. sheaf restriction chain
- Low-rank approximation quality
- Memory vs. speed tradeoffs for context encoding

## Verdict
**Strong candidate for bulk/ML workloads but not for contextual semantic queries.** Sparse tensors are excellent for high-arity storage and parallel computation, but lack the context hierarchy, consistency checking, and global section capabilities that make SheafDB distinctive. Most promising for hybrid architectures: tensor for bulk storage, sheaf for contextual queries.

## White Whale: Could Tensors Beat SheafDB on Context?
If context is encoded as a single tensor dimension (not a hierarchy), context queries are just tensor slices — O(log nnz) via CSR/CSC index. This would **beat** SheafDB's O(|stalk|) restriction for flat contexts. However, it cannot represent hierarchical contexts, and nested context queries require multiple slices (each O(log nnz), total O(depth × log nnz)). The trade: SheafDB's richer context structure at O(|stalk|) cost vs. tensor's flat context at O(log nnz) cost.
