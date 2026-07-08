# Theorems

> Proof sketches are provided where complete proofs are impractical.
> Detailed proofs for the core sheaf-theoretic claims are in the files
> listed under **References**.

---

## Theorem 1: Semantic Preservation (Round-trip Correctness)

**Assumptions:**
- Let $f \in \mathcal{F}$ be a semantic fact.
- Let $T$ be the triple decomposition function: $T(f) = \{t_1, \ldots, t_k\}$ where $k = 2 + \operatorname{arity}(f)$.
- Let $R$ be the reconstruction function: $R(\{t_1, \ldots, t_k\}) = f'$.

**Statement:** For any semantic fact $f$,
\[
R(T(f)) = f.
\]

**Proof Sketch:** The decomposition $T$ creates $k$ reified triples using a unique statement ID $s = f.id$:
1. $(s, \text{rdf:type}, \text{rdf:Statement})$
2. $(s, \text{rdf:subject}, f.subject)$
3. $(s, \text{rdf:predicate}, f.relation)$
4. $(s, \text{rdf:object}_j, f.objects_j)$ for each $j$.

Reconstruction $R$ groups triples by statement ID, then inverts each step. Since the decomposition is injective and the reconstruction is its left inverse on the image of $T$, the round-trip is identity.

**References:** `research/proofs/presheaf.md`, `src/sfdb/kg/triple.py`.

---

## Theorem 2: Restriction Functoriality

**Assumptions:**
- Let $(\mathcal{C}, \leq)$ be the context poset.
- For each $c \in \mathcal{C}$, let $F(c)$ be the set of facts valid in context $c$.
- For each $c \leq d$, let $\rho_{d,c}: F(d) \to F(c)$ be the restriction map.

**Statement:** The restriction maps satisfy:
1. $\rho_{c,c} = \operatorname{id}_{F(c)}$ for all $c \in \mathcal{C}$.
2. $\rho_{e,c} = \rho_{d,c} \circ \rho_{e,d}$ for all $c \leq d \leq e$.

This is exactly the statement that $F: \mathcal{C}^{\text{op}} \to \mathbf{Set}$ is a functor (a presheaf on $\mathcal{C}$).

**Proof Sketch:** Property (1) holds because restricting from $c$ to $c$ leaves all object slots unchanged. Property (2) holds because restriction is defined pointwise: restricting from $e$ to $d$ then from $d$ to $c$ is equivalent to restricting directly from $e$ to $c$, as both apply the same sequence of slot operations.

**References:** `research/proofs/restriction_maps.md`, `research/proofs/presheaf.md`.

---

## Theorem 3: Presheaf Locality

**Assumptions:**
- Let $F$ be a presheaf on a topological space $(X, \mathcal{T})$.
- Let $U \in \mathcal{T}$ and $\{U_i\}_{i \in I}$ be an open cover of $U$.
- Let $s, t \in F(U)$.

**Statement (Locality):** If $\rho_{U,U_i}(s) = \rho_{U,U_i}(t)$ for all $i \in I$, then $s = t$.

**Proof Sketch:** In the Alexandrov topology on $\mathcal{C}$, every open set $U$ has a basis of minimal open sets $\{\mathcal{B}(x) \mid x \in U\}$. Equality of restrictions to each $\mathcal{B}(x)$ implies equality of the sections at each point, hence equality globally. The result follows from the fact that restriction maps are functions and the cover separates points.

**References:** `research/proofs/locality_and_gluing.md`, `research/proofs/local_sections.md`.

---

## Theorem 4: Sheaf Gluing

**Assumptions:**
- Let $F$ be a sheaf on $(X, \mathcal{T})$.
- Let $U \in \mathcal{T}$ and $\{U_i\}_{i \in I}$ be an open cover of $U$.
- Let $\{s_i \in F(U_i)\}_{i \in I}$ be a compatible family:
  \[
  \rho_{U_i, U_i \cap U_j}(s_i) = \rho_{U_j, U_i \cap U_j}(s_j) \quad \forall i, j \in I.
  \]

**Statement (Gluing):** There exists a unique section $s \in F(U)$ such that $\rho_{U,U_i}(s) = s_i$ for all $i \in I$.

**Proof Sketch:** For each point $x \in U$, pick $i$ such that $x \in U_i$ and define $s(x) = s_i(x)$. Compatibility ensures this is well-defined: if $x \in U_i \cap U_j$, then $s_i(x) = s_j(x)$ by the compatibility condition. Define $s$ as the unique section whose germ at each $x$ agrees with the $s_i$. Uniqueness follows from the locality axiom.

**References:** `research/proofs/locality_and_gluing.md`, `research/proofs/global_sections.md`, `research/proofs/sheaf.md`.

---

## Theorem 5: Invertibility of the Canonical Mapping

**Assumptions:**
- Let $\mathfrak{F}$ be the canonical model (set of canonical entities, relations, and facts).
- Let $\phi: \mathcal{F} \to \mathfrak{F}$ be the canonical mapping from facts to canonical facts.
- Let $\psi: \mathfrak{F} \to \mathcal{F}$ be the inverse mapping.

**Statement:** The mappings $\phi$ and $\psi$ are mutual inverses:
\[
\psi(\phi(f)) = f \quad \text{for all } f \in \mathcal{F},
\]
\[
\phi(\psi(\mathfrak{f})) = \mathfrak{f} \quad \text{for all } \mathfrak{f} \in \mathfrak{F}.
\]

**Proof Sketch:** $\phi$ decomposes a generic fact $f = (i, s, r, \vec{o}, c, k, m)$ into a canonical entity $\varepsilon_s$ (for subject), canonical relation $\rho_r$ (with slot types determined by $r$), and canonical fact $\mathfrak{f} = (\varepsilon_s, \rho_r, \vec{o}, c)$. The inverse $\psi$ reconstructs $f$ from these components. Since the mapping preserves all fields and the decomposition is bijective on the component types, the round-trip is identity.

**References:** `src/sfdb/canonical/canonical.py`.

---

## Theorem 6: Context Meet as Open Set Intersection

**Assumptions:**
- Let $(\mathcal{C}, \leq)$ be the context poset with Alexandrov topology $\mathcal{T}_A$.
- For each $c \in \mathcal{C}$, let $U_c = \downarrow c$ be the corresponding open set.

**Statement:** For any $c_1, c_2 \in \mathcal{C}$,
\[
U_{c_1} \cap U_{c_2} = U_{c_1 \wedge c_2}.
\]

**Proof Sketch:** By definition, $d \in U_{c_1} \cap U_{c_2}$ iff $d \leq c_1$ and $d \leq c_2$. This is equivalent to $d \leq c_1 \wedge c_2$ (by definition of meet), which is exactly $d \in U_{c_1 \wedge c_2}$.

**Corollary:** The open sets $\{U_c\}_{c \in \mathcal{C}}$ form a basis for $\mathcal{T}_A$ that is closed under finite intersection.

---

## Theorem 7: Equivalence of Query Results Across Engines

**Assumptions:**
- Let $\Sigma_{\text{KG}}$ be the knowledge state expressed in the KG system (triple store).
- Let $\Sigma_{\text{Sheaf}}$ be the same knowledge state expressed in the sheaf system.
- Let $\mathfrak{F}$ be the canonical model derived from either representation.
- Let $Q$ be a canonical query.

**Statement:** If $\Sigma_{\text{KG}}$ and $\Sigma_{\text{Sheaf}}$ are both consistent translations of $\mathfrak{F}$, then:
\[
\llbracket Q \rrbracket_{\Sigma_{\text{KG}}} \cong \llbracket Q \rrbracket_{\Sigma_{\text{Sheaf}}}
\]
where $\cong$ denotes equality up to identifier isomorphism (bijection between result sets preserving all semantic fields).

**Proof Sketch:** Both storage engines are proven to implement the same canonical model via their respective adapter mappings. The query execution is defined in terms of the canonical model's matching predicate. Since both engines produce identical canonical model representations for equivalent inputs, the query results must be isomorphic.

**References:** `research/mappings/kg_mapping.md`, `research/mappings/sheaf_mapping.md`, `src/common/interfaces.py`.

---

## Theorem 8: Preservation of Referential Integrity

**Assumptions:**
- Let $\Sigma$ be a knowledge state.
- Let $f = (i, s, r, \vec{o}, c, k, m) \in \Sigma$ be any fact.
- Let $\mathcal{E}_\Sigma = \{\text{subject}(f') \mid f' \in \Sigma\}$ be the set of entities in $\Sigma$.
- Let $\mathcal{R}_\Sigma = \{\text{relation}(f') \mid f' \in \Sigma\}$ be the set of relations in $\Sigma$.

**Statement:** For every fact $f \in \Sigma$:
1. $\operatorname{subject}(f) \in \mathcal{E}_\Sigma$ (subject is a known entity).
2. $\operatorname{relation}(f) \in \mathcal{R}_\Sigma$ (relation is known).
3. For each object $\omega_j \in \vec{o}$ that is a reference, $\omega_j \in \mathcal{E}_\Sigma$ (referenced entity exists).

**Proof:** This follows from the construction of $\Sigma$ by successive insertions. When a fact is inserted, its subject is added to $\mathcal{E}_\Sigma$ if not already present, and referenced entities are verified to exist. The invariant is maintained across all state transitions.

---

## Theorem 9: Determinism of Query Execution

**Assumptions:**
- Let $Q$ be a canonical query.
- Let $\Sigma$ be a fixed knowledge state.
- Let $E$ be a query execution engine.

**Statement:** The result $\llbracket Q \rrbracket_\Sigma$ is uniquely determined by $Q$ and $\Sigma$ alone, independent of:
- Execution order within the engine.
- Memory layout or caching state.
- Parallelisation strategy.
- Previous query history.

**Proof Sketch:** The query denotation $\llbracket Q \rrbracket_\Sigma$ is defined purely declaratively as the set of facts matching $Q$ in $\Sigma$. Any correct implementation must compute exactly this set. Different execution strategies may produce the facts in different orders (non-deterministic ordering), but the set of facts is uniquely determined. The benchmark verifies this by comparing results across independent engines.

**References:** `src/sfdb/query/execution.py`, `src/common/interfaces.py`.

---

## Theorem 10: Consistency of Global Section Computation

**Assumptions:**
- Let $F$ be a sheaf on the Alexandrov space $(\mathcal{C}, \mathcal{T}_A)$.
- Let $\Gamma(F)$ be the set of global sections computed by the gluing algorithm.

**Statement:** A family of local sections $\{s_i \in F(U_i)\}$ can be glued to a global section $s \in F(\mathcal{C})$ if and only if for every pair $i, j$, the restrictions agree on the overlap: $\rho_{U_i, U_i \cap U_j}(s_i) = \rho_{U_j, U_i \cap U_j}(s_j)$.

**Proof:** This is exactly the gluing axiom of a sheaf (Definition 6 in `definitions.md`). The "if" direction is guaranteed by the sheaf property. The "only if" direction follows from the consistency of restriction: if $s$ exists, its restrictions to $U_i$ and $U_j$ must agree on $U_i \cap U_j$.

**References:** `research/proofs/global_sections.md`, `research/proofs/sheaf.md`.

---

## References to Detailed Proofs

| Theorem | Detailed Proof File |
|---------|-------------------|
| Semantic Preservation | `research/proofs/simplicial.md` |
| Restriction Functoriality | `research/proofs/restriction_maps.md`, `research/proofs/presheaf.md` |
| Presheaf Locality | `research/proofs/locality_and_gluing.md`, `research/proofs/local_sections.md` |
| Sheaf Gluing | `research/proofs/locality_and_gluing.md`, `research/proofs/sheaf.md` |
| Invertibility | `research/mappings/kg_mapping.md`, `research/mappings/sheaf_mapping.md` |
| Context Meet | `research/proofs/alexandrov_topology.md` |
| Query Equivalence | `research/proofs/properties.md` |
| Referential Integrity | `research/proofs/stalks.md` |
| Determinism | `research/proofs/properties.md` |
| Global Section Consistency | `research/proofs/global_sections.md`, `research/proofs/sheaf.md` |
