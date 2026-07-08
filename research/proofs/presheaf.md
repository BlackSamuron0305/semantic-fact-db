# Presheaf

## Definition

Let $C$ be a category (in our case, the context poset viewed as a
category).  A **presheaf** on $C$ is a functor

\[
F: C^{\text{op}} \longrightarrow \mathbf{Set}.
\]

Explicitly:

- To each object $c \in \operatorname{Ob}(C)$, the presheaf assigns a set
  $F(c)$, called the set of **sections** over $c$.
- To each morphism $f: c \to d$ in $C$ (i.e. $d \leq c$ in the poset),
  the presheaf assigns a function
  \[
  F(f): F(d) \to F(c),
  \]
  called the **restriction map** along $f$.

These must satisfy **functoriality**:

1. $F(\operatorname{id}_c) = \operatorname{id}_{F(c)}$ for every $c$.
2. $F(g \circ f) = F(f) \circ F(g)$ whenever $f$ and $g$ are composable.

## Interpretation for SFDB

In the SFDB context:

- $C$ is the poset $(\text{Contexts}, \leq)$ with $c_1 \leq c_2$ meaning
  $c_1$ is a sub-context (more specific) of $c_2$.
- The opposite category $C^{\text{op}}$ reverses this: a morphism
  $c_1 \to c_2$ in $C^{\text{op}}$ corresponds to $c_2 \leq c_1$ in $C$,
  i.e. restriction from a broader context to a narrower one.
- $F(c)$ is the set of **semantic facts** (``SemanticFact`` instances)
  that are valid in context $c$.
- $F(f): F(d) \to F(c)$ for $c \leq d$ restricts a fact from the broader
  context $d$ to the narrower context $c$ by dropping object slots that
  are not meaningful in $c$, or by specialising values.

## Examples

**Example 1 (trivial context).**  Let $C = \{*\}$ be a single object.
Then a presheaf is just a set $F(*)$ with identity restriction.  This
corresponds to a set of global facts with no contextual structure.

**Example 2 (linearly ordered contexts).**  Let
$C = \{\text{world} \geq \text{world.2024} \geq \text{world.2024.physics}\}$.
A presheaf assigns three sets $F(\text{world})$, $F(\text{world.2024})$,
$F(\text{world.2024.physics})$ with restriction maps:

\[
\rho_{\text{world.2024.physics}}^{\text{world.2024}}:
F(\text{world.2024}) \to F(\text{world.2024.physics})
\]

and similarly from world to world.2024 and world to
world.2024.physics (by composition).

## References

- Mac Lane & Moerdijk, *Sheaves in Geometry and Logic* (1992), §II.1.
- Tennison, *Sheaf Theory* (1975), §1.1–1.3.
