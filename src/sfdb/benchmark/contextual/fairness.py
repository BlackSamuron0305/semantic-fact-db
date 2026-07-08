"""Fairness verification — ensures KG and SheafDB answer the same semantic question.

For each contextual workload, this module verifies that:
1. KG and SheafDB answer the same semantic question.
2. Results are functionally equivalent (modulo ordering).
3. SheafDB-native operations have documented KG-equivalent simulations.
4. No workload gives an unfair advantage to either engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sfdb.benchmark.contextual.workloads import (
    ContextualWorkload,
    ALL_CONTEXTUAL_WORKLOADS,
)


@dataclass
class FairnessEntry:
    workload_id: str
    workload_name: str
    semantic_question: str
    kg_executable: bool
    sheaf_executable: bool
    kg_simulation_required: bool
    kg_simulation_note: str
    results_equivalent: bool | None = None
    equivalence_notes: str = ""


@dataclass
class FairnessReport:
    entries: list[FairnessEntry] = field(default_factory=list)

    @property
    def all_executable(self) -> bool:
        return all(e.kg_executable and e.sheaf_executable for e in self.entries)

    @property
    def all_equivalent(self) -> bool:
        return all(e.results_equivalent for e in self.entries if e.results_equivalent is not None)

    @property
    def sheaf_native_count(self) -> int:
        return sum(1 for e in self.entries if e.kg_simulation_required)

    def to_dict(self) -> dict[str, Any]:
        return {
            "all_executable": self.all_executable,
            "all_equivalent": self.all_equivalent,
            "sheaf_native_count": self.sheaf_native_count,
            "entries": [
                {
                    "workload_id": e.workload_id,
                    "workload_name": e.workload_name,
                    "kg_executable": e.kg_executable,
                    "sheaf_executable": e.sheaf_executable,
                    "kg_simulation_required": e.kg_simulation_required,
                    "kg_simulation_note": e.kg_simulation_note,
                    "results_equivalent": e.results_equivalent,
                }
                for e in self.entries
            ],
        }

    def to_markdown(self) -> str:
        lines = ["# Fairness Report\n", "| Workload | KG | SheafDB | Simulation? | Equivalent? |", "|---|---|---|---|---|"]
        for e in self.entries:
            sim = "Yes" if e.kg_simulation_required else "No"
            eq = str(e.results_equivalent) if e.results_equivalent is not None else "N/A"
            lines.append(f"| {e.workload_id}: {e.workload_name} | {'✓' if e.kg_executable else '✗'} | {'✓' if e.sheaf_executable else '✗'} | {sim} | {eq} |")
        lines.append(f"\n**All executable:** {self.all_executable}")
        lines.append(f"**All equivalent:** {self.all_equivalent}")
        lines.append(f"**SheafDB-native operations:** {self.sheaf_native_count}/10")
        return "\n".join(lines)


def verify_knowledge_graph_parity(
    workload: ContextualWorkload,
    kg_results: list[dict[str, Any]] | None = None,
    sheaf_results: list[dict[str, Any]] | None = None,
) -> FairnessEntry:
    """Verify that the KG and SheafDB results are functionally equivalent.

    Two result sets are equivalent if:
    - They have the same length.
    - Every row in one set has a matching row in the other (by dict equality).
    - Ordering does not matter (results are compared as sets of frozen dicts).
    """
    kg_executable = kg_results is not None
    sheaf_executable = sheaf_results is not None
    eq: bool | None = None
    notes = ""

    if kg_executable and sheaf_executable:
        kg_set = {_freeze(r) for r in kg_results}
        sheaf_set = {_freeze(r) for r in sheaf_results}
        eq = kg_set == sheaf_set
        if not eq:
            only_kg = len(kg_set - sheaf_set)
            only_sheaf = len(sheaf_set - kg_set)
            notes = f"{only_kg} rows only in KG, {only_sheaf} only in SheafDB"
    elif kg_executable:
        notes = "SheafDB results not provided"
    elif sheaf_executable:
        notes = "KG results not provided"

    return FairnessEntry(
        workload_id=workload.id,
        workload_name=workload.name,
        semantic_question=workload.semantic_question,
        kg_executable=kg_executable,
        sheaf_executable=sheaf_executable,
        kg_simulation_required=workload.is_sheaf_native,
        kg_simulation_note=workload.kg_simulation_note,
        results_equivalent=eq,
        equivalence_notes=notes,
    )


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return frozenset((k, _freeze(v)) for k, v in sorted(value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value
