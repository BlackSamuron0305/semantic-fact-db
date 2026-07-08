# Formal Properties of the Canonical Semantic Model

## 1. Losslessness

A mapping phi: A -> B is **lossless** if there exists a
right-inverse psi: B -> A such that psi(phi(a)) = a for all
a in A.

### Claim
The mappings iota_KG: KG -> SemanticFact and
iota_Sheaf: Sheaf -> SemanticFact are lossless.

### Proof sketch
Both mappings produce a SemanticFact whose fields are populated from
the source representation without projection or approximation.  The
inverse mapping (from_canonical) reconstructs the source
representation from the SemanticFact.  Because the SemanticFact
stores the complete n-ary structure (including all object slots,
attributes, provenance, temporal info, and metadata), no information is
lost.

## 2. Determinism

A mapping phi is **deterministic** if phi(a) is always the same
value for the same a.

### Claim
All canonical mappings are deterministic.

### Justification
Every mapping function is pure: it depends only on its input and has no
side effects.  No random number generation, no mutable state, no
environment dependence enters the mapping logic.  The serialisation
formatters (JSON, Parquet, MessagePack) are also deterministic because
they use sorted keys and fixed-precision arithmetic.

## 3. Referential Integrity

A collection of facts satisfies **referential integrity** if every
identifier that appears as a reference (subject, relation, or object
reference) corresponds to an existing entity.

### Claim
The canonical model enforces referential integrity at the collection
level.  Individual facts may reference entities that are resolved by
the containing model.

### Invariant
For any SemanticFact f in a collection C, if f contains a
reference id_ref in any of its fields (subject, relation, objects),
then there exists at least one fact in C whose identifier equals
id_ref (or the identifier is registered as an entity-level identifier).

## 4. Semantic Equivalence

Two representations R1 and R2 are **semantically equivalent** if
their canonical images are equal:

    R1 ~ R2  iff  iota(R1) = iota(R2)

### Claim
For any input data set, the KG and SheafDB produce semantically
equivalent canonical models.

### Verification
This is tested by:
1. Insert the same facts into both systems.
2. Extract all facts in canonical form from each system.
3. Compare the two canonical sets for equality.

If iota_KG(KG) = iota_Sheaf(Sheaf), the representations are
semantically equivalent.

## 5. Invertibility

A mapping phi: A -> B is **invertible** if there exists an inverse
mapping phi^{-1}: B -> A such that phi^{-1}(phi(a)) = a for all
a in A and phi(phi^{-1}(b)) = b for all b in B.

### Claim
The canonical mappings iota_KG and iota_Sheaf are injective but not
necessarily surjective onto the full space of SemanticFact.  They are
invertible on their images (left-invertible).

### Proof
Injectivity follows from losslessness: distinct inputs produce distinct
SemanticFact instances because the mapping is a bijection between the
source representation and its image.