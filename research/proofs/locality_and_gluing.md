# Locality and Gluing Axioms

## Locality Axiom

Let $F$ be a presheaf on a topological space $(X, \mathcal{T})$.
$F$ satisfies the **locality axiom** if for every open set
$U \subseteq X$, every open cover $\{U_i\}_{i \in I}$ of $U$, and every
pair of sections $s, t \in F(U)$:

\[
\bigl(\forall i \in I,\; \rho_{U, U_i}(s) = \rho_{U, U_i}(t)\bigr)
\implies s = t.
\]

### Interpretation

Two facts that are indistinguishable in every sub-context are the same
fact.  This prevents the database from storing two distinct facts that
agree on all restrictions.

## Gluing Axiom

Let $F$ be a presheaf on $(X, \mathcal{T})$.  $F$ satisfies the
**gluing axiom** if for every open set $U \subseteq X$ and every open
cover $\{U_i\}_{i \in I}$ of $U$, given a family of sections
$\{s_i \in F(U_i)\}_{i \in I}$ that is **compatible** on overlaps:

\[
\rho_{U_i, U_i \cap U_j}(s_i) = \rho_{U_j, U_i \cap U_j}(s_j)
\qquad \forall i, j \in I,
\]

there exists a **unique** section $s \in F(U)$ such that

\[
\rho_{U, U_i}(s) = s_i \qquad \forall i \in I.
\]

### Interpretation

If facts stated in different sub-contexts agree on all overlapping
sub-contexts, they can be **glued** into a single consistent fact
valid in the broader context.  The uniqueness ensures determinism.

## Combined Significance

Together the locality and gluing axioms make a presheaf into a **sheaf**.
For SFDB:

- **Locality** ensures consistency: contradictory facts cannot coexist
  in the same context and agree on all sub-contexts.
- **Gluing** enables inference: from facts in sub-contexts we can
  reconstruct the unique fact that must hold in the encompassing context.

These axioms are the foundation for the **global sections** computation
that drives semantic equivalence verification in the benchmarks.

## Failure Modes

### Locality violation
Two different facts $f_1, f_2 \in F(c)$ that happen to restrict to the
same values in every sub-context $c_i \leq c$ but differ at $c$.  This
is impossible in SFDB because the context field is part of the fact;
two facts with the same ID are the same fact.

### Gluing failure
Two sections $s_1 \in F(c_1)$ and $s_2 \in F(c_2)$ that disagree on the
overlap $c_1 \land c_2$.  In SFDB this indicates inconsistent knowledge:
two sources assert incompatible facts about the same entity.  The sheaf
condition flags this as an error.

## References

- Mac Lane & Moerdijk, *Sheaves in Geometry and Logic* (1992), §II.2.
- Roselly, *Sheaf Theory through Examples* (2021), §2.1–2.3.
