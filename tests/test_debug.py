from __future__ import annotations

import asyncio
import json
import sys
from io import StringIO

import pytest

from src import debug
from src.core.models import DebugRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _capture_stderr(fn, *args, **kwargs):
    """Call fn(*args, **kwargs), capture stderr, return (result, stderr_str)."""
    buf = StringIO()
    old, sys.stderr = sys.stderr, buf
    try:
        result = fn(*args, **kwargs)
    finally:
        sys.stderr = old
    return result, buf.getvalue()


# ---------------------------------------------------------------------------
# Basic correctness
# ---------------------------------------------------------------------------


def test_return_value_preserved():
    @debug(label="d.return")
    def add(a: int, b: int) -> int:
        return a + b

    assert add(3, 4) == 7


def test_args_captured_by_name():
    records: list[DebugRecord] = []

    @debug(label="d.args")
    def fn(x: int, y: str = "hi") -> None:
        pass

    from src.core.renderer import PrettyDebugRenderer

    original_render = PrettyDebugRenderer.render

    captured: list[DebugRecord] = []

    def capturing_render(self, record: DebugRecord) -> None:
        captured.append(record)

    PrettyDebugRenderer.render = capturing_render  # type: ignore[method-assign]
    try:
        fn(42, y="hello")
    finally:
        PrettyDebugRenderer.render = original_render  # type: ignore[method-assign]

    assert len(captured) == 1
    assert captured[0].args_repr["x"] == "42"
    assert captured[0].args_repr["y"] == "'hello'"


def test_return_repr_captured():
    captured: list[DebugRecord] = []

    @debug(label="d.ret_repr")
    def fn() -> dict:
        return {"ok": True}

    from src.core.renderer import PrettyDebugRenderer

    original = PrettyDebugRenderer.render

    def cap(self, record):
        captured.append(record)

    PrettyDebugRenderer.render = cap  # type: ignore[method-assign]
    try:
        fn()
    finally:
        PrettyDebugRenderer.render = original  # type: ignore[method-assign]

    assert captured[0].return_repr == "{'ok': True}"
    assert captured[0].exception_repr is None
    assert not captured[0].raised


def test_exception_repr_captured_and_reraised():
    captured: list[DebugRecord] = []

    @debug(label="d.exc")
    def boom() -> None:
        raise ValueError("something broke")

    from src.core.renderer import PrettyDebugRenderer

    original = PrettyDebugRenderer.render

    def cap(self, record):
        captured.append(record)

    PrettyDebugRenderer.render = cap  # type: ignore[method-assign]
    try:
        with pytest.raises(ValueError, match="something broke"):
            boom()
    finally:
        PrettyDebugRenderer.render = original  # type: ignore[method-assign]

    assert len(captured) == 1
    assert captured[0].raised
    assert "ValueError" in captured[0].exception_repr  # type: ignore[operator]
    assert "something broke" in captured[0].exception_repr  # type: ignore[operator]
    assert captured[0].return_repr is None


def test_file_and_line_captured():
    captured: list[DebugRecord] = []

    @debug(label="d.location")
    def fn() -> None:
        pass

    from src.core.renderer import PrettyDebugRenderer

    original = PrettyDebugRenderer.render

    def cap(self, record):
        captured.append(record)

    PrettyDebugRenderer.render = cap  # type: ignore[method-assign]
    try:
        fn()
    finally:
        PrettyDebugRenderer.render = original  # type: ignore[method-assign]

    assert captured[0].file.endswith("test_debug.py")
    assert isinstance(captured[0].line, int)
    assert captured[0].line > 0


def test_duration_is_positive():
    captured: list[DebugRecord] = []

    @debug(label="d.dur")
    def fn() -> None:
        pass

    from src.core.renderer import PrettyDebugRenderer

    original = PrettyDebugRenderer.render

    def cap(self, record):
        captured.append(record)

    PrettyDebugRenderer.render = cap  # type: ignore[method-assign]
    try:
        fn()
    finally:
        PrettyDebugRenderer.render = original  # type: ignore[method-assign]

    assert captured[0].duration_ns > 0


# ---------------------------------------------------------------------------
# max_length truncation
# ---------------------------------------------------------------------------


def test_max_length_truncates_args():
    captured: list[DebugRecord] = []

    @debug(label="d.trunc", max_length=10)
    def fn(data: list) -> None:
        pass

    from src.core.renderer import PrettyDebugRenderer

    original = PrettyDebugRenderer.render

    def cap(self, record):
        captured.append(record)

    PrettyDebugRenderer.render = cap  # type: ignore[method-assign]
    try:
        fn(list(range(100)))
    finally:
        PrettyDebugRenderer.render = original  # type: ignore[method-assign]

    assert len(captured[0].args_repr["data"]) <= 11  # 10 chars + "…"
    assert captured[0].args_repr["data"].endswith("…")


def test_max_length_truncates_return():
    captured: list[DebugRecord] = []

    @debug(label="d.trunc_ret", max_length=10)
    def fn() -> str:
        return "x" * 100

    from src.core.renderer import PrettyDebugRenderer

    original = PrettyDebugRenderer.render

    def cap(self, record):
        captured.append(record)

    PrettyDebugRenderer.render = cap  # type: ignore[method-assign]
    try:
        fn()
    finally:
        PrettyDebugRenderer.render = original  # type: ignore[method-assign]

    assert captured[0].return_repr is not None
    assert captured[0].return_repr.endswith("…")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_no_args_function():
    captured: list[DebugRecord] = []

    @debug(label="d.noargs")
    def fn() -> int:
        return 0

    from src.core.renderer import PrettyDebugRenderer

    original = PrettyDebugRenderer.render

    def cap(self, record):
        captured.append(record)

    PrettyDebugRenderer.render = cap  # type: ignore[method-assign]
    try:
        fn()
    finally:
        PrettyDebugRenderer.render = original  # type: ignore[method-assign]

    assert captured[0].args_repr == {}


def test_bare_decorator():
    @debug
    def bare() -> None:
        pass

    bare()  # should not raise


def test_label_override():
    captured: list[DebugRecord] = []

    @debug(label="custom.label")
    def fn() -> None:
        pass

    from src.core.renderer import PrettyDebugRenderer

    original = PrettyDebugRenderer.render

    def cap(self, record):
        captured.append(record)

    PrettyDebugRenderer.render = cap  # type: ignore[method-assign]
    try:
        fn()
    finally:
        PrettyDebugRenderer.render = original  # type: ignore[method-assign]

    assert captured[0].name == "custom.label"


# ---------------------------------------------------------------------------
# Render modes (smoke + JSON field assertions)
# ---------------------------------------------------------------------------


def test_simple_mode():
    @debug(mode="simple", label="d.simple")
    def fn(x: int) -> int:
        return x * 2

    fn(5)  # should not raise


def test_simple_mode_exception():
    @debug(mode="simple", label="d.simple_exc")
    def fn() -> None:
        raise RuntimeError("oops")

    with pytest.raises(RuntimeError):
        fn()


def test_json_mode_success():
    buf = StringIO()
    old, sys.stderr = sys.stderr, buf

    try:
        @debug(mode="json", label="d.json")
        def fn(a: int, b: int) -> int:
            return a + b

        fn(10, 20)
    finally:
        sys.stderr = old

    data = json.loads(buf.getvalue().strip())
    assert data["name"] == "d.json"
    assert data["args"] == {"a": "10", "b": "20"}
    assert data["return"] == "30"
    assert "duration_ms" in data
    assert "file" in data
    assert "line" in data
    assert "raised" not in data


def test_json_mode_exception():
    buf = StringIO()
    old, sys.stderr = sys.stderr, buf

    try:
        @debug(mode="json", label="d.json_exc")
        def fn() -> None:
            raise KeyError("missing")

        with pytest.raises(KeyError):
            fn()
    finally:
        sys.stderr = old

    data = json.loads(buf.getvalue().strip())
    assert "raised" in data
    assert "KeyError" in data["raised"]
    assert "return" not in data


# ---------------------------------------------------------------------------
# Async support
# ---------------------------------------------------------------------------


async def test_async_return_value():
    @debug(label="d.async")
    async def fetch() -> str:
        await asyncio.sleep(0)
        return "data"

    assert await fetch() == "data"


async def test_async_exception_reraised():
    @debug(label="d.async_exc")
    async def boom() -> None:
        raise ValueError("async fail")

    with pytest.raises(ValueError, match="async fail"):
        await boom()


async def test_async_json_output():
    buf = StringIO()
    old, sys.stderr = sys.stderr, buf

    try:
        @debug(mode="json", label="d.async_json")
        async def fn(n: int) -> int:
            await asyncio.sleep(0)
            return n * 3

        await fn(7)
    finally:
        sys.stderr = old

    data = json.loads(buf.getvalue().strip())
    assert data["args"] == {"n": "7"}
    assert data["return"] == "21"


# ---------------------------------------------------------------------------
# functools.wraps preservation
# ---------------------------------------------------------------------------


def test_wraps_preserves_metadata():
    @debug(label="d.wraps")
    def documented(x: int) -> int:
        """Multiplies by two."""
        return x * 2

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Multiplies by two."


# ---------------------------------------------------------------------------
# DebugRecord.raised property
# ---------------------------------------------------------------------------


def test_debug_record_raised_false():
    r = DebugRecord("fn", "f.py", 1, {}, "'ok'", None, 100)
    assert not r.raised


def test_debug_record_raised_true():
    r = DebugRecord("fn", "f.py", 1, {}, None, "ValueError: x", 100)
    assert r.raised
