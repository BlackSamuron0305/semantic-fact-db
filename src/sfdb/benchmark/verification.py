"""Result verification — ensures all engines produce identical canonical results."""

from __future__ import annotations

from typing import Any


class VerificationError(Exception):
    pass


class VerificationResult:
    def __init__(self, passed: bool = True, message: str = "") -> None:
        self.passed = passed
        self.message = message

    def __bool__(self) -> bool:
        return self.passed


def verify_equivalence(results: dict[str, list[dict[str, Any]]]) -> VerificationResult:
    if len(results) < 2:
        return VerificationResult(True, "Single engine — no comparison needed")

    engine_names = list(results.keys())
    baseline_name = engine_names[0]
    baseline = _normalize_rows(results[baseline_name])

    for name in engine_names[1:]:
        other = _normalize_rows(results[name])

        if len(baseline) != len(other):
            return VerificationResult(
                False, f"Row count mismatch: {baseline_name}={len(baseline)}, {name}={len(other)}"
            )

        for i, (br, or_) in enumerate(zip(baseline, other, strict=False)):
            if br != or_:
                return VerificationResult(
                    False, f"Row {i} differs: {baseline_name}={br}, {name}={or_}"
                )

    return VerificationResult(True, f"All {len(results)} engines produce identical results")


def _normalize_rows(rows: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    if not rows:
        return []
    result: list[tuple[str, ...]] = []
    for r in rows:
        items = tuple(str(v) for v in r.values())
        result.append(items)
    return result
