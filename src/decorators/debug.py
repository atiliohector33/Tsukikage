from __future__ import annotations

import functools
import inspect
import logging
import time
from typing import Callable, TypeVar, overload

from ..debug.collector import build_record, collect_args, collect_runtime_context, truncate
from ..debug.config import DebugConfig
from ..debug.context import pop_depth, push_depth
from ..debug.emitter import build_emitter
from ..debug.record import DebugRecord
from ..debug.renderers import get_renderer
from ..debug.sampler import build_sampler

F = TypeVar("F", bound=Callable[..., object])


def _source_location(fn: Callable) -> tuple[str, int]:
    try:
        file = inspect.getfile(fn)
        _, line = inspect.getsourcelines(fn)
        return file, line
    except (TypeError, OSError):
        return "<unknown>", 0


@overload
def debug(func: F) -> F: ...


@overload
def debug(
    func: None = None,
    *,
    mode: str = "pretty",
    label: str | None = None,
    max_length: int = 200,
    sample_rate: float = 1.0,
    every_n: int = 1,
    slow_threshold_ms: float | None = None,
    redact: tuple[str, ...] | list[str] = (),
    include_traceback: bool = False,
    include_caller: bool = False,
    logger: logging.Logger | None = None,
    log_level_ok: int = logging.DEBUG,
    log_level_slow: int = logging.WARNING,
    log_level_error: int = logging.ERROR,
    on_record: Callable[[DebugRecord], None] | None = None,
) -> Callable[[F], F]: ...


def debug(
    func: F | None = None,
    *,
    mode: str = "pretty",
    label: str | None = None,
    max_length: int = 200,
    sample_rate: float = 1.0,
    every_n: int = 1,
    slow_threshold_ms: float | None = None,
    redact: tuple[str, ...] | list[str] = (),
    include_traceback: bool = False,
    include_caller: bool = False,
    logger: logging.Logger | None = None,
    log_level_ok: int = logging.DEBUG,
    log_level_slow: int = logging.WARNING,
    log_level_error: int = logging.ERROR,
    on_record: Callable[[DebugRecord], None] | None = None,
) -> F | Callable[[F], F]:
    def decorator(fn: F) -> F:
        config = DebugConfig(
            mode=mode,  # type: ignore[arg-type]
            label=label,
            max_length=max_length,
            sample_rate=sample_rate,
            every_n=every_n,
            slow_threshold_ms=slow_threshold_ms,
            redact=tuple(redact),
            include_traceback=include_traceback,
            include_caller=include_caller,
            logger=logger,
            log_level_ok=log_level_ok,
            log_level_slow=log_level_slow,
            log_level_error=log_level_error,
        )
        name = config.label or f"{fn.__module__}.{fn.__qualname__}"
        file, line = _source_location(fn)
        renderer = get_renderer(config.mode)
        sampler = build_sampler(config.every_n, config.sample_rate)
        emitter = build_emitter(config, renderer)

        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: object, **kwargs: object) -> object:
                ctx = collect_runtime_context()
                args_repr = collect_args(fn, args, kwargs, config)

                caller: tuple[str | None, int | None] = (None, None)
                if config.include_caller:
                    frame = inspect.currentframe()
                    outer = frame.f_back if frame else None
                    if outer:
                        caller = (outer.f_code.co_filename, outer.f_lineno)

                depth_token = push_depth()
                start = time.perf_counter_ns()
                exc_caught: BaseException | None = None
                ret_repr: str | None = None

                try:
                    result = await fn(*args, **kwargs)  # type: ignore[misc]
                    ret_repr = truncate(repr(result), config.max_length)
                    return result
                except BaseException as exc:
                    exc_caught = exc
                    raise
                finally:
                    pop_depth(depth_token)
                    if sampler.should_emit():
                        record = build_record(
                            name=name,
                            file=file,
                            line=line,
                            ctx=ctx,
                            args_repr=args_repr,
                            return_repr=ret_repr,
                            exc=exc_caught,
                            duration_ns=time.perf_counter_ns() - start,
                            config=config,
                            caller=caller,
                        )
                        emitter.emit(record)
                        if on_record:
                            on_record(record)

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def sync_wrapper(*args: object, **kwargs: object) -> object:
            ctx = collect_runtime_context()
            args_repr = collect_args(fn, args, kwargs, config)

            caller: tuple[str | None, int | None] = (None, None)
            if config.include_caller:
                frame = inspect.currentframe()
                outer = frame.f_back if frame else None
                if outer:
                    caller = (outer.f_code.co_filename, outer.f_lineno)

            depth_token = push_depth()
            start = time.perf_counter_ns()
            exc_caught: BaseException | None = None
            ret_repr: str | None = None

            try:
                result = fn(*args, **kwargs)
                ret_repr = truncate(repr(result), config.max_length)
                return result
            except BaseException as exc:
                exc_caught = exc
                raise
            finally:
                pop_depth(depth_token)
                if sampler.should_emit():
                    record = build_record(
                        name=name,
                        file=file,
                        line=line,
                        ctx=ctx,
                        args_repr=args_repr,
                        return_repr=ret_repr,
                        exc=exc_caught,
                        duration_ns=time.perf_counter_ns() - start,
                        config=config,
                        caller=caller,
                    )
                    emitter.emit(record)
                    if on_record:
                        on_record(record)

        return sync_wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator
