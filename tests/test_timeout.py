from __future__ import annotations

import asyncio
import time

import pytest

from src import TimeoutExpired, timeout


# ---------------------------------------------------------------------------
# Basic correctness
# ---------------------------------------------------------------------------


def test_completes_within_limit():
    @timeout(seconds=2.0)
    def fast() -> int:
        return 42

    assert fast() == 42


def test_return_value_preserved():
    @timeout(seconds=2.0)
    def get_data() -> dict[str, str]:
        return {"status": "ok"}

    assert get_data() == {"status": "ok"}


def test_arguments_forwarded():
    @timeout(seconds=2.0)
    def add(a: int, b: int) -> int:
        return a + b

    assert add(10, 32) == 42


# ---------------------------------------------------------------------------
# Timeout fires
# ---------------------------------------------------------------------------


def test_raises_on_slow_function():
    @timeout(seconds=0.05)
    def slow() -> None:
        time.sleep(2.0)

    with pytest.raises(TimeoutExpired):
        slow()


def test_exception_carries_func_name():
    @timeout(seconds=0.05)
    def sluggish() -> None:
        time.sleep(2.0)

    with pytest.raises(TimeoutExpired) as exc_info:
        sluggish()

    assert "sluggish" in exc_info.value.func_name


def test_exception_carries_seconds():
    @timeout(seconds=0.05)
    def slow() -> None:
        time.sleep(2.0)

    with pytest.raises(TimeoutExpired) as exc_info:
        slow()

    assert exc_info.value.seconds == 0.05


def test_custom_message():
    @timeout(seconds=0.05, message="response took too long")
    def slow() -> None:
        time.sleep(2.0)

    with pytest.raises(TimeoutExpired, match="response took too long"):
        slow()


# ---------------------------------------------------------------------------
# TimeoutExpired is a subclass of TsukikageError / Exception
# ---------------------------------------------------------------------------


def test_timeout_expired_is_exception():
    exc = TimeoutExpired("fn", 1.0)
    assert isinstance(exc, Exception)


def test_timeout_expired_str_default():
    exc = TimeoutExpired("process", 3.5)
    assert "process" in str(exc)
    assert "3.5" in str(exc)


def test_timeout_expired_str_custom():
    exc = TimeoutExpired("process", 3.5, "custom msg")
    assert str(exc) == "custom msg"


# ---------------------------------------------------------------------------
# Async support
# ---------------------------------------------------------------------------


async def test_async_completes_within_limit():
    @timeout(seconds=2.0)
    async def fast() -> str:
        await asyncio.sleep(0)
        return "done"

    assert await fast() == "done"


async def test_async_raises_on_slow():
    @timeout(seconds=0.05)
    async def slow() -> None:
        await asyncio.sleep(2.0)

    with pytest.raises(TimeoutExpired):
        await slow()


async def test_async_custom_message():
    @timeout(seconds=0.05, message="async timed out!")
    async def slow() -> None:
        await asyncio.sleep(2.0)

    with pytest.raises(TimeoutExpired, match="async timed out!"):
        await slow()


async def test_async_exception_carries_seconds():
    @timeout(seconds=0.1)
    async def slow() -> None:
        await asyncio.sleep(2.0)

    with pytest.raises(TimeoutExpired) as exc_info:
        await slow()

    assert exc_info.value.seconds == 0.1


# ---------------------------------------------------------------------------
# functools.wraps preservation
# ---------------------------------------------------------------------------


def test_wraps_preserves_name():
    @timeout(seconds=1.0)
    def documented() -> None:
        """Does something important."""

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Does something important."


async def test_async_wraps_preserves_name():
    @timeout(seconds=1.0)
    async def async_fn() -> None:
        """Async docstring."""

    assert async_fn.__name__ == "async_fn"
    assert async_fn.__doc__ == "Async docstring."


# ---------------------------------------------------------------------------
# Thread-based path (non-main thread, forces _run_with_thread)
# ---------------------------------------------------------------------------


def test_thread_path_completes():
    """_run_with_thread is used when called from a worker thread."""
    import threading

    @timeout(seconds=2.0)
    def work() -> int:
        return 99

    result: list[int] = []
    exc: list[Exception] = []

    def run() -> None:
        try:
            result.append(work())
        except Exception as e:
            exc.append(e)

    t = threading.Thread(target=run)
    t.start()
    t.join(timeout=5.0)

    assert not exc
    assert result == [99]


def test_thread_path_raises_on_slow():
    """_run_with_thread raises TimeoutExpired when the deadline is exceeded."""
    import threading
    import time

    @timeout(seconds=0.1)
    def slow() -> None:
        time.sleep(2.0)

    errors: list[Exception] = []

    def run() -> None:
        try:
            slow()
        except TimeoutExpired as e:
            errors.append(e)

    t = threading.Thread(target=run)
    t.start()
    t.join(timeout=5.0)

    assert len(errors) == 1
    assert isinstance(errors[0], TimeoutExpired)
