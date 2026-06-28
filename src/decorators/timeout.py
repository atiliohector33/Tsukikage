from __future__ import annotations

import asyncio
import concurrent.futures
import functools
import inspect
import signal
import sys
import threading
from typing import Callable, TypeVar

from ..exceptions import TimeoutExpired

F = TypeVar("F", bound=Callable[..., object])


def _can_use_signals() -> bool:
    return (
        sys.platform != "win32"
        and threading.current_thread() is threading.main_thread()
    )


def _run_with_signal(
    fn: Callable[..., object],
    seconds: float,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> object:
    def _handler(signum: int, frame: object) -> None:
        raise TimeoutExpired(fn.__qualname__, seconds)

    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return fn(*args, **kwargs)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, old_handler)


def _run_with_thread(
    fn: Callable[..., object],
    seconds: float,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> object:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn, *args, **kwargs)
    try:
        return future.result(timeout=seconds)
    except concurrent.futures.TimeoutError:
        raise TimeoutExpired(fn.__qualname__, seconds)
    finally:
        executor.shutdown(wait=False)


def timeout(
    seconds: float,
    *,
    message: str | None = None,
) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: object, **kwargs: object) -> object:
                try:
                    return await asyncio.wait_for(
                        fn(*args, **kwargs),  # type: ignore[arg-type]
                        timeout=seconds,
                    )
                except asyncio.TimeoutError:
                    raise TimeoutExpired(fn.__qualname__, seconds, message)

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def sync_wrapper(*args: object, **kwargs: object) -> object:
            runner = _run_with_signal if _can_use_signals() else _run_with_thread
            try:
                return runner(fn, seconds, args, kwargs)
            except TimeoutExpired as exc:
                if message:
                    raise TimeoutExpired(exc.func_name, exc.seconds, message) from None
                raise

        return sync_wrapper  # type: ignore[return-value]

    return decorator
