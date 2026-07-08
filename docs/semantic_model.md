# Semantic Fact Model — Documentation

## Overview

The Semantic Fact Model is the canonical representation of knowledge in
the SFDB project.  Every storage engine (Knowledge Graph, Sheaf Database)
maps to and from this model.  The model is **storage-agnostic**:
it captures only semantics, never physical layout.

## Core Type: SemanticFact

SemanticFact is an immutable Python dataclass with the following fields:

### id (Identifier)
A globally unique identifier for the fact.  Generated as a UUID4 string
by default.  Can be supplied explicitly for deterministic addressing.
Identifier ordering is lexicographic by string representation.

### subject (Identifier)
The primary entity the fact is about.  Example: for a fact "Alice signed
contract C42", the subject would be the Identifier for "Alice".

### relation (Identifier)
The type of relationship or event.  Examples: "signed", "knows",
"located_in", "born_on".  Relations are identified by their own
Identifiers, enabling relation-level metadata.

### objects (tuple of Value)
The n-ary object slots of the fact.  Each Value is either:

- **Literal**: a string, number, or boolean (e.g. "contract-42", 2024,
  True).
- **Reference**: a pointer to another entity via its Identifier (e.g.
  a reference to the entity "Bob").

The number of objects is the **arity** of the fact.  Arity can be 0
(for existence facts), 1 (binary relation), or more (n-ary event).

### attributes (dict of str to Value)
Named attributes that qualify the fact.  Unlike object slots, attributes
are unordered key-value pairs.  Examples: {"date": Value.literal("2024-03-15"),
"location": Value.literal("Geneva")}.

### context (Context)
The semantic scope where this fact holds.  Contexts are dot-separated
paths forming a poset: "world" > "world.2024" > "world.2024.science".
A narrower context is a sub-context (more specific) of a broader one.

### provenance (Provenance)
Who asserted this fact, when, and how.  Contains:
- source: human-readable origin string
- recorded_at: UTC timestamp of ingestion
- confidence: source-level confidence [0, 1]
- method: how obtained ("extraction", "inference", "manual", etc.)

### confidence (float)
Overall confidence in [0, 1].  Combined with provenance.confidence
this provides a two-level confidence model: source reliability + fact
certainty.

### temporal (TemporalInfo or None)
Optional temporal validity interval.  When set, the fact is only
guaranteed to hold during [start, end).  When None, the fact is
timeless.

### metadata (dict of str to Any)
Arbitrary key-value metadata.  Preserved through serialisation
round-trips.  Excluded from equality and hashing to allow
application-specific extensions without affecting identity.

## Invariants

1. **Immutability**: SemanticFact is frozen.  No field can be modified
   after construction.

2. **Global uniqueness**: Every SemanticFact has a distinct id.

3. **Confidence bounds**: Both fact.confidence and
   provenance.confidence must be in [0, 1].

4. **Temporal consistency**: If temporal.end is set, temporal.start
   must also be set.  end must not precede start.

5. **Provenance preservation**: Provenance metadata is never stripped
   during serialisation or mapping.

6. **Lossless round-trip**: Every serialiser preserves all fields
   exactly.

## Mapping to Knowledge Graph

A SemanticFact is mapped to RDF triples via reification:

1. An event node is created for the fact.
2. The subject, relation, and each object become triples with the
   event node as subject.
3. Attributes become additional triples.
4. Provenance and temporal info become reification-level triples.

The number of triples generated is O(arity + |attributes|).

## Mapping to Sheaf Database

A SemanticFact is stored as a section in its maximal context:

1. The fact is assigned to its context in the SheafStore.
2. Restriction maps to sub-contexts are computed lazily or eagerly.
3. Gluing checks are performed when overlapping sections exist.
4. Global sections are computed by gluing compatible local sections.

## Serialisation

See the serialisation module for details on JSON, Parquet, and
MessagePack formats.  All serialisers are deterministic and
guarantee lossless round-trips.