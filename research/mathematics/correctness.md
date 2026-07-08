# Correctness

## What Correctness Means

For SheafDB, correctness is the property that the system's observable behaviour matches its formal mathematical specification. Concretely, a knowledge state $\Sigma$ is **correct** if:

1. Every query result $\llbracket Q \rrbracket_\Sigma$ contains exactly the facts that satisfy $Q$ according to the denotational semantics.
2. Every state transition (insert, update, delete) preserves the invariants of the semantic fact model.
3. The sheaf axioms (locality and gluing) are satisfied at all times.
4. Two different storage engines (KG and Sheaf) produce equivalent results for identical inputs and queries.

We decompose correctness into five specific conditions.

---

## Correctness Condition 1: Lossless Mapping

**Definition:** A mapping $\phi: \mathcal{F}_A \to \mathcal{F}_B$ (from representation $A$ to representation $B$) is **lossless** iff there exists a reverse mapping $\psi: \mathcal{F}_B \to \mathcal{F}_A$ such that $\psi(\phi(f)) = f$ for all $f \in \mathcal{F}_A$.

**Required mappings:**
- $\phi_{\text{KG}}$: Generic `Fact` → KG triple representation (via reification).
- $\phi_{\text{Sheaf}}$: Generic `Fact` → Sheaf section.
- $\phi_{\text{Canonical}}$: Generic `Fact` → `CanonicalFact`.

**Correctness requirement:** All three mappings must be lossless, and their compositions must commute:

\[
\phi_{\text{Canonical}} \circ \psi_{\text{KG}} \circ \phi_{\text{KG}} = \phi_{\text{Canonical}}
\]
\[
\phi_{\text{Canonical}} \circ \psi_{\text{Sheaf}} \circ \phi_{\text{Sheaf}} = \phi_{\text{Canonical}}
\]

**Verification:** The `CanonicalMapping` class implements the invertible mapping. Tests in `tests/test_roundtrip.py` verify that facts survive round-trips through each representation.

**Failure mode:** A fact loses information (e.g., an object slot is dropped) during insertion and cannot be reconstructed.

---

## Correctness Condition 2: Semantic Equivalence

**Definition:** Two knowledge states $\Sigma_1$ and $\Sigma_2$ are **semantically equivalent** iff they produce isomorphic canonical models:

\[
\mathfrak{F}(\Sigma_1) \cong \mathfrak{F}(\Sigma_2)
\]

where $\cong$ denotes equality up to identifier renaming (bijection between entity identifiers preserving all semantic relationships).

**Correctness requirement:** For any sequence of insert operations applied identically to both KG and Sheaf systems:

\[
\mathfrak{F}(\Sigma_{\text{KG}}) \cong \mathfrak{F}(\Sigma_{\text{Sheaf}})
\]

**Verification:** The `QueryEngine.results_equivalent()` method compares result sets by fact ID equality. The benchmark framework verifies equivalence across all 15 benchmark queries.

**Failure mode:** The two engines produce different results for the same query, indicating a semantic discrepancy in one or both engines.

---

## Correctness Condition 3: Referential Integrity

**Definition:** A knowledge state $\Sigma$ satisfies **referential integrity** iff for every fact $f \in \Sigma$:

1. $\operatorname{subject}(f) \in \mathcal{E}_\Sigma$ (the subject entity exists).
2. If any object $\omega_j$ is a reference (not a literal), then $\omega_j \in \mathcal{E}_\Sigma$ (the referenced entity exists).
3. $\operatorname{relation}(f) \in \mathcal{R}_\Sigma$ (the relation type exists).

**Correctness requirement:** Every state transition preserves referential integrity.

**Verification:** Insertion validates referenced entities. Deletion checks that removed entities are not referenced by remaining facts. The `validation.py` module enforces these constraints.

**Failure mode:** An orphan reference exists (a fact references a non-existent entity), leading to query-time errors or incomplete results.

---

## Correctness Condition 4: Consistency (Sheaf Axioms)

**Definition:** A knowledge state $\Sigma$ with presheaf $F$ is **consistent** iff $F$ satisfies the sheaf axioms:

1. **Locality:** For every open set $U$ and open cover $\{U_i\}$, if $s|_U = t|_U$ for all $i$, then $s = t$.
2. **Gluing:** For every open set $U$ and compatible family $\{s_i \in F(U_i)\}$, there exists a unique $s \in F(U)$ extending all $s_i$.

**Correctness requirement:** After every state transition, the sheaf axioms must hold.

**Verification:** The `Sheaf.glue()` method enforces gluing by checking pairwise compatibility and raising a `ConsistencyError` when incompatible sections are detected. The `VerifyConsistency` algorithm checks both axioms.

**Failure mode:** Two sections in overlapping contexts disagree, making it impossible to glue them into a consistent section over a broader context. This indicates conflicting knowledge that must be resolved before the state can be considered consistent.

---

## Correctness Condition 5: Determinism

**Definition:** A query execution is **deterministic** iff the same query $Q$ against the same knowledge state $\Sigma$ always returns the same result $\llbracket Q \rrbracket_\Sigma$ (as a set of facts), regardless of:

- Execution order.
- Memory layout or caching.
- Parallelism.
- Previous query history.

**Correctness requirement:** `ExecuteQuery(Q, Σ) = ExecuteQuery(Q, Σ)` for any two invocations with identical arguments.

**Verification:** The benchmark framework runs each query multiple times and verifies result consistency. Non-determinism in result ordering is permitted (sets are unordered), but non-determinism in fact membership is a correctness failure.

**Failure mode:** Two runs of the same query return different fact sets, indicating a race condition, stale cache, or non-deterministic traversal.

---

## Summary Table

| Condition | Formal Criterion | Verification Method | Failure Consequence |
|-----------|-----------------|---------------------|---------------------|
| Lossless Mapping | $\psi(\phi(f)) = f$ | Round-trip tests | Data loss |
| Semantic Equivalence | $\mathfrak{F}(\Sigma_1) \cong \mathfrak{F}(\Sigma_2)$ | Cross-engine query comparison | Incorrect results |
| Referential Integrity | $\forall f: \text{refs}(f) \subseteq \mathcal{E}_\Sigma$ | Validation on insert/delete | Orphan references |
| Consistency (Sheaf) | Locality + Gluing axioms | Gluing checks, consistency verification | Contradictory knowledge |
| Determinism | $Q(\Sigma) = Q(\Sigma)$ | Repeated execution | Non-reproducible results |

---

## Implementation Checklist

Every correctness condition should be:
- [x] Formally defined (this document).
- [x] Tested by at least one unit test.
- [x] Verified by the benchmark framework for the 15 standard queries.
- [x] Documented in the paper.
- [x] Traceable to code: each condition maps to a specific validation routine.
