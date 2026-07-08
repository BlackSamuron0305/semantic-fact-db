"""Optimization framework — management, ablation, sensitivity, scalability.

Architecture
------------
OptimizationManager
    Orchestrates all optimizations.  Loads profiles, resolves modules,
    exposes enable/disable for benchmarking.

OptimizationRegistry
    Central registry of all known optimization modules.  Each module
    declares its name, description, engine affinity (sheaf/kg/general),
    default on/off, and a list of dependencies.

OptimizationProfile
    Named configuration preset (Minimal, Default, Research, Max,
    Memory, Debug).  Each profile specifies which optimizations to
    enable and with what parameters.

OptimizationReport
    Generates human-readable and machine-parsable reports about which
    optimizations are active, their hit rates, memory usage, and the
    resulting performance characteristics.

AblationStudy
    Runs automatic ablation by enabling/disabling optimisations in
    all 2^N combinations (or pairwise/random subsets for large N).

SensitivityAnalysis
    Sweeps a parameter across a range and measures the effect on
    latency, memory, and throughput.

ScalabilityAnalysis
    Measures performance across 9 scaling dimensions (facts, entities,
    relations, open sets, contexts, points per set, attributes, queries,
    concurrency).

MemoryAnalysis
    Deep memory profiling — object counting, per-cache RSS breakdown,
    cross-engine comparison.

HotspotAnalysis
    Profiles execution to identify hotspots using the existing Profiler
    and MeasuredRun infrastructure.

PerformanceDashboard
    Generates HTML/CSV/JSON reports combining all analyses.
"""

from __future__ import annotations

from .registry import OptimizationRegistry
from .manager import OptimizationManager
from .profile import OptimizationProfile, ProfileManager
from .report import OptimizationReport
from .ablation import AblationStudy, AblationResult
from .sensitivity import SensitivityAnalysis, SensitivityResult
from .scalability import ScalabilityAnalysis, ScalabilityResult
from .memory import MemoryAnalysis, MemoryReport
from .hotspot import HotspotAnalysis, HotspotReport
from .dashboard import PerformanceDashboard

__all__ = [
    "OptimizationRegistry",
    "OptimizationManager",
    "OptimizationProfile",
    "ProfileManager",
    "OptimizationReport",
    "AblationStudy",
    "AblationResult",
    "SensitivityAnalysis",
    "SensitivityResult",
    "ScalabilityAnalysis",
    "ScalabilityResult",
    "MemoryAnalysis",
    "MemoryReport",
    "HotspotAnalysis",
    "HotspotReport",
    "PerformanceDashboard",
]
