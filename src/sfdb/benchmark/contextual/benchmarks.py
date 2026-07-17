"""Contextual benchmark implementations — T3 through T10.

NOT the paper's benchmark suite. For every workload defined here, the
"_sheaf" function is a literal alias of the "_kg" function operating on a
plain in-memory list of facts — neither touches a real KnowledgeGraphEngine
or SheafDatabaseEngine, so no latency difference measured through this
module reflects anything about the two engines. This module is not called
by `sfdb benchmark` or by any script under scripts/. The paper's numbers
come exclusively from sfdb.benchmark.paper_suite (see that module and
paper/sections/evaluation.tex).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable

from sfdb.benchmark.contextual.generator import ContextualConfig, ContextualDataset
from sfdb.benchmark.contextual.metrics import ContextualMetrics, collect_contextual_metrics
from sfdb.benchmark.contextual.workloads import C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, ContextualWorkload
from sfdb.common.types import Context, Fact


@dataclass
class ContextualBenchResult:
    workload_id: str
    engine: str
    metrics: ContextualMetrics
    raw_results: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


@dataclass
class ContextualBenchmark:
    workload: ContextualWorkload
    dataset: ContextualDataset
    kg_fn: Callable[[Any], list[dict[str, Any]]] | None = None
    sheaf_fn: Callable[[Any], list[dict[str, Any]]] | None = None
    params: dict[str, Any] = field(default_factory=dict)

    def run_kg(self) -> ContextualBenchResult:
        if self.kg_fn is None:
            return ContextualBenchResult(
                workload_id=self.workload.id,
                engine="KnowledgeGraph",
                metrics=ContextualMetrics(),
                error="KG implementation not provided",
            )
        try:
            m = collect_contextual_metrics(self.kg_fn, self.params)
            r = self.kg_fn(self.params) if callable(self.kg_fn) else []
            return ContextualBenchResult(
                workload_id=self.workload.id,
                engine="KnowledgeGraph",
                metrics=m,
                raw_results=r,
            )
        except Exception as e:
            return ContextualBenchResult(
                workload_id=self.workload.id,
                engine="KnowledgeGraph",
                metrics=ContextualMetrics(),
                error=str(e),
            )

    def run_sheaf(self) -> ContextualBenchResult:
        if self.sheaf_fn is None:
            return ContextualBenchResult(
                workload_id=self.workload.id,
                engine="SheafDatabase",
                metrics=ContextualMetrics(),
                error="SheafDB implementation not provided",
            )
        try:
            m = collect_contextual_metrics(self.sheaf_fn, self.params)
            r = self.sheaf_fn(self.params) if callable(self.sheaf_fn) else []
            return ContextualBenchResult(
                workload_id=self.workload.id,
                engine="SheafDatabase",
                metrics=m,
                raw_results=r,
            )
        except Exception as e:
            return ContextualBenchResult(
                workload_id=self.workload.id,
                engine="SheafDatabase",
                metrics=ContextualMetrics(),
                error=str(e),
            )


def _first_obj(f: Fact) -> str:
    return f.objects[0] if f.objects else ""


def _neighborhood_kg(params: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[Fact] = params.get("facts", [])
    radius = params.get("radius", 1)
    seeds = params.get("seeds", [])
    results: list[dict[str, Any]] = []
    for seed in seeds:
        visited: set[str] = set()
        frontier = {seed.subject, _first_obj(seed)}
        for hop in range(radius):
            next_frontier: set[str] = set()
            for f in facts:
                obj = _first_obj(f)
                if f.subject in frontier or obj in frontier:
                    if f.id not in visited:
                        visited.add(f.id)
                        results.append({
                            "fact_id": f.id,
                            "subject": f.subject,
                            "relation": f.relation,
                            "object": obj,
                            "distance": hop + 1,
                        })
                        next_frontier.add(f.subject)
                        next_frontier.add(obj)
            frontier = next_frontier
    return results


def _neighborhood_sheaf(params: dict[str, Any]) -> list[dict[str, Any]]:
    return _neighborhood_kg(params)


def _high_arity_lookup_kg(params: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[Fact] = params.get("facts", [])
    target_rel = params.get("relation", "")
    match_args = params.get("match_args", {})
    results: list[dict[str, Any]] = []
    for f in facts:
        if f.relation != target_rel:
            continue
        if not f.objects:
            continue
        vals = f.objects
        ok = True
        for pos, val in match_args.items():
            if pos >= len(vals) or vals[pos] != val:
                ok = False
                break
        if ok:
            results.append({"fact_id": f.id, **{f"arg_{i}": v for i, v in enumerate(vals)}})
    return results


def _high_arity_lookup_sheaf(params: dict[str, Any]) -> list[dict[str, Any]]:
    return _high_arity_lookup_kg(params)


def _high_arity_join_kg(params: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[Fact] = params.get("facts", [])
    rel1 = params.get("rel1", "")
    rel2 = params.get("rel2", "")
    join_pairs: list[tuple[int, int]] = params.get("join_pairs", [])
    f1s = [f for f in facts if f.relation == rel1 and f.objects]
    f2s = [f for f in facts if f.relation == rel2 and f.objects]
    results: list[dict[str, Any]] = []
    for f1 in f1s:
        for f2 in f2s:
            match = True
            for p1, p2 in join_pairs:
                v1 = f1.objects[p1] if p1 < len(f1.objects) else None
                v2 = f2.objects[p2] if p2 < len(f2.objects) else None
                if v1 != v2:
                    match = False
                    break
            if match:
                results.append({"f1_id": f1.id, "f2_id": f2.id})
    return results


def _high_arity_join_sheaf(params: dict[str, Any]) -> list[dict[str, Any]]:
    return _high_arity_join_kg(params)


def _temporal_interval_kg(params: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[Fact] = params.get("facts", [])
    q_start = params.get("q_start", 0)
    q_end = params.get("q_end", 100)
    results: list[dict[str, Any]] = []
    for f in facts:
        md = f.metadata
        fs, fe = md.get("start", 0), md.get("end", 0)
        if fs < q_end and fe > q_start:
            overlap = min(fe, q_end) - max(fs, q_start)
            results.append({
                "fact_id": f.id,
                "start": fs, "end": fe,
                "overlap": max(0, overlap),
            })
    return results


def _temporal_interval_sheaf(params: dict[str, Any]) -> list[dict[str, Any]]:
    return _temporal_interval_kg(params)


def _temporal_agg_kg(params: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[Fact] = params.get("facts", [])
    window_size = params.get("window_size", 100)
    num_windows = params.get("num_windows", 10)
    time_start = params.get("time_start", 0)
    results: list[dict[str, Any]] = []
    for w in range(num_windows):
        ws = time_start + w * window_size
        we = ws + window_size
        active = [f for f in facts
                  if f.metadata.get("start", 0) < we
                  and f.metadata.get("end", 0) > ws]
        vals = [f.metadata.get("attr", 0) for f in active]
        results.append({
            "window_id": w,
            "window_start": ws,
            "window_end": we,
            "fact_count": len(active),
            "avg_value": sum(vals) / len(vals) if vals else 0.0,
        })
    return results


def _temporal_agg_sheaf(params: dict[str, Any]) -> list[dict[str, Any]]:
    return _temporal_agg_kg(params)


def _provenance_chain_kg(params: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[Fact] = params.get("facts", [])
    derived_ids: list[str] = params.get("derived_ids", [])
    fact_map = {f.id: f for f in facts}
    results: list[dict[str, Any]] = []
    for did in derived_ids:
        current = did
        depth = 0
        while current in fact_map:
            f = fact_map[current]
            parents = f.metadata.get("parents", [])
            results.append({
                "step": depth,
                "fact_id": f.id,
                "source_ids": parents,
                "transformation": f.metadata.get("transformation", ""),
                "confidence": f.metadata.get("confidence", 1.0),
            })
            if parents:
                current = parents[0]
                depth += 1
            else:
                break
    return results


def _provenance_chain_sheaf(params: dict[str, Any]) -> list[dict[str, Any]]:
    return _provenance_chain_kg(params)


def _consistency_check_kg(params: dict[str, Any]) -> list[dict[str, Any]]:
    contexts: dict[str, list[tuple[str, str]]] = params.get("contexts", {})
    overlap_map: dict[str, set[str]] = {}
    for ctx, assigns in contexts.items():
        for entity, val in assigns:
            overlap_map.setdefault(entity, set()).add(val)
    conflicts_found = any(len(v) > 1 for v in overlap_map.values())
    return [{
        "is_consistent": not conflicts_found,
        "num_contexts": len(contexts),
        "assignment_count": sum(len(v) for v in contexts.values()),
        "max_overlap": max((len(v) for v in overlap_map.values()), default=0),
    }]


def _consistency_check_sheaf(params: dict[str, Any]) -> list[dict[str, Any]]:
    return _consistency_check_kg(params)


def _global_section_kg(params: dict[str, Any]) -> list[dict[str, Any]]:
    contexts: dict[str, dict[str, str]] = params.get("local_sections", {})
    all_entities: set[str] = set()
    for ctx_section in contexts.values():
        all_entities.update(ctx_section.keys())
    conflicts: list[Any] = []
    built: dict[str, str] = {}
    for entity in all_entities:
        seen: set[str] = set()
        for _ctx, section in contexts.items():
            if entity in section:
                seen.add(section[entity])
        if len(seen) == 1:
            built[entity] = next(iter(seen))
        elif len(seen) > 1:
            conflicts.append((entity, list(seen)))
    return [{
        "has_global": len(conflicts) == 0,
        "num_assignments": len(built),
        "conflicts": [(str(c[0]), str(c[1])) for c in conflicts],
        "built_section": built,
    }]


def _global_section_sheaf(params: dict[str, Any]) -> list[dict[str, Any]]:
    return _global_section_kg(params)


def _lineage_kg(params: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[Fact] = params.get("facts", [])
    target_id = params.get("target_id", "")
    fact_map = {f.id: f for f in facts}
    results: list[dict[str, Any]] = []
    visited: set[str] = set()
    stack = [(target_id, 0)]
    while stack:
        fid, depth = stack.pop()
        if fid in visited:
            continue
        visited.add(fid)
        f = fact_map.get(fid)
        if f is None:
            continue
        parents = f.metadata.get("parents", [])
        results.append({
            "fact_id": fid,
            "depth": depth,
            "parent_ids": parents,
        })
        for p in parents:
            if p not in visited:
                stack.append((p, depth + 1))
    return results


def _lineage_sheaf(params: dict[str, Any]) -> list[dict[str, Any]]:
    return _lineage_kg(params)


def _mixed_flagship_kg(params: dict[str, Any]) -> list[dict[str, Any]]:
    step1 = _neighborhood_kg(params)
    temp_params = dict(params)
    temp_params["facts"] = [f for f in params.get("facts", [])
                            if any(r["fact_id"] == f.id for r in step1)]
    step2 = _temporal_interval_kg(temp_params)
    remaining_ids = {r["fact_id"] for r in step2}
    prov_params = dict(params)
    prov_params["derived_ids"] = list(remaining_ids)
    step3 = _provenance_chain_kg(prov_params)
    return [{
        "seed_id": params.get("seed_id", ""),
        "neighbor_count": len(step1),
        "temporal_filtered": len(step2),
        "provenance_chains": len(step3),
        "is_consistent": True,
        "total_steps": len(step1) + len(step2) + len(step3),
    }]


def _mixed_flagship_sheaf(params: dict[str, Any]) -> list[dict[str, Any]]:
    return _mixed_flagship_kg(params)


def benchmark_event_reconstruction(dataset: ContextualDataset, **kwargs) -> ContextualBenchmark:
    params = {
        "radius": kwargs.get("radius", 2),
        "facts": dataset.contextual_facts,
        "seeds": dataset.contextual_facts[: kwargs.get("num_seeds", 5)],
    }
    return ContextualBenchmark(
        workload=C1,
        dataset=dataset,
        kg_fn=_neighborhood_kg,
        sheaf_fn=_neighborhood_sheaf,
        params=params,
    )


def benchmark_provenance(dataset: ContextualDataset, **kwargs) -> ContextualBenchmark:
    prov_facts = dataset.provenance_facts
    derived = [f for f in prov_facts if "depth" in f.metadata]
    params = {
        "facts": prov_facts,
        "derived_ids": [f.id for f in derived[: kwargs.get("num_chains", 10)]],
    }
    return ContextualBenchmark(
        workload=C7,
        dataset=dataset,
        kg_fn=_provenance_chain_kg,
        sheaf_fn=_provenance_chain_sheaf,
        params=params,
    )


def benchmark_temporal(dataset: ContextualDataset, **kwargs) -> ContextualBenchmark:
    params = {
        "facts": dataset.temporal_facts,
        "q_start": kwargs.get("q_start", 10000),
        "q_end": kwargs.get("q_end", 20000),
        "window_size": kwargs.get("window_size", 1000),
        "num_windows": kwargs.get("num_windows", 10),
        "time_start": kwargs.get("time_start", 0),
    }
    return ContextualBenchmark(
        workload=C5,
        dataset=dataset,
        kg_fn=_temporal_interval_kg,
        sheaf_fn=_temporal_interval_sheaf,
        params=params,
    )


def benchmark_high_arity(dataset: ContextualDataset, **kwargs) -> ContextualBenchmark:
    high_facts = dataset.high_arity_facts
    target_rel = high_facts[0].relation if high_facts else "high_arity_r0"
    params = {
        "facts": high_facts,
        "relation": kwargs.get("relation", target_rel),
        "match_args": kwargs.get("match_args", {0: "v0"}),
    }
    return ContextualBenchmark(
        workload=C3,
        dataset=dataset,
        kg_fn=_high_arity_lookup_kg,
        sheaf_fn=_high_arity_lookup_sheaf,
        params=params,
    )


def benchmark_high_arity_join(dataset: ContextualDataset, **kwargs) -> ContextualBenchmark:
    high_facts = dataset.high_arity_facts
    rels = sorted(set(f.relation for f in high_facts))
    rel1 = rels[0] if len(rels) > 0 else "high_arity_r0"
    rel2 = rels[1] if len(rels) > 1 else "high_arity_r1"
    params = {
        "facts": high_facts,
        "rel1": kwargs.get("rel1", rel1),
        "rel2": kwargs.get("rel2", rel2),
        "join_pairs": kwargs.get("join_pairs", [(0, 0)]),
    }
    return ContextualBenchmark(
        workload=C4,
        dataset=dataset,
        kg_fn=_high_arity_join_kg,
        sheaf_fn=_high_arity_join_sheaf,
        params=params,
    )


def benchmark_temporal_aggregation(dataset: ContextualDataset, **kwargs) -> ContextualBenchmark:
    params = {
        "facts": dataset.temporal_facts,
        "window_size": kwargs.get("window_size", 1000),
        "num_windows": kwargs.get("num_windows", 10),
        "time_start": kwargs.get("time_start", 0),
    }
    return ContextualBenchmark(
        workload=C6,
        dataset=dataset,
        kg_fn=_temporal_agg_kg,
        sheaf_fn=_temporal_agg_sheaf,
        params=params,
    )


def benchmark_neighborhood(dataset: ContextualDataset, **kwargs) -> ContextualBenchmark:
    params = {
        "radius": kwargs.get("radius", 2),
        "facts": dataset.contextual_facts,
        "seeds": dataset.contextual_facts[: kwargs.get("num_seeds", 5)],
    }
    return ContextualBenchmark(
        workload=C2,
        dataset=dataset,
        kg_fn=_neighborhood_kg,
        sheaf_fn=_neighborhood_sheaf,
        params=params,
    )


def benchmark_consistency(dataset: ContextualDataset, **kwargs) -> ContextualBenchmark:
    contexts: dict[str, list[tuple[str, str]]] = {}
    for i, f in enumerate(dataset.facts[: kwargs.get("num_contexts", 10)]):
        ctx = f"ctx_{i}"
        obj = _first_obj(f)
        contexts[ctx] = [(f.subject, obj)]
    params = {"contexts": contexts}
    return ContextualBenchmark(
        workload=C8,
        dataset=dataset,
        kg_fn=_consistency_check_kg,
        sheaf_fn=_consistency_check_sheaf,
        params=params,
    )


def benchmark_global_section(dataset: ContextualDataset, **kwargs) -> ContextualBenchmark:
    local_sections: dict[str, dict[str, str]] = {}
    for i in range(kwargs.get("num_contexts", 5)):
        ctx = f"ctx_{i}"
        local_sections[ctx] = {
            f"e{r}": f"v{r}" for r in range(kwargs.get("context_size", 10))
        }
    params = {"local_sections": local_sections}
    return ContextualBenchmark(
        workload=C9,
        dataset=dataset,
        kg_fn=_global_section_kg,
        sheaf_fn=_global_section_sheaf,
        params=params,
    )


def benchmark_lineage(dataset: ContextualDataset, **kwargs) -> ContextualBenchmark:
    prov_facts = dataset.provenance_facts
    derived = [f for f in prov_facts if "depth" in f.metadata]
    target = derived[-1] if derived else prov_facts[0]
    params = {
        "facts": prov_facts,
        "target_id": target.id,
    }
    return ContextualBenchmark(
        workload=C7,
        dataset=dataset,
        kg_fn=_lineage_kg,
        sheaf_fn=_lineage_sheaf,
        params=params,
    )


def benchmark_mixed_workload(dataset: ContextualDataset, **kwargs) -> ContextualBenchmark:
    seed = dataset.contextual_facts[0] if dataset.contextual_facts else (
        dataset.temporal_facts[0] if dataset.temporal_facts else dataset.facts[0]
    )
    params = {
        "radius": kwargs.get("radius", 2),
        "facts": dataset.all_facts,
        "seeds": [seed],
        "q_start": kwargs.get("q_start", 0),
        "q_end": kwargs.get("q_end", 100000),
        "derived_ids": [f.id for f in dataset.provenance_facts
                        if "depth" in f.metadata][:5],
        "seed_id": seed.id,
    }
    return ContextualBenchmark(
        workload=C10,
        dataset=dataset,
        kg_fn=_mixed_flagship_kg,
        sheaf_fn=_mixed_flagship_sheaf,
        params=params,
    )
