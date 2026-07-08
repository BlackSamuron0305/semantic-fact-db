# Stalks

## Definition

Let $F: \mathcal{T}^{\text{op}} \to \mathbf{Set}$ be a presheaf on a
topological space $X$.  For a point $x \in X$, the **stalk** of $F$ at
$x$ is the direct limit

\[
F_x = \varinjlim_{U \ni x} F(U),
\]

where the limit is taken over all open neighbourhoods $U$ of $x$,
directed by reverse inclusion.  More concretely, an element of $F_x$
is an equivalence class $[s]_x$ of sections $s \in F(U)$ for some
$U \ni x$, where two sections $s \in F(U)$ and $t \in F(V)$ are
equivalent if they agree on some smaller neighbourhood
$W \subseteq U \cap V$ containing $x$:

\[
\rho_{U, W}(s) = \rho_{V, W}(t).
\]

## Interpretation for SFDB (Alexandrov Case)

In the Alexandrov topology on a finite poset $(C, \leq)$, every point
$c \in C$ has a **smallest neighbourhood**:

\[
U_c = \downarrow c = \{ d \in C \mid d \leq c \}.
\]

Therefore the direct limit collapses to a single evaluation:

\[
F_c \cong F(\downarrow c) = F(c).
\]

The stalk at $c$ is simply $F(c)$, the set of facts valid in context
$c$.  The equivalence relation is trivial because $U_c$ is the minimal
neighbourhood — there is no smaller open set containing $c$.

This simplification means that for SFDB we do not need to construct or
query stalks explicitly; the context-indexed sections serve the same role.

## Why Stalks Matter Conceptually

While the stalk computation is trivial for Alexandrov spaces, the
concept is important for the **global sections** functor and the
**sheafification** process:

1. The **global sections functor** $\Gamma(X, -): \mathbf{Sh}(X) \to \mathbf{Set}$
   sends a sheaf $F$ to its set of global sections $F(X)$.  This is computed
   by gluing compatible local sections.
2. In sheaf cohomology, stalks are used to compute cohomology groups
   that measure the obstructions to gluing local sections into global ones.

## References

- Mac Lane & Moerdijk, *Sheaves in Geometry and Logic* (1992), §II.2, §II.5.
- Hartshorne, *Algebraic Geometry* (1977), §II.1.
