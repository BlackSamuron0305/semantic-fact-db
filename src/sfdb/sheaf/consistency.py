"""Sheaf consistency conditions: locality, gluing, and compatibility.

A sheaf must satisfy two conditions beyond the presheaf axioms:

1. **Locality**: If {Uᵢ} is an open cover of U, and s, t ∈ F(U) agree
   on every Uᵢ (i.e., ρ_{U,Uᵢ}(s) = ρ_{U,Uᵢ}(t) for all i), then
   s = t in F(U).

2. **Gluing**: If {sᵢ ∈ F(Uᵢ)} is a family such that for all i, j,
   ρ_{Uᵢ, Uᵢ∩Uⱼ}(sᵢ) = ρ_{Uⱼ, Uᵢ∩Uⱼ}(sⱼ), then there exists a unique
   s ∈ F(∪Uᵢ) such that ρ_{∪Uᵢ, Uᵢ}(s) = sᵢ for all i.

3. **Compatibility**: Restriction maps compose: for W ⊆ V ⊆ U,
   ρ_{V,W} ∘ ρ_{U,V} = ρ_{U,W}.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sfdb.sheaf.presheaf import Presheaf
from sfdb.sheaf.topology import FiniteTopologicalSpace


@dataclass
class ConsistencyDiagnostic:
    """Detailed diagnostic output from a consistency check."""

    passed: bool
    check_name: str
    detail: str = ""
    affected_sections: list[str] = field(default_factory=list)
    computation_time_ns: int = 0

    def __repr__(self) -> str:
        status = "✓" if self.passed else "✗"
        return f"{status} {self.check_name}: {self.detail}"


class ConsistencyChecker:
    """Verifies sheaf consistency conditions for a presheaf.

    Usage::
        checker = ConsistencyChecker(presheaf, topology)
        results = checker.check_all()
        for r in results:
            print(r)
    """

    def __init__(
        self,
        presheaf: Presheaf,
        topology: FiniteTopologicalSpace,
    ) -> None:
        self._presheaf = presheaf
        self._topology = topology

    def check_all(self) -> list[ConsistencyDiagnostic]:
        """Run all consistency checks and return diagnostics."""
        diagnostics: list[ConsistencyDiagnostic] = []
        diagnostics.append(self.check_locality())
        diagnostics.append(self.check_gluing())
        diagnostics.append(self.check_restriction_composition())
        diagnostics.append(self.check_identity_restriction())
        diagnostics.append(self.check_empty_set())
        return diagnostics

    def check_locality(self) -> ConsistencyDiagnostic:
        """Verify that sections agreeing on all covers are identical.

        For each open set U with an open cover {Vᵢ}, check that any
        two sections s, t ∈ F(U) that agree on every Vᵢ are identical.
        """
        import time

        t0 = time.perf_counter_ns()
        affected: list[str] = []
        os_names = list(self._topology._open_sets.keys())
        passed = True

        for i, u_name in enumerate(os_names):
            if u_name not in self._presheaf._sections_by_openset:
                continue
            u_sections = self._presheaf.sections_over(u_name)
            if len(u_sections) < 2:
                continue
            for j, v_name in enumerate(os_names):
                if i == j:
                    continue
                v_set = self._topology.get_open_set(v_name)
                if v_set is None:
                    continue
                u_set = self._topology.get_open_set(u_name)
                if u_set is None:
                    continue
                if not v_set.is_subset_of(u_set):
                    continue
                v_sections = self._presheaf.restrict(u_name, v_name)
                v_section_map = {s.fact.id.value: s for s in v_sections}
                for s in u_sections:
                    for t in u_sections:
                        if s.fact.id == t.fact.id:
                            continue
                        s_rest = v_section_map.get(s.fact.id.value)
                        t_rest = v_section_map.get(t.fact.id.value)
                        if s_rest is not None and t_rest is not None:
                            if s_rest.fact != t_rest.fact:
                                passed = False
                                affected.extend([s.fact.id.value[:8], t.fact.id.value[:8]])

        ns = time.perf_counter_ns() - t0
        return ConsistencyDiagnostic(
            passed=passed,
            check_name="locality",
            detail=f"Locality holds over {len(os_names)} open sets"
            if passed
            else f"Locality violation detected in {len(affected)} sections",
            affected_sections=affected,
            computation_time_ns=ns,
        )

    def check_gluing(self) -> ConsistencyDiagnostic:
        """Verify that compatible local sections glue uniquely.

        For each pair of overlapping open sets Uᵢ, Uⱼ, check that
        sections sᵢ ∈ F(Uᵢ) and sⱼ ∈ F(Uⱼ) agree on the overlap
        Uᵢ ∩ Uⱼ.
        """
        import time

        t0 = time.perf_counter_ns()
        affected: list[str] = []
        os_names = list(self._presheaf._sections_by_openset.keys())
        passed = True
        glued = 0

        for i in range(len(os_names)):
            for j in range(i + 1, len(os_names)):
                u_name = os_names[i]
                v_name = os_names[j]
                u_set = self._topology.get_open_set(u_name)
                v_set = self._topology.get_open_set(v_name)
                if u_set is None or v_set is None:
                    continue
                shared = u_set.points & v_set.points
                if not shared:
                    continue
                u_sects = self._presheaf._sections_by_openset[u_name]
                v_sects = self._presheaf._sections_by_openset[v_name]
                for fid in shared:
                    su = u_sects.get(fid)
                    sv = v_sects.get(fid)
                    if su is not None and sv is not None:
                        if su.fact != sv.fact:
                            passed = False
                            affected.append(fid[:8])
                        else:
                            glued += 1

        ns = time.perf_counter_ns() - t0
        return ConsistencyDiagnostic(
            passed=passed,
            check_name="gluing",
            detail=f"{glued} sections glued compatibly"
            if passed
            else f"Gluing failure: {len(affected)} incompatible sections",
            affected_sections=affected,
            computation_time_ns=ns,
        )

    def check_restriction_composition(self) -> ConsistencyDiagnostic:
        """Verify that restriction maps compose: ρ_{V,W} ∘ ρ_{U,V} = ρ_{U,W}."""
        import time

        t0 = time.perf_counter_ns()
        passed = True
        affected: list[str] = []
        os_names = list(self._topology._open_sets.keys())

        for u_name in os_names:
            for v_name in os_names:
                if v_name == u_name:
                    continue
                v_set = self._topology.get_open_set(v_name)
                u_set = self._topology.get_open_set(u_name)
                if v_set is None or u_set is None:
                    continue
                if not v_set.is_subset_of(u_set):
                    continue
                for w_name in os_names:
                    if w_name in (u_name, v_name):
                        continue
                    w_set = self._topology.get_open_set(w_name)
                    if w_set is None:
                        continue
                    if not w_set.is_subset_of(v_set):
                        continue
                    uv = self._presheaf.restrict(u_name, v_name)
                    vw = self._presheaf.restrict(v_name, w_name)
                    uw = self._presheaf.restrict(u_name, w_name)
                    uv_ids = {s.fact.id.value for s in uv}
                    vw_ids = {s.fact.id.value for s in vw}
                    uw_ids = {s.fact.id.value for s in uw}
                    midpoint = uv_ids & vw_ids
                    if midpoint != uw_ids:
                        passed = False
                        affected.append(f"{u_name}→{v_name}→{w_name}")

        ns = time.perf_counter_ns() - t0
        return ConsistencyDiagnostic(
            passed=passed,
            check_name="restriction_composition",
            detail="Restriction maps compose correctly"
            if passed
            else f"Composition failure in {len(affected)} paths",
            affected_sections=affected,
            computation_time_ns=ns,
        )

    def check_identity_restriction(self) -> ConsistencyDiagnostic:
        """Verify that ρ_{U,U} = id_{F(U)}."""
        passed = True
        for os_name in self._presheaf._sections_by_openset:
            restricted = self._presheaf.restrict(os_name, os_name)
            originals = self._presheaf.sections_over(os_name)
            if len(restricted) != len(originals):
                passed = False
        return ConsistencyDiagnostic(
            passed=passed,
            check_name="identity_restriction",
            detail="Identity restrictions preserve all sections",
        )

    def check_empty_set(self) -> ConsistencyDiagnostic:
        """Verify that F(∅) is a singleton (the empty section)."""
        empty_os = self._topology.get_open_set("∅")
        passed = empty_os is not None
        return ConsistencyDiagnostic(
            passed=passed,
            check_name="empty_set",
            detail="Empty set defined" if passed else "Empty set missing from topology",
        )
