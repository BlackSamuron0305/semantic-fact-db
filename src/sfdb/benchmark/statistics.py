"""Statistical analysis — mean, median, variance, percentiles, confidence intervals."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Statistics:
    mean: float = 0.0
    median: float = 0.0
    variance: float = 0.0
    std_dev: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    count: int = 0
    ci95_low: float = 0.0
    ci95_high: float = 0.0
    bootstrap_ci95_low: float = 0.0
    bootstrap_ci95_high: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "mean": self.mean,
            "median": self.median,
            "variance": self.variance,
            "std_dev": self.std_dev,
            "p50": self.p50,
            "p95": self.p95,
            "p99": self.p99,
            "min": self.min_val,
            "max": self.max_val,
            "count": self.count,
            "ci95_low": self.ci95_low,
            "ci95_high": self.ci95_high,
        }


def compute_statistics(values: list[float], bootstrap_samples: int = 10000) -> Statistics:
    if not values:
        return Statistics()

    n = len(values)
    s = sorted(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = math.sqrt(variance)

    def percentile(data: list[float], p: float) -> float:
        idx = max(0, min(len(data) - 1, int(len(data) * p / 100)))
        return data[idx]

    median = percentile(s, 50)
    p50 = percentile(s, 50)
    p95 = percentile(s, 95)
    p99 = percentile(s, 99)

    se = std_dev / math.sqrt(n)
    ci95_low = mean - 1.96 * se
    ci95_high = mean + 1.96 * se

    rng = random.Random(42)
    boot_means: list[float] = []
    for _ in range(bootstrap_samples):
        sample = [rng.choice(values) for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    bi = int(bootstrap_samples * 0.025)
    bootstrap_ci95_low = boot_means[bi]
    bootstrap_ci95_high = boot_means[bootstrap_samples - bi - 1]

    return Statistics(
        mean=mean,
        median=median,
        variance=variance,
        std_dev=std_dev,
        p50=p50,
        p95=p95,
        p99=p99,
        min_val=s[0],
        max_val=s[-1],
        count=n,
        ci95_low=ci95_low,
        ci95_high=ci95_high,
        bootstrap_ci95_low=bootstrap_ci95_low,
        bootstrap_ci95_high=bootstrap_ci95_high,
    )


def speedup_ratio(baseline: float, comparison: float) -> float:
    if comparison == 0:
        return float("inf")
    return baseline / comparison
