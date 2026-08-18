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

**Corrected 2026-08-16.** An earlier version of this note (and of the
paper's own Definition of Restriction Map, since fixed) described
restriction as rewriting a fact's context field and, for restrictions
"that cross domain boundaries," dropping or specialising object slots.
Neither claim matches what any restriction implementation in the
codebase actually does. `sfdb.sheaf.presheaf.Presheaf.restrict` — the
one the live query planner and the consistency checker actually
call — is a **membership filter**: it returns each section from the
broader open set *unchanged* (same fact object, same `open_set_name`)
that also happens to be a member of the narrower open set, and
otherwise excludes it. No field of the fact is read or rewritten, and
the "same fact but with its context field changed" description above
was simply wrong — the fact's context is fixed at insert time and
restriction does not touch it.

Concretely: for context $c_1 \le c_2$ (so $U_{c_1} \subseteq U_{c_2}$)
and a fact $f \in F(c_2)$,

\[
\rho_{c_2, c_1}(f) =
\begin{cases}
f & \text{if } \operatorname{context}(f) \le c_1 \text{ (i.e. } f \in U_{c_1}\text{)}, \\
\text{undefined} & \text{otherwise.}
\end{cases}
\]

Restriction succeeds exactly when the fact was *already* valid at the
narrower context — it is the identity on its (partial) domain, not a
specialisation operation. This is the presheaf of "visibility from an
open set," which is a legitimate and useful presheaf construction, just
not the one the original text above described.

Restriction maps are **deterministic**: given the same fact and target
context, they always produce the same result (either $f$ itself, or
undefined).

## Example

Given $c_2 = \text{world.2024}$ and $c_1 = \text{world.2024.physics}$, and
a fact $f$ = SIGNED$(e, c, \text{contract-42}, \text{2024-03-15}, \dots)$
whose own context is $\text{world.2024.physics}$ (i.e. $f \in U_{c_1}$
already):

\[
\rho_{c_2, c_1}(f) = f
\]

returned unchanged, because $f$ was already a member of the narrower
open set. If instead $f$'s own context were $\text{world.2024.chemistry}$
(a sibling of $c_1$, not $\le c_1$), $\rho_{c_2, c_1}(f)$ would be
undefined — restriction is not a general specialisation operator, it can
only "find" a fact in a narrower scope it was already visible from.

## References

- Mac Lane & Moerdijk, *Sheaves in Geometry and Logic* (1992), §II.1.
- Tennison, *Sheaf Theory* (1975), §1.4.
