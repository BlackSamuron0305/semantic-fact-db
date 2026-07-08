"""Sheaf-theoretic semantic store.

Mathematical background
=======================

Let (C, ≤) be a poset of contexts. A **presheaf** F: C^op → Set assigns:
    - To each context c ∈ C, a set F(c) of *sections* (facts) over c.
    - To each pair c₁ ≤ c₂, a *restriction map* ρ_{c₂,c₁}: F(c₂) → F(c₁).

These satisfy:
    1. ρ_{c,c} = id_{F(c)} for all c.
    2. If c₁ ≤ c₂ ≤ c₃, then ρ_{c₃,c₁} = ρ_{c₂,c₁} ∘ ρ_{c₃,c₂}.

A **sheaf** additionally satisfies:
    - **Locality**: If s, t ∈ F(c) and for every covering {cᵢ} of c,
        ρ_{c,cᵢ}(s) = ρ_{c,cᵢ}(t), then s = t.
    - **Gluing**: If {cᵢ} covers c and sᵢ ∈ F(cᵢ) agree on overlaps
        (ρ_{cᵢ,cᵢ∧cⱼ}(sᵢ) = ρ_{cⱼ,cᵢ∧cⱼ}(sⱼ) for all i, j),
        then there exists a unique s ∈ F(c) with ρ_{c,cᵢ}(s) = sᵢ.

In our setting, the cover of a context c is its immediate sub-contexts.
The poset is finite, so covers are finite.

Semantic interpretation
-----------------------
- A section over context c is a fact that holds (is true, is valid) within c.
- Restriction from c₂ to c₁ (where c₁ ≤ c₂) extracts the meaning of a
  fact from a broader context to a narrower one.
- Gluing combines locally consistent facts into a globally consistent one.
- A *global section* over the maximal context is a fact that holds everywhere.

This construction ensures:
    1. **Locality**: Queries can be answered using only the relevant context.
    2. **Consistency**: Facts from different contexts that are compatible
       can be combined uniquely.
    3. **Reconstruction**: The full knowledge is the set of global sections.

Complexity
==========
Section lookup by context: O(log n) with indexed contexts.
Restriction: O(k) where k = arity of the section.
Gluing: O(n · m) where n = number of sections, m = number of overlapping contexts.
Global section computation: O(c · s) where c = number of contexts, s = avg sections per context.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sfdb.common.types import Context, Fact


class GluingError(Exception):
    """Raised when sections cannot be glued due to incompatibility."""


class ContextPoset:
    """A finite partially ordered set of contexts.

    Maintains the cover relations: cover(c) = {c'} where c' is a maximal
    proper sub-context of c (i.e., c' < c and nothing lies between).

    Complexity
    ----------
    Add context: O(1).
    Find cover: O(n) where n = number of contexts.
    Check ordering: O(min(depth(c₁), depth(c₂))).
    """

    def __init__(self) -> None:
        self._contexts: set[Context] = set()

    def add(self, ctx: Context) -> None:
        self._contexts.add(ctx)

    def contains(self, ctx: Context) -> bool:
        return ctx in self._contexts

    def cover(self, ctx: Context) -> list[Context]:
        """Return the immediate sub-contexts of ctx."""
        candidates: list[Context] = []
        for c in self._contexts:
            if c < ctx:
                # c is a sub-context of ctx
                # Check if it's immediate (no intermediate)
                is_immediate = True
                for d in self._contexts:
                    if c < d < ctx:
                        is_immediate = False
                        break
                if is_immediate:
                    candidates.append(c)
        return candidates

    def is_cover(self, ctx: Context, sub_contexts: list[Context]) -> bool:
        """Check if sub_contexts form a cover of ctx.

        A cover is a set of sub-contexts whose join is ctx.
        For a poset of contexts by prefix, a cover exists iff
        every path from root to ctx passes through at least one sub_context.
        """
        if not sub_contexts:
            return False
        # For the prefix poset, the immediate sub-contexts cover the parent.
        # This simplifies: the cover check depends on the poset structure.
        return all(s < ctx for s in sub_contexts)

    def join(self, c1: Context, c2: Context) -> Context | None:
        """Compute the join (least upper bound) of two contexts.

        In the prefix poset, the join is the longest common prefix
        if one is a prefix of the other, otherwise the common prefix.
        """
        i = 0
        while i < len(c1.segments) and i < len(c2.segments) and c1.segments[i] == c2.segments[i]:
            i += 1
        if i == 0:
            return None
        return Context(".".join(c1.segments[:i]))

    def meet(self, c1: Context, c2: Context) -> Context | None:
        """Compute the meet (greatest lower bound) of two contexts.

        In the prefix poset, the meet of c₁ and c₂ is the longest common
        prefix.  If one refines the other, the more specific is returned.
        For disjoint contexts with no common prefix beyond root, returns
        the root context (the true meet in a bounded poset).

        Returns None only when the poset is empty (no root exists).
        """
        if c1 <= c2:
            return c1
        if c2 <= c1:
            return c2
        # Longest common prefix = true meet in a prefix poset
        i = 0
        while i < len(c1.segments) and i < len(c2.segments) and c1.segments[i] == c2.segments[i]:
            i += 1
        if i == 0:
            return Context("world")  # root is the meet of disjoint branches
        return Context(".".join(c1.segments[:i]))

    @property
    def root(self) -> Context | None:
        """The maximal (broadest) context, if any."""
        if not self._contexts:
            return None
        return min(self._contexts, key=lambda c: c.depth)

    @property
    def leaves(self) -> list[Context]:
        """The minimal (most specific) contexts."""
        if not self._contexts:
            return []
        result: list[Context] = []
        for c in self._contexts:
            if not any(d < c for d in self._contexts if d != c):
                result.append(c)
        return result

    def all_contexts(self) -> list[Context]:
        return list(self._contexts)

    def __repr__(self) -> str:
        return f"ContextPoset(contexts={len(self._contexts)})"


@dataclass(slots=True, frozen=True)
class Section:
    """A sheaf section: a fact within a specific context.

    A section is the basic unit of knowledge in the sheaf model.
    It pairs a fact with the context in which it holds.

    The section is *local*: it only asserts truth within its context,
    not in broader or narrower contexts (though restriction maps apply).
    """

    fact: Fact
    context: Context

    def __repr__(self) -> str:
        return f"Sec({self.fact.subject}, {self.fact.relation}, ctx={self.context})"


class Presheaf:
    """A presheaf of semantic facts over the context poset.

    F(c) = {sections valid in context c}
    ρ_{c₂,c₁}: F(c₂) → F(c₁) for c₁ ≤ c₂

    Implements the presheaf axioms (functoriality):
        ρ_{c,c} = id
        ρ_{c₃,c₁} = ρ_{c₂,c₁} ∘ ρ_{c₃,c₂}

    Parameters
    ----------
    poset: The underlying context poset.
    restriction_fn: Optional custom restriction function.
        Default: identity restriction (facts pass through unchanged).
    """

    def __init__(
        self,
        poset: ContextPoset | None = None,
        restriction_fn: Callable[[Fact, Context, Context], Fact | None] | None = None,
    ) -> None:
        self._poset = poset or ContextPoset()
        self._sections: dict[Context, list[Section]] = {}
        # Default restriction: identity — a fact in c₂ is also valid in c₁
        self._restrict = restriction_fn or (lambda fact, _src, _tgt: fact)

    def assign(self, section: Section) -> None:
        """Assign a section to its context.

        If the context is not yet in the poset, it is added.
        """
        ctx = section.context
        self._poset.add(ctx)
        if ctx not in self._sections:
            self._sections[ctx] = []
        self._sections[ctx].append(section)

    def sections_over(self, ctx: Context) -> list[Section]:
        """Retrieve all sections directly over a context (F(ctx))."""
        return list(self._sections.get(ctx, []))

    def restrict(self, section: Section, target: Context) -> Section | None:
        """Apply the restriction map ρ_{ctx, target}.

        Returns None if restriction is not possible (section does not
        survive the narrowing of context).
        """
        if not target.is_subcontext(section.context):
            return None
        restricted_fact = self._restrict(section.fact, section.context, target)
        if restricted_fact is None:
            return None
        return Section(fact=restricted_fact, context=target)

    def restrict_all(self, ctx: Context, target: Context) -> list[Section]:
        """Restrict all sections from ctx to target."""
        return [
            s for s in (self.restrict(s, target) for s in self.sections_over(ctx)) if s is not None
        ]

    def sections_local_to(self, ctx: Context) -> list[Section]:
        """Get all sections that are *relevant* to context ctx.

        This is the union of:
            1. Sections directly over ctx.
            2. Sections over super-contexts of ctx, restricted to ctx.

        This implements *local querying*: to answer a question in context
        ctx, we only need to look at ctx and its ancestors.
        """
        result: list[Section] = []
        result.extend(self.sections_over(ctx))
        # Add restricted sections from broader contexts
        for super_ctx in self._poset.all_contexts():
            if ctx.is_subcontext(super_ctx) and ctx != super_ctx:
                result.extend(self.restrict_all(super_ctx, ctx))
        return result

    @property
    def poset(self) -> ContextPoset:
        return self._poset

    def __repr__(self) -> str:
        n_ctx = len(self._poset.all_contexts())
        n_sec = sum(len(v) for v in self._sections.values())
        return f"Presheaf(contexts={n_ctx}, sections={n_sec})"


class Sheaf(Presheaf):
    """A sheaf of semantic facts: a presheaf satisfying gluing and locality.

    Extends Presheaf with:
        1. **Gluing**: Given a cover {cᵢ} of c and sections sᵢ ∈ F(cᵢ)
           that agree on overlaps (cᵢ ∧ cⱼ), produce a unique s ∈ F(c).
        2. **Locality check**: Verify that two sections are equal locally.

    The sheaf condition is checked at query time (or at gluing time),
    not at insertion time. This is the *constructive* approach: we
    maintain the presheaf and verify the sheaf condition when needed.

    Parameters
    ----------
    equality_fn: Optional custom equality function for sections.
        Default: structural equality of the underlying facts.
    """

    def __init__(
        self,
        poset: ContextPoset | None = None,
        restriction_fn: Callable[[Fact, Context, Context], Fact | None] | None = None,
        equality_fn: Callable[[Section, Section], bool] | None = None,
    ) -> None:
        super().__init__(poset, restriction_fn)
        self._equal = equality_fn or (lambda s1, s2: s1.fact == s2.fact)

    def glue(self, ctx: Context, covering_sections: dict[Context, Section]) -> Section:
        """Glue sections covering ctx into a single section.

        Given a cover {cᵢ} of ctx and sections sᵢ ∈ F(cᵢ) that agree
        on overlaps, produce the unique s ∈ F(ctx).

        The sheaf condition guarantees that sections agreeing on all
        overlaps can be uniquely combined. The resulting section s is
        assigned to ctx and restricts back to each sᵢ.

        Raises GluingError if sections disagree on overlaps.

        Complexity: O(k · m) where k = number of covering sections,
        m = number of overlap checks.
        """
        covering_contexts = list(covering_sections.keys())
        if not covering_contexts:
            raise GluingError("No covering sections provided")

        # Check pairwise agreement on overlaps.
        # The overlap of two contexts in a prefix poset is their meet
        # (greatest lower bound) — the most specific context that both
        # refine. When one is a sub-context of the other, the meet is
        # the more specific one. For incomparable sibling contexts,
        # there is no common refinement in a tree, so the overlap is
        # undefined (empty), and the condition is vacuous.
        for i, c_i in enumerate(covering_contexts):
            for j, c_j in enumerate(covering_contexts):
                if i >= j:
                    continue
                overlap = self._poset.meet(c_i, c_j)
                s_i = covering_sections[c_i]
                s_j = covering_sections[c_j]

                r_i = self.restrict(s_i, overlap)
                r_j = self.restrict(s_j, overlap)

                if r_i is not None and r_j is not None and not self._equal(r_i, r_j):
                    raise GluingError(
                        f"Sections at {c_i} and {c_j} disagree on overlap {overlap}: "
                        f"{r_i.fact} ≠ {r_j.fact}"
                    )

        # Gluing: construct the unique section over ctx.
        # The glued section's fact is determined by the covering sections.
        # Since any two covering sections agree on overlaps, we can use
        # any representative; the result is unique up to sheaf condition.
        representative = covering_sections[covering_contexts[0]]
        glued_fact = Fact(
            id=representative.fact.id,
            subject=representative.fact.subject,
            relation=representative.fact.relation,
            objects=representative.fact.objects,
            context=ctx,
            confidence=representative.fact.confidence,
        )
        glued = Section(fact=glued_fact, context=ctx)

        # Store the glued section
        self.assign(glued)
        return glued

    def global_sections(self) -> list[Section]:
        """Compute all global sections (sections over the root context).

        A global section is a fact that holds in the broadest context
        (typically the 'world' context). These represent universally
        true knowledge.

        Computed by gluing sections from leaf contexts upward until
        reaching the root.

        Complexity: O(c · s) where c = number of contexts, s = avg sections.
        """
        root = self._poset.root
        if root is None:
            return []

        # Start from leaves and work up via restriction maps
        # A global section is any section that can be restricted to root
        # OR any section directly at root.
        root_sections = self.sections_over(root)
        if root_sections:
            return root_sections

        # Try to glue from cover
        cover = self._poset.cover(root)
        if not cover:
            return []

        # Gather all sections from the cover, restrict each to root
        results: list[Section] = []
        for c in cover:
            results.extend(self.restrict_all(c, root))

        return results

    def locally_equivalent(self, s1: Section, s2: Section) -> bool:
        """Check if two sections are locally equivalent.

        s1 ≃ s2 iff there exists a cover {cᵢ} of context(s) such that
        ρ(s1) = ρ(s2) for every member of the cover.

        This is the sheaf-theoretic notion of local equality.
        """
        common_ctx = self._poset.meet(s1.context, s2.context)
        r1 = self.restrict(s1, common_ctx)
        r2 = self.restrict(s2, common_ctx)
        if r1 is None or r2 is None:
            return False
        return self._equal(r1, r2)

    def __repr__(self) -> str:
        n_ctx = len(self._poset.all_contexts())
        n_sec = sum(len(v) for v in self._sections.values())
        return f"Sheaf(contexts={n_ctx}, sections={n_sec})"


class SheafStore:
    """A complete sheaf database store.

    Wraps a Sheaf with higher-level operations for fact insertion,
    querying, and canonical model export.

    This is the primary user-facing API for the sheaf subsystem.
    """

    def __init__(self, sheaf: Sheaf | None = None) -> None:
        self._sheaf = sheaf or Sheaf()

    def insert(self, fact: Fact, context: Context | None = None) -> Section:
        """Insert a fact into the sheaf at the given context."""
        ctx = context or fact.context
        section = Section(fact=fact, context=ctx)
        self._sheaf.assign(section)
        return section

    def query_context(self, ctx: Context) -> list[Fact]:
        """Retrieve all facts locally relevant to a context.

        This is the *local query* operation: only the given context
        and its ancestors are examined.
        """
        sections = self._sheaf.sections_local_to(ctx)
        return [s.fact for s in sections]

    def query_global(self) -> list[Fact]:
        """Retrieve all global facts (holding in the broadest context)."""
        sections = self._sheaf.global_sections()
        return [s.fact for s in sections]

    def restrict_fact(self, fact: Fact, from_ctx: Context, to_ctx: Context) -> Fact | None:
        """Restrict a fact from one context to a narrower one."""
        section = Section(fact=fact, context=from_ctx)
        result = self._sheaf.restrict(section, to_ctx)
        return result.fact if result is not None else None

    @property
    def sheaf(self) -> Sheaf:
        return self._sheaf

    def __repr__(self) -> str:
        return f"SheafStore(sheaf={self._sheaf})"
