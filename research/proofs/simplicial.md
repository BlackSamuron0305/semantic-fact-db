# Simplicial Sets — A Secondary Mathematical Approach

## Definition (Simplicial Set)

A **simplicial set** is a functor

    X: Delta^op -> Set

where Delta is the **simplex category** whose objects are finite totally
ordered sets [n] = {0, 1, ..., n} and whose morphisms are order-preserving
functions (face maps d_i and degeneracy maps s_i).

Explicitly, a simplicial set consists of:

- Sets X_n for each n >= 0 (the **n-simplices**).
- **Face maps** d_i: X_n -> X_{n-1} for 0 <= i <= n, which delete the
  i-th vertex.
- **Degeneracy maps** s_i: X_n -> X_{n+1} for 0 <= i <= n, which repeat
  the i-th vertex.

These satisfy the **simplicial identities**:

    d_i d_j = d_{j-1} d_i   for i < j
    d_i s_j = s_{j-1} d_i   for i < j
    d_j s_j = d_{j+1} s_j = id
    d_i s_j = s_j d_{i-1}   for i > j+1
    s_i s_j = s_{j+1} s_i   for i <= j

## Interpretation for SFDB

A semantic fact with arity n can be viewed as an **n-simplex** whose
vertices are the entities and values involved:

- 0-simplices (vertices): individual entities or values.
- 1-simplices (edges): binary relations.
- 2-simplices (triangles): ternary events.
- n-simplices: n-ary events.

The **face maps** correspond to restriction: taking a subset of the
participants.  The **degeneracy maps** correspond to adding redundant
information.

### Boundary Operator

The boundary of an n-simplex is the alternating sum of its faces:

    partial_n = sum_{i=0}^n (-1)^i d_i

This operator satisfies the fundamental property:

    partial_{n-1} circ partial_n = 0

which is the defining equation of a **chain complex**.  This property
ensures that the boundary of a boundary is always zero — a necessary
condition for consistent knowledge.

### Simplicial Database

A SimplicialDatabase would store facts as simplices in a simplicial set,
using:

- **Simplex Index**: maps simplex IDs to their vertices.
- **Incidence Matrix**: records which simplices share faces.
- **Boundary Operator**: computes the boundary of any simplex.
- **Dimension Index**: groups simplices by dimension.

The key advantage over the sheaf approach is that the simplicial
structure naturally handles **partial information** (a k-simplex with
k < n can represent incomplete knowledge about an n-ary event) and
provides a well-defined notion of **homology**: inconsistencies
appear as non-zero homology groups.

## Comparison with Sheaves

| Property | Sheaf | Simplicial Set |
|----------|-------|---------------|
| Primitive | Section over context | Simplex |
| Structure | Poset of contexts | Simplicial category |
| Consistency | Gluing condition | `partial^2 = 0` |
| Partial info | Restriction maps | Face maps |
| Inference | Gluing | Filling horns |
| Cohomology | Sheaf cohomology | Simplicial homology |

## References

- P. Goerss and J. Jardine, *Simplicial Homotopy Theory* (1999).
- G. Friedman, *An Elementary Illustrated Introduction to Simplicial Sets* (2012).
- J. P. May, *Simplicial Objects in Algebraic Topology* (1967).