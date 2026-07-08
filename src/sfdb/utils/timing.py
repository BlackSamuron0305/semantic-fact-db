"""Timing utilities for performance measurement.

Provides a context manager and decorator for nanosecond-precision
timing of code blocks.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class Timer:
    """A context manager for measuring execution time.

    Usage:
        with Timer() as t:
            do_something()
        print(t.elapsed_ns)

    Complexity: O(1) overhead per measurement.
    """

    def __init__(self) -> None:
        self._start: int = 0
        self._end: int = 0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter_ns()
        return self

    def __exit__(self, *args: Any) -> None:
        self._end = time.perf_counter_ns()

    @property
    def elapsed_ns(self) -> int:
        return self._end - self._start

    @property
    def elapsed_ms(self) -> float:
        return self.elapsed_ns / 1e6

    @property
    def elapsed_s(self) -> float:
        return self.elapsed_ns / 1e9


def timed(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that logs the execution time of a function.

    Usage:
        @timed
        def my_function():
            ...
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with Timer() as t:
            result = func(*args, **kwargs)
        logger.debug(
            "%s took %.2f ms",
            func.__name__,
            t.elapsed_ms,
        )
        return result

    return wrapper
