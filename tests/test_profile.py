from __future__ import annotations

import asyncio
import json
import sys
from io import StringIO

import pytest

from src import profile
from src.core.registry import profile_registry


# ---------------------------------------------------------------------------
# Isolation
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_profile_registry():
    profile_registry.reset()
    yield
    profile_registry.reset()


# ---------------------------------------------------------------------------
# Basic correctness
# ---------------------------------------------------------------------------


def test_return_value_preserved():
    @profile(label="p.return")
    def add(a: int, b: int) -> int:
        return a + b

    assert add(3, 4) == 7


def test_snapshot_recorded_after_call():
    @profile(label="p.snapshot")
    def fn() -> None:
        pass

    fn()
    stats = profile_registry.get_or_create("p.snapshot")
    assert stats.calls == 1
    assert stats.last is not None
    assert stats.last.duration_ns > 0


def test_bare_decorator():
    @profile
    def bare() -> None:
        pass

    bare()
    assert bare.stats().calls == 1


def test_label_overrides_qualname():
    @profile(label="custom.profile")
    def fn() -> None:
        pass

    fn()
    assert profile_registry.get_or_create("custom.profile").calls == 1


# ---------------------------------------------------------------------------
# Snapshot fields
# ---------------------------------------------------------------------------


def test_snapshot_has_cpu_time():
    @profile(label="p.cpu")
    def fn() -> None:
        x = sum(range(10_000))
        _ = x

    fn()
    snapshot = profile_registry.get_or_create("p.cpu").last
    assert snapshot is not None
    assert snapshot.cpu_ns >= 0


def test_snapshot_has_memory_fields():
    @profile(label="p.mem")
    def fn() -> None:
        pass

    fn()
    snapshot = profile_registry.get_or_create("p.mem").last
    assert snapshot is not None
    assert snapshot.memory_before_bytes >= 0
    assert snapshot.memory_after_bytes >= 0
    assert snapshot.memory_peak_bytes >= 0


def test_memory_delta_property():
    @profile(label="p.memdelta")
    def fn() -> None:
        pass

    fn()
    snapshot = profile_registry.get_or_create("p.memdelta").last
    assert snapshot is not None
    assert snapshot.memory_delta_bytes == (
        snapshot.memory_after_bytes - snapshot.memory_before_bytes
    )


def test_snapshot_captures_allocation():
    @profile(label="p.alloc")
    def allocate() -> list:
        return list(range(10_000))

    allocate()
    snapshot = profile_registry.get_or_create("p.alloc").last
    assert snapshot is not None
    assert snapshot.memory_peak_bytes > 0


def test_snapshot_has_thread_counts():
    @profile(label="p.threads")
    def fn() -> None:
        pass

    fn()
    snapshot = profile_registry.get_or_create("p.threads").last
    assert snapshot is not None
    assert snapshot.threads_before >= 1
    assert snapshot.threads_after >= 1


# ---------------------------------------------------------------------------
# Accumulation
# ---------------------------------------------------------------------------


def test_calls_accumulate():
    @profile(label="p.accum")
    def fn() -> None:
        pass

    for _ in range(4):
        fn()

    stats = profile_registry.get_or_create("p.accum")
    assert stats.calls == 4
    assert len(stats.snapshots) == 4


def test_avg_duration_available_after_multiple_calls():
    @profile(label="p.avg")
    def fn() -> None:
        pass

    fn()
    fn()
    stats = profile_registry.get_or_create("p.avg")
    assert stats.avg_duration_ns is not None
    assert stats.avg_cpu_ns is not None
    assert stats.avg_memory_delta_bytes is not None


# ---------------------------------------------------------------------------
# Accessor methods
# ---------------------------------------------------------------------------


def test_stats_accessor():
    @profile(label="p.acc")
    def fn() -> None:
        pass

    fn()
    fn()
    assert fn.stats().calls == 2


def test_reset_accessor():
    @profile(label="p.res")
    def fn() -> None:
        pass

    fn()
    fn.reset()
    assert fn.stats().calls == 0


# ---------------------------------------------------------------------------
# Exception transparency
# ---------------------------------------------------------------------------


def test_exception_is_reraised():
    @profile(label="p.exc")
    def boom() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        boom()


def test_stats_recorded_on_exception():
    @profile(label="p.exc_stats")
    def boom() -> None:
        raise RuntimeError

    with pytest.raises(RuntimeError):
        boom()

    assert profile_registry.get_or_create("p.exc_stats").calls == 1


# ---------------------------------------------------------------------------
# Render modes
# ---------------------------------------------------------------------------


def test_simple_mode():
    @profile(mode="simple", label="p.simple")
    def fn() -> None:
        pass

    fn()


def test_simple_mode_multi_call():
    @profile(mode="simple", label="p.simple_multi")
    def fn() -> None:
        pass

    fn()
    fn()


def test_json_mode_output():
    buf = StringIO()
    old_stderr, sys.stderr = sys.stderr, buf

    try:
        @profile(mode="json", label="p.json")
        def fn() -> None:
            pass

        fn()
    finally:
        sys.stderr = old_stderr

    data = json.loads(buf.getvalue().strip())
    assert data["name"] == "p.json"
    assert data["calls"] == 1
    assert "duration_ms" in data
    assert "cpu_ms" in data
    assert "memory_delta_bytes" in data
    assert "memory_peak_bytes" in data
    assert "threads_before" in data
    assert "threads_after" in data


def test_json_mode_multi_call_includes_avgs():
    buf = StringIO()

    @profile(mode="json", label="p.json_multi")
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
    assert "avg_duration_ms" in data
    assert "avg_cpu_ms" in data


# ---------------------------------------------------------------------------
# Async support
# ---------------------------------------------------------------------------


async def test_async_return_value():
    @profile(label="p.async")
    async def fetch() -> int:
        await asyncio.sleep(0)
        return 99

    assert await fetch() == 99


async def test_async_stats_recorded():
    @profile(label="p.async_stats")
    async def fn() -> None:
        await asyncio.sleep(0)

    await fn()
    assert profile_registry.get_or_create("p.async_stats").calls == 1


async def test_async_exception_reraises_and_records():
    @profile(label="p.async_exc")
    async def boom() -> None:
        raise ValueError("async boom")

    with pytest.raises(ValueError, match="async boom"):
        await boom()

    assert profile_registry.get_or_create("p.async_exc").calls == 1


# ---------------------------------------------------------------------------
# functools.wraps preservation
# ---------------------------------------------------------------------------


def test_wraps_preserves_name():
    @profile(label="p.wraps")
    def documented() -> None:
        """Important function."""

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Important function."


# ---------------------------------------------------------------------------
# Renderer helpers (_fmt_bytes, _fmt_bytes_delta)
# ---------------------------------------------------------------------------


def test_fmt_bytes_b():
    from src.core.renderer import _fmt_bytes
    assert _fmt_bytes(512) == "512 B"


def test_fmt_bytes_kb():
    from src.core.renderer import _fmt_bytes
    assert "KB" in _fmt_bytes(2048)


def test_fmt_bytes_mb():
    from src.core.renderer import _fmt_bytes
    assert "MB" in _fmt_bytes(2 * 1024 ** 2)


def test_fmt_bytes_delta_positive():
    from src.core.renderer import _fmt_bytes_delta
    assert _fmt_bytes_delta(1024).startswith("+")


def test_fmt_bytes_delta_negative():
    from src.core.renderer import _fmt_bytes_delta
    assert _fmt_bytes_delta(-1024).startswith("-")
