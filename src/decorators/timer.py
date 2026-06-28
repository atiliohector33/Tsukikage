from __future__ import annotations

import asyncio
import functools
import inspect
import time
from typing import Callable, TypeVar, overload

from ..core.registry import timer_registry
from ..core.renderer import RenderMode, get_renderer

F = TypeVar("F", bound=Callable[..., object])


@overload
def timer(func: F) -> F: ...


@overload
def timer(
    func: None = None,
    *,
    mode: RenderMode = "pretty",
    label: str | None = None,
) -> Callable[[F], F]: ...


def timer(
    func: F | None = None,
    *,
    mode: RenderMode = "pretty",
    label: str | None = None,
) -> F | Callable[[F], F]:
    """Measure and report the execution time of a function.

    Works as a bare decorator (@timer) or with options (@timer(mode="json")).
    Stats accumulate across calls and are accessible via func.stats().

    Parameters:
        mode: Output format — "pretty" (rich panel), "simple" (plain), or "json".
        label: Display name. Defaults to "<module>.<qualname>".
    """

    def decorator(fn: F) -> F:
        name = label or f"{fn.__module__}.{fn.__qualname__}"
        renderer = get_renderer(mode)

        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: object, **kwargs: object) -> object:
                start = time.perf_counter_ns()
                try:
                    return await fn(*args, **kwargs)  # type: ignore[misc]
                finally:
                    duration_ns = time.perf_counter_ns() - start
                    stats = timer_registry.get_or_create(name)
                    stats.record(duration_ns)
                    renderer.render(stats, duration_ns)

            async_wrapper.stats = lambda: timer_registry.get_or_create(name)  # type: ignore[attr-defined]
            async_wrapper.reset = lambda: timer_registry.reset(name)  # type: ignore[attr-defined]
            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def sync_wrapper(*args: object, **kwargs: object) -> object:
            start = time.perf_counter_ns()
            try:
                return fn(*args, **kwargs)
            finally:
                duration_ns = time.perf_counter_ns() - start
                stats = timer_registry.get_or_create(name)
                stats.record(duration_ns)
                renderer.render(stats, duration_ns)

        sync_wrapper.stats = lambda: timer_registry.get_or_create(name)  # type: ignore[attr-defined]
        sync_wrapper.reset = lambda: timer_registry.reset(name)  # type: ignore[attr-defined]
        return sync_wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator
