from __future__ import annotations

import asyncio
import json
import sys
import time
from io import StringIO

import pytest

from src import timer
from src.core.registry import timer_registry


def test_return_value_is_preserved():
    @timer(label="t.return")
    def add(a: int, b: int) -> int:
        return a + b

    assert add(2, 3) == 5


def test_stats_recorded_after_call():
    @timer(label="t.stats")
    def fn() -> None:
        pass

    fn()
    stats = timer_registry.get_or_create("t.stats")
    assert stats.calls == 1
    assert stats.total_ns > 0
    assert stats.min_ns is not None
    assert stats.max_ns is not None


def test_bare_decorator_uses_qualname():
    @timer
    def bare() -> None:
        pass

    bare()
    assert bare.stats().calls == 1


def test_label_overrides_qualname():
    @timer(label="custom.label")
    def fn() -> None:
        pass

    fn()
    assert timer_registry.get_or_create("custom.label").calls == 1


def test_stats_accumulate_across_calls():
    @timer(label="t.accum")
    def fn() -> None:
        pass

    for _ in range(5):
        fn()

    stats = timer_registry.get_or_create("t.accum")
    assert stats.calls == 5
    assert stats.min_ns <= stats.max_ns  # type: ignore[operator]
    assert stats.avg_ns is not None


def test_percentiles_available_after_two_calls():
    @timer(label="t.p2")
    def fn() -> None:
        pass

    fn()
    fn()
    stats = timer_registry.get_or_create("t.p2")
    assert stats.percentile(50) is not None
    assert stats.percentile(95) is not None


def test_percentile_none_on_single_call():
    @timer(label="t.p1")
    def fn() -> None:
        pass

    fn()
    assert timer_registry.get_or_create("t.p1").percentile(50) is None


def test_percentile_invalid_range():
    @timer(label="t.pbad")
    def fn() -> None:
        pass

    fn()
    fn()
    stats = timer_registry.get_or_create("t.pbad")
    assert stats.percentile(0) is None
    assert stats.percentile(100) is None


def test_stats_accessor():
    @timer(label="t.accessor")
    def fn() -> None:
        pass

    fn()
    fn()
    assert fn.stats().calls == 2


def test_reset_accessor():
    @timer(label="t.reset")
    def fn() -> None:
        pass

    fn()
    fn.reset()
    assert fn.stats().calls == 0


def test_exception_is_reraised():
    @timer(label="t.exc")
    def boom() -> None:
        raise ValueError("kaboom")

    with pytest.raises(ValueError, match="kaboom"):
        boom()


def test_stats_recorded_on_exception():
    @timer(label="t.exc_stats")
    def boom() -> None:
        raise RuntimeError

    with pytest.raises(RuntimeError):
        boom()

    assert timer_registry.get_or_create("t.exc_stats").calls == 1


def test_simple_mode():
    @timer(mode="simple", label="t.simple")
    def fn() -> None:
        pass

    fn()


def test_json_mode_output():
    buf = StringIO()
    old_stderr, sys.stderr = sys.stderr, buf

    try:
        @timer(mode="json", label="t.json")
        def fn() -> None:
            pass

        fn()
    finally:
        sys.stderr = old_stderr

    data = json.loads(buf.getvalue().strip())
    assert data["name"] == "t.json"
    assert data["calls"] == 1
    assert "duration_ms" in data


def test_json_mode_multi_call_includes_stats():
    buf = StringIO()

    @timer(mode="json", label="t.json_multi")
    def fn() -> None:
        pass

    fn()

    old_stderr, sys.stderr = sys.stderr, buf
    try:
        fn()
    finally:
        sys.stderr = old_stderr

    data = json.loads(buf.getvalue().strip())
    assert data["calls"] == 2
    assert "avg_ms" in data
    assert "min_ms" in data
    assert "max_ms" in data


async def test_async_return_value():
    @timer(label="t.async")
    async def fetch() -> int:
        await asyncio.sleep(0)
        return 42

    assert await fetch() == 42


async def test_async_stats_recorded():
    @timer(label="t.async_stats")
    async def fn() -> None:
        await asyncio.sleep(0)

    await fn()
    assert timer_registry.get_or_create("t.async_stats").calls == 1


async def test_async_exception_reraises_and_records():
    @timer(label="t.async_exc")
    async def boom() -> None:
        raise ValueError("async kaboom")

    with pytest.raises(ValueError, match="async kaboom"):
        await boom()

    assert timer_registry.get_or_create("t.async_exc").calls == 1


def test_wraps_preserves_name():
    @timer(label="t.wraps")
    def my_function() -> None:
        """Important docstring."""

    assert my_function.__name__ == "my_function"
    assert my_function.__doc__ == "Important docstring."


def test_simple_mode_multi_call():
    @timer(mode="simple", label="t.simple_multi")
    def fn() -> None:
        pass

    fn()
    fn()


def test_fmt_nanoseconds():
    from src.core.renderer import _fmt

    assert _fmt(500) == "500 ns"


def test_fmt_microseconds():
    from src.core.renderer import _fmt

    assert _fmt(1_500) == "1.500 µs"


def test_fmt_milliseconds():
    from src.core.renderer import _fmt

    assert _fmt(1_500_000) == "1.500 ms"


def test_fmt_seconds():
    from src.core.renderer import _fmt

    assert "s" in _fmt(2_000_000_000)


def test_registry_all():
    from src.core.registry import timer_registry

    @timer(label="t.all_a")
    def a() -> None:
        pass

    @timer(label="t.all_b")
    def b() -> None:
        pass

    a()
    b()
    all_stats = timer_registry.all
    assert "t.all_a" in all_stats
    assert "t.all_b" in all_stats
