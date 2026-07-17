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
    """Check that every engine's result set is equal as a *set* of rows.

    Rows are compared order-independently and without lossy stringification:
    a set of frozen (type-preserving) rows, not a positional zip of
    str()-cast tuples, so re-ordered-but-identical results correctly pass
    and type differences (e.g. 1 vs "1") correctly fail.
    """
    if len(results) < 2:
        return VerificationResult(True, "Single engine — no comparison needed")

    engine_names = list(results.keys())
    baseline_name = engine_names[0]
    baseline = _freeze_rows(results[baseline_name])

    for name in engine_names[1:]:
        other = _freeze_rows(results[name])

        if baseline != other:
            only_baseline = len(baseline - other)
            only_other = len(other - baseline)
            return VerificationResult(
                False,
                f"{baseline_name} vs {name} differ: "
                f"{only_baseline} rows only in {baseline_name}, {only_other} only in {name}",
            )

    return VerificationResult(True, f"All {len(results)} engines produce identical results")


def _freeze_rows(rows: list[dict[str, Any]]) -> frozenset[Any]:
    return frozenset(_freeze(r) for r in rows)


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return frozenset((k, _freeze(v)) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value
