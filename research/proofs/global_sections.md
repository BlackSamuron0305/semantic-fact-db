# Global Sections

## Definition

Let $F: \mathcal{T}^{\text{op}} \to \mathbf{Set}$ be a sheaf on a
topological space $X$.  A **global section** of $F$ is an element
of $F(X)$, the set of sections over the whole space $X$.

## Interpretation for SFDB

In the context poset $(C, \leq)$ with its Alexandrov topology, the
whole space $X$ corresponds to the down-set $\downarrow c_0$ where
$c_0 = \text{world}$ is the root context.  A **global section** is
therefore a fact that holds in the root context — i.e. a fact that
is valid **everywhere**.

### Computing Global Sections

Given a sheaf $F$ on $C$, the set of global sections is computed by
starting with local sections over the minimal (most specific) contexts
and gluing upward:

1. Collect all maximal local sections (those not obtained by restriction
   from a broader context).
2. Check compatibility on overlaps (meets of contexts).
3. Apply the gluing axiom to combine compatible sections into sections
   over broader contexts.
4. Repeat until reaching the root context $c_0$.

### Relationship to the Canonical Model

The set of global sections $F(c_0)$ is exactly the set of
``SemanticFact`` instances in the canonical model that are context-free.
These are the facts that hold regardless of contextual scoping.

In the benchmark, both the KG and SheafDB must produce the same set of
global sections for the same input data.  This is the primary check
for **semantic equivalence**.

## Properties

1. **Uniqueness**: If a compatible family of local sections exists,
   the global section obtained by gluing is unique.
2. **Locality**: If two global sections agree on every neighbourhood,
   they are identical.
3. **Functoriality**: The global sections functor $\Gamma(X, -)$ is
   left-exact but not generally right-exact — the failure of
   right-exactness is measured by sheaf cohomology.

## References

- Mac Lane & Moerdijk, *Sheaves in Geometry and Logic* (1992), §II.2–3.
- Hartshorne, *Algebraic Geometry* (1977), §II.1–2.
