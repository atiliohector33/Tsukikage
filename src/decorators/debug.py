from __future__ import annotations

import functools
import inspect
import time
from typing import Callable, TypeVar, overload

from ..core.models import DebugRecord
from ..core.renderer import RenderMode, get_debug_renderer

F = TypeVar("F", bound=Callable[..., object])


def _source_location(fn: Callable) -> tuple[str, int]:
    try:
        file = inspect.getfile(fn)
        _, line = inspect.getsourcelines(fn)
        return file, line
    except (TypeError, OSError):
        return "<unknown>", 0


def _truncate(s: str, max_length: int) -> str:
    return s if len(s) <= max_length else s[:max_length] + "…"


def _collect_args(
    fn: Callable,
    args: tuple,
    kwargs: dict,
    max_length: int,
) -> dict[str, str]:
    try:
        sig = inspect.signature(fn)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        return {k: _truncate(repr(v), max_length) for k, v in bound.arguments.items()}
    except TypeError:
        result: dict[str, str] = {}
        if args:
            result["*args"] = _truncate(repr(args), max_length)
        if kwargs:
            result["**kwargs"] = _truncate(repr(kwargs), max_length)
        return result


@overload
def debug(func: F) -> F: ...


@overload
def debug(
    func: None = None,
    *,
    mode: RenderMode = "pretty",
    label: str | None = None,
    max_length: int = 200,
) -> Callable[[F], F]: ...


def debug(
    func: F | None = None,
    *,
    mode: RenderMode = "pretty",
    label: str | None = None,
    max_length: int = 200,
) -> F | Callable[[F], F]:
    """Show arguments, return value, exceptions, source location, and duration.

    Designed for active development — outputs on every call.
    Works as a bare decorator (@debug) or with options (@debug(mode="json")).

    Parameters:
        mode: Output format — "pretty" (rich panel), "simple" (plain), or "json".
        label: Display name. Defaults to "<module>.<qualname>".
        max_length: Maximum repr length for arguments and return values.
    """

    def decorator(fn: F) -> F:
        name = label or f"{fn.__module__}.{fn.__qualname__}"
        file, line = _source_location(fn)
        renderer = get_debug_renderer(mode)

        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: object, **kwargs: object) -> object:
                args_repr = _collect_args(fn, args, kwargs, max_length)
                start = time.perf_counter_ns()
                exc_repr: str | None = None
                ret_repr: str | None = None
                try:
                    result = await fn(*args, **kwargs)  # type: ignore[misc]
                    ret_repr = _truncate(repr(result), max_length)
                    return result
                except Exception as exc:
                    exc_repr = f"{type(exc).__name__}: {exc}"
                    raise
                finally:
                    record = DebugRecord(
                        name=name,
                        file=file,
                        line=line,
                        args_repr=args_repr,
                        return_repr=ret_repr,
                        exception_repr=exc_repr,
                        duration_ns=time.perf_counter_ns() - start,
                    )
                    renderer.render(record)

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def sync_wrapper(*args: object, **kwargs: object) -> object:
            args_repr = _collect_args(fn, args, kwargs, max_length)
            start = time.perf_counter_ns()
            exc_repr: str | None = None
            ret_repr: str | None = None
            try:
                result = fn(*args, **kwargs)
                ret_repr = _truncate(repr(result), max_length)
                return result
            except Exception as exc:
                exc_repr = f"{type(exc).__name__}: {exc}"
                raise
            finally:
                record = DebugRecord(
                    name=name,
                    file=file,
                    line=line,
                    args_repr=args_repr,
                    return_repr=ret_repr,
                    exception_repr=exc_repr,
                    duration_ns=time.perf_counter_ns() - start,
                )
                renderer.render(record)

        return sync_wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator
