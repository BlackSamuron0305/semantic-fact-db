# Graph Neural Network Databases / Neural Graph Databases

## Overview
Neural graph databases use learned embeddings (GNNs, GraphSAGE, GATs) to store and retrieve structured data. Facts are encoded in graph embeddings; queries are answered by learned functions over embeddings. Examples: NeuralDB, Graph Neural Database (GND), Learned Databases.

## Advantages
- Learned compression: embeddings capture structural patterns automatically
- Fast approximate query via embedding operations
- Generalizes to unseen query patterns
- Robust to missing or noisy data
- Continuous representations enable gradient-based optimization
- Natural for vector-similarity search (ANN)

## Limitations
- **No exact answers** — embeddings provide approximate retrieval
- Training requires labeled query-answer pairs
- Updates require (partial) retraining
- No consistency guarantees
- No context representation (beyond learned latent factors)
- No provenance
- No global section construction
- Interpretability is poor
- Hallucination risk (model invents facts)

## Comparison to SheafDB
Neural graph databases sacrifice exactness for flexibility. They are not a replacement for SheafDB (which guarantees correct semantic retrieval via the sheaf structure). For applications where approximation is acceptable, neural approaches scale better. SheafDB is exact but constrained; neural DBs are approximate but flexible.

## Implementation Difficulty: Medium (3/5)
Mature GNN libraries (PyTorch Geometric, DGL). The challenge is training query-answering models that generalize across query types and fact patterns.

## Architecture
- Encode facts as a graph
- Learn entity/relation embeddings via GNN message passing
- Query = embedding operation (e.g., TransE-style composition of embeddings)
- Retrieve entities nearest to query embedding
- Fine-tune on query-answer pairs

## Expected Complexity
- Training: O(epochs × |E| × d²) for d-dim embeddings
- Query: O(d²) embedding computation + O(|E|) ANN search
- Update: O(retraining) expensive

## Verdict
Neural graph databases are an approximation method, not a replacement for exact semantic storage. For SheafDB's use case (exact contextual retrieval), they are inapplicable. Interesting for approximate versions of SheafDB queries but fundamentally incompatible with the exact consistency guarantees that motivate the sheaf framework.
