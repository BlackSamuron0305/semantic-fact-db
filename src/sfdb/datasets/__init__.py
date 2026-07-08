"""Datasets for benchmarking and testing.

Provides synthetic and real-world datasets that can be loaded into
both KG and Sheaf representations.

Every dataset provides:
    1. A list of Fact objects (the data).
    2. A list of Query objects (the workload).
    3. Metadata (size, arity distribution, etc).

Datasets are the common ground for fair comparison.
"""

from sfdb.datasets.loaders import (
    load_dataset,
)
from sfdb.datasets.synthetic import (
    SyntheticConfig,
    SyntheticDataset,
    generate_facts,
    generate_random_graph,
)

__all__ = [
    "SyntheticConfig",
    "SyntheticDataset",
    "generate_facts",
    "generate_random_graph",
    "load_dataset",
]
