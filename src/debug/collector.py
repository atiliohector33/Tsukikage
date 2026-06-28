from __future__ import annotations

import asyncio
import secrets
import threading
import traceback
from datetime import datetime, timezone
from inspect import signature
from typing import TYPE_CHECKING

from .context import get_depth, get_trace_id
from .record import DebugRecord

if TYPE_CHECKING:
    from .config import DebugConfig


def _current_task_name() -> str | None:
    try:
        task = asyncio.current_task()
        return task.get_name() if task else None
    except RuntimeError:
        return None


def collect_runtime_context() -> dict[str, object]:
    return {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "thread_id": threading.get_ident(),
        "thread_name": threading.current_thread().name,
        "task_name": _current_task_name(),
        "trace_id": get_trace_id(),
        "span_id": secrets.token_hex(4),
        "depth": get_depth(),
    }


def collect_args(fn: object, args: tuple, kwargs: dict, config: DebugConfig) -> dict[str, str]:
    try:
        sig = signature(fn)  # type: ignore[arg-type]
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        result = {
            k: _truncate(repr(v), config.max_length)
            for k, v in bound.arguments.items()
        }
    except TypeError:
        result = {}
        if args:
            result["*args"] = _truncate(repr(args), config.max_length)
        if kwargs:
            result["**kwargs"] = _truncate(repr(kwargs), config.max_length)

    for key in config.redact:
        if key in result:
            result[key] = "***"

    return result


def build_record(
    *,
    name: str,
    file: str,
    line: int,
    ctx: dict[str, object],
    args_repr: dict[str, str],
    return_repr: str | None,
    exc: BaseException | None,
    duration_ns: int,
    config: DebugConfig,
    caller: tuple[str | None, int | None],
) -> DebugRecord:
    exception_repr: str | None = None
    exception_type: str | None = None
    traceback_lines: tuple[str, ...] | None = None

    if exc is not None:
        exception_type = type(exc).__name__
        exception_repr = f"{exception_type}: {exc}"
        if config.include_traceback:
            traceback_lines = tuple(traceback.format_exc().splitlines())

    slow = (
        config.slow_threshold_ms is not None
        and duration_ns > config.slow_threshold_ms * 1_000_000
    )

    return DebugRecord(
        name=name,
        file=file,
        line=line,
        args_repr=args_repr,
        return_repr=return_repr,
        exception_repr=exception_repr,
        exception_type=exception_type,
        traceback_lines=traceback_lines,
        duration_ns=duration_ns,
        timestamp=str(ctx["timestamp"]),
        thread_id=int(ctx["thread_id"]),  # type: ignore[arg-type]
        thread_name=str(ctx["thread_name"]),
        task_name=ctx["task_name"] if isinstance(ctx["task_name"], str) else None,
        trace_id=ctx["trace_id"] if isinstance(ctx["trace_id"], str) else None,
        span_id=str(ctx["span_id"]),
        caller_file=caller[0],
        caller_line=caller[1],
        depth=int(ctx["depth"]),  # type: ignore[arg-type]
        slow=slow,
    )


def truncate(s: str, max_length: int) -> str:
    return s if len(s) <= max_length else s[:max_length] + "…"


_truncate = truncate
