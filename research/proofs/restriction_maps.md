# Restriction Maps

## Definition

Let $(C, \leq)$ be a poset of contexts and $F: C^{\text{op}} \to \mathbf{Set}$
a presheaf.  For any pair $c_1, c_2 \in C$ with $c_1 \leq c_2$ (i.e. $c_1$
is a sub-context of $c_2$), the **restriction map**

\[
\rho_{c_2, c_1}: F(c_2) \longrightarrow F(c_1)
\]

takes a section (semantic fact) valid in the broader context $c_2$ and
produces a section valid in the narrower context $c_1$.

## Functoriality

Restriction maps must satisfy:

1. **Identity**: $\rho_{c, c} = \operatorname{id}_{F(c)}$ for every $c \in C$.
2. **Composition**: For $c_1 \leq c_2 \leq c_3$,
   \[
   \rho_{c_3, c_1} = \rho_{c_2, c_1} \circ \rho_{c_3, c_2}.
   \]

## Interpretation for SFDB

In the SFDB model, a restriction map specialises a fact from a broader
context to a narrower one.  Concretely, if a fact

\[
f = (\text{id}, s, r, \vec{o}, \text{attrs}, c_2, \text{prov}, \text{conf}, \text{temp}, \text{meta})
\]

is valid in $c_2$, then $\rho_{c_2, c_1}(f)$ is the same fact but with its
context field changed to $c_1$.  For the root restriction (when $c_1$ is
a direct refinement of $c_2$), no values are modified — the fact is simply
re-contextualised.  For restrictions that cross domain boundaries, certain
object slots may be dropped or specialised according to domain-specific
rules.

Restriction maps are **deterministic**: given the same fact and target
context, they always produce the same result.

## Examples

Given $c_2 = \text{world.2024}$ and $c_1 = \text{world.2024.physics}$:

\[
\rho_{c_2, c_1}(\text{SIGNED}(e, c, \text{contract-42}, \text{2024-03-15}, \dots))
= \text{SIGNED}(e, c, \text{contract-42}, \text{2024-03-15}, \dots)
\]

with context changed from world.2024 to world.2024.physics.  The fact
continues to hold in the narrower domain.

## References

- Mac Lane & Moerdijk, *Sheaves in Geometry and Logic* (1992), §II.1.
- Tennison, *Sheaf Theory* (1975), §1.4.
