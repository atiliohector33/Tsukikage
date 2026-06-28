from __future__ import annotations

import functools
import inspect
import threading
import time
import tracemalloc
from typing import Callable, TypeVar, overload

from ..core.models import ProfileSnapshot
from ..core.registry import profile_registry
from ..core.renderer import RenderMode, get_profile_renderer

F = TypeVar("F", bound=Callable[..., object])


def _start_tracing() -> None:
    if not tracemalloc.is_tracing():
        tracemalloc.start()


def _snapshot_before() -> tuple[int, int, int, int]:
    """Capture baseline metrics just before the call.

    Returns (wall_ns, cpu_ns, mem_before_bytes, threads_before).
    """
    _start_tracing()
    tracemalloc.reset_peak()
    mem_before = tracemalloc.get_traced_memory()[0]
    threads_before = threading.active_count()
    wall = time.perf_counter_ns()
    cpu = time.process_time_ns()
    return wall, cpu, mem_before, threads_before


def _snapshot_after(
    name: str,
    wall_start: int,
    cpu_start: int,
    mem_before: int,
    threads_before: int,
) -> ProfileSnapshot:
    """Capture metrics immediately after the call and build a ProfileSnapshot."""
    wall_end = time.perf_counter_ns()
    cpu_end = time.process_time_ns()
    mem_after, mem_peak = tracemalloc.get_traced_memory()
    threads_after = threading.active_count()

    return ProfileSnapshot(
        name=name,
        duration_ns=wall_end - wall_start,
        cpu_ns=cpu_end - cpu_start,
        memory_before_bytes=mem_before,
        memory_after_bytes=mem_after,
        memory_peak_bytes=mem_peak,
        threads_before=threads_before,
        threads_after=threads_after,
    )


@overload
def profile(func: F) -> F: ...


@overload
def profile(
    func: None = None,
    *,
    mode: RenderMode = "pretty",
    label: str | None = None,
) -> Callable[[F], F]: ...


def profile(
    func: F | None = None,
    *,
    mode: RenderMode = "pretty",
    label: str | None = None,
) -> F | Callable[[F], F]:
    """Measure time, CPU, memory, and thread count for a function.

    Works as a bare decorator (@profile) or with options (@profile(mode="json")).
    Snapshots accumulate across calls and are accessible via func.stats().

    Parameters:
        mode: Output format — "pretty" (rich panel), "simple" (plain), or "json".
        label: Display name. Defaults to "<module>.<qualname>".

    Note:
        Memory is measured via tracemalloc (Python-level allocations only).
        CPU time uses process_time_ns (user + kernel). In async contexts both
        metrics include other coroutines running concurrently on the event loop.
    """

    def decorator(fn: F) -> F:
        name = label or f"{fn.__module__}.{fn.__qualname__}"
        renderer = get_profile_renderer(mode)

        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: object, **kwargs: object) -> object:
                wall, cpu, mem_before, threads_before = _snapshot_before()
                try:
                    return await fn(*args, **kwargs)  # type: ignore[misc]
                finally:
                    snapshot = _snapshot_after(name, wall, cpu, mem_before, threads_before)
                    stats = profile_registry.get_or_create(name)
                    stats.record(snapshot)
                    renderer.render(stats, snapshot)

            async_wrapper.stats = lambda: profile_registry.get_or_create(name)  # type: ignore[attr-defined]
            async_wrapper.reset = lambda: profile_registry.reset(name)  # type: ignore[attr-defined]
            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def sync_wrapper(*args: object, **kwargs: object) -> object:
            wall, cpu, mem_before, threads_before = _snapshot_before()
            try:
                return fn(*args, **kwargs)
            finally:
                snapshot = _snapshot_after(name, wall, cpu, mem_before, threads_before)
                stats = profile_registry.get_or_create(name)
                stats.record(snapshot)
                renderer.render(stats, snapshot)

        sync_wrapper.stats = lambda: profile_registry.get_or_create(name)  # type: ignore[attr-defined]
        sync_wrapper.reset = lambda: profile_registry.reset(name)  # type: ignore[attr-defined]
        return sync_wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator
