# Higher-Order Networks and Topological Deep Learning

## Overview
Higher-order networks generalize pairwise graphs to simplicial complexes, hypergraphs, cellular sheaves, and other structures within the topological deep learning framework. These models learn on structured data using message passing over cells of any dimension.

## Advantages
- Unified framework for learning on any topological structure (Bodnar et al., 2021)
- Message passing generalizes across dimensions (0-cells, 1-cells, 2-cells, ...)
- Expressive power beyond WL graph isomorphism test
- Sheaf-based message passing (Hansen & Gebhart, 2020) = learned sheaf structure
- Cellular sheaf neural networks = learn the sheaf itself
- Auto-context discovery via sheaf learning

## Limitations
- **Learning framework, not a storage model** — no query semantics, no retrieval guarantees
- Sheaf learning requires gradient backpropagation — expensive
- Message passing is iterative O(k × |Cells|) — can be slow
- No support for temporal, provenance, global sections
- No standard for persistent storage between training runs
- Learned sheaves may not correspond to interpretable contexts

## Comparison to SheafDB
Topological deep learning is the closest field to SheafDB outside pure mathematics. Cellular sheaf neural networks *learn* a sheaf structure from data — potentially automating SheafDB's topology construction. However, learned sheaves are instrumentally useful (for prediction tasks) but not necessarily interpretable or useful for query answering. SheafDB builds a sheaf explicitly for query processing.

## Implementation Difficulty: Very High (5/5)
Requires differentiable sheaf operations (learnable restriction maps). Existing implementations in PyTorch Geometric (via CellLang, TopoNetX, TopoModelX). No existing work combines learnable sheaves with database semantics.

## Potential Architecture (Speculative)
- Learn sheaf structure via gradient descent on query-answer pairs
- Restriction maps = learnable linear transformations
- Stalks = hidden representations of entity/context combinations
- Query = forward pass through the learned sheaf
- Generate topology from data via learned overlap structure

## Expected Complexity
- Sheaf learning: O(epochs × |Open| × d³) for d-dim stalks
- Forward pass (query): O(|Open| × d²)
- Gradient computation: O(|Open| × d³) (backprop through restriction maps)

## Possible Benchmarks
- Sheaf learning quality (reconstruction of known topology)
- Query accuracy with learned vs. prescribed sheaves
- Generalization to novel queries

## Verdict
**The most exciting potential enhancement to SheafDB, but not a replacement.** Topological deep learning can learn sheaf structures from data, potentially automating SheafDB's topology and restriction map construction. However:

1. Learned sheaves are expensive to train
2. They lack query semantics (no standard retrieval)
3. They are approximate (learned), not exact

A hybrid: use sheaf learning to propose candidate topologies, then refine and query via classical sheaf operations. This is a **future direction for SheafDB research**, not a competitor.

## Key Literature
- Hansen & Gebhart (2020): Sheaf Neural Networks
- Bodnar et al. (2021): Weisfeiler-Lehman goes topological
- Barbero et al. (2022): Sheaf attention networks
- de Haan et al. (2020): Sheaf autoencoders
