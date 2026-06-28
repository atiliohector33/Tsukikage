from __future__ import annotations

import asyncio
import json
import logging
import sys
import threading
import time
from io import StringIO

import pytest

from src import clear_trace_id, debug, get_trace_id, set_trace_id
from src.debug.record import DebugRecord
from src.debug.sampler import AlwaysSampler, NthSampler, RateSampler, build_sampler


def _capture(fn, *args, **kwargs) -> tuple[object, list[DebugRecord]]:
    captured: list[DebugRecord] = []

    @debug(mode="simple", on_record=captured.append)
    def wrapper(*a, **kw):
        return fn(*a, **kw)

    result = wrapper(*args, **kwargs)
    return result, captured


@pytest.fixture(autouse=True)
def reset_trace_context():
    clear_trace_id()
    yield
    clear_trace_id()


def test_return_value_preserved():
    captured: list[DebugRecord] = []

    @debug(label="d.add", on_record=captured.append)
    def add(a: int, b: int) -> int:
        return a + b

    assert add(3, 4) == 7
    assert captured[0].return_repr == "7"


def test_args_captured_by_name():
    captured: list[DebugRecord] = []

    @debug(label="d.args", on_record=captured.append)
    def fn(x: int, y: str = "hi") -> None:
        pass

    fn(42, y="hello")
    assert captured[0].args_repr == {"x": "42", "y": "'hello'"}


def test_exception_repr_captured_and_reraised():
    captured: list[DebugRecord] = []

    @debug(label="d.exc", on_record=captured.append)
    def boom() -> None:
        raise ValueError("something broke")

    with pytest.raises(ValueError, match="something broke"):
        boom()

    assert captured[0].raised
    assert "ValueError" in captured[0].exception_repr  # type: ignore[operator]
    assert captured[0].exception_type == "ValueError"
    assert captured[0].return_repr is None


def test_file_and_line_captured():
    captured: list[DebugRecord] = []

    @debug(label="d.location", on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    assert captured[0].file.endswith("test_debug.py")
    assert captured[0].line > 0


def test_duration_is_positive():
    captured: list[DebugRecord] = []

    @debug(label="d.dur", on_record=captured.append)
    def fn() -> None:
        time.sleep(0.001)

    fn()
    assert captured[0].duration_ns > 0


def test_no_args_function():
    captured: list[DebugRecord] = []

    @debug(label="d.noargs", on_record=captured.append)
    def fn() -> int:
        return 0

    fn()
    assert captured[0].args_repr == {}


def test_bare_decorator():
    @debug
    def bare() -> None:
        pass

    bare()


def test_label_override():
    captured: list[DebugRecord] = []

    @debug(label="custom.label", on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    assert captured[0].name == "custom.label"


def test_wraps_preserves_metadata():
    @debug(label="d.wraps")
    def documented(x: int) -> int:
        """Multiplies by two."""
        return x * 2

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Multiplies by two."


def test_max_length_truncates_args():
    captured: list[DebugRecord] = []

    @debug(label="d.trunc", max_length=10, on_record=captured.append)
    def fn(data: list) -> None:
        pass

    fn(list(range(100)))
    val = captured[0].args_repr["data"]
    assert val.endswith("…")
    assert len(val) <= 11


def test_max_length_truncates_return():
    captured: list[DebugRecord] = []

    @debug(label="d.trunc_ret", max_length=10, on_record=captured.append)
    def fn() -> str:
        return "x" * 100

    fn()
    assert captured[0].return_repr is not None
    assert captured[0].return_repr.endswith("…")


def test_thread_info_captured():
    captured: list[DebugRecord] = []

    @debug(label="d.thread", on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    assert captured[0].thread_id == threading.get_ident()
    assert isinstance(captured[0].thread_name, str)
    assert len(captured[0].thread_name) > 0


def test_timestamp_is_iso8601():
    captured: list[DebugRecord] = []

    @debug(label="d.ts", on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    ts = captured[0].timestamp
    assert "T" in ts
    assert ts.endswith("+00:00") or ts.endswith("Z") or "+00:00" in ts


def test_span_id_is_hex_string():
    captured: list[DebugRecord] = []

    @debug(label="d.span", on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    span = captured[0].span_id
    assert len(span) == 8
    int(span, 16)


def test_task_name_none_in_sync():
    captured: list[DebugRecord] = []

    @debug(label="d.task_sync", on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    assert captured[0].task_name is None


async def test_task_name_captured_in_async():
    captured: list[DebugRecord] = []

    @debug(label="d.task_async", on_record=captured.append)
    async def fn() -> None:
        pass

    await fn()
    assert captured[0].task_name is not None


def test_trace_id_none_by_default():
    captured: list[DebugRecord] = []

    @debug(label="d.notrace", on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    assert captured[0].trace_id is None


def test_trace_id_propagated():
    captured: list[DebugRecord] = []
    set_trace_id("req-abc123")

    @debug(label="d.trace", on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    assert captured[0].trace_id == "req-abc123"


def test_trace_id_clear():
    set_trace_id("req-xyz")
    clear_trace_id()
    assert get_trace_id() is None


def test_multiple_functions_share_trace_id():
    set_trace_id("shared-trace")
    records: list[DebugRecord] = []

    @debug(label="svc.a", on_record=records.append)
    def service_a() -> str:
        return "a"

    @debug(label="svc.b", on_record=records.append)
    def service_b() -> str:
        return "b"

    service_a()
    service_b()
    assert records[0].trace_id == "shared-trace"
    assert records[1].trace_id == "shared-trace"
    assert records[0].span_id != records[1].span_id


def test_depth_zero_at_top_level():
    captured: list[DebugRecord] = []

    @debug(label="d.depth0", on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    assert captured[0].depth == 0


def test_depth_increments_in_nested_calls():
    records: list[DebugRecord] = []

    @debug(label="outer", on_record=records.append)
    def outer() -> None:
        inner()

    @debug(label="inner", on_record=records.append)
    def inner() -> None:
        pass

    outer()
    outer_rec = next(r for r in records if r.name == "outer")
    inner_rec = next(r for r in records if r.name == "inner")
    assert outer_rec.depth == 0
    assert inner_rec.depth == 1


def test_slow_flag_false_when_fast():
    captured: list[DebugRecord] = []

    @debug(label="d.fast", slow_threshold_ms=1000.0, on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    assert captured[0].slow is False


def test_slow_flag_true_when_exceeds_threshold():
    captured: list[DebugRecord] = []

    @debug(label="d.slow", slow_threshold_ms=1.0, on_record=captured.append)
    def fn() -> None:
        time.sleep(0.05)

    fn()
    assert captured[0].slow is True


def test_redact_replaces_value_with_stars():
    captured: list[DebugRecord] = []

    @debug(label="d.redact", redact=["password", "token"], on_record=captured.append)
    def authenticate(username: str, password: str) -> bool:
        return True

    authenticate("ada", password="s3cr3t")
    assert captured[0].args_repr["password"] == "***"
    assert captured[0].args_repr["username"] == "'ada'"


def test_redact_leaves_other_args_intact():
    captured: list[DebugRecord] = []

    @debug(label="d.redact2", redact=["secret"], on_record=captured.append)
    def fn(a: int, secret: str) -> None:
        pass

    fn(42, secret="xyz")
    assert captured[0].args_repr["a"] == "42"
    assert captured[0].args_repr["secret"] == "***"


def test_traceback_not_captured_by_default():
    captured: list[DebugRecord] = []

    @debug(label="d.tb_off", on_record=captured.append)
    def fn() -> None:
        raise RuntimeError("oops")

    with pytest.raises(RuntimeError):
        fn()

    assert captured[0].traceback_lines is None


def test_traceback_captured_when_requested():
    captured: list[DebugRecord] = []

    @debug(label="d.tb_on", include_traceback=True, on_record=captured.append)
    def fn() -> None:
        raise RuntimeError("oops")

    with pytest.raises(RuntimeError):
        fn()

    assert captured[0].traceback_lines is not None
    assert any("RuntimeError" in line for line in captured[0].traceback_lines)


def test_caller_info_none_when_disabled():
    captured: list[DebugRecord] = []

    @debug(label="d.nocaller", on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    assert captured[0].caller_file is None
    assert captured[0].caller_line is None


def test_caller_info_captured_when_enabled():
    captured: list[DebugRecord] = []

    @debug(label="d.caller", include_caller=True, on_record=captured.append)
    def fn() -> None:
        pass

    fn()
    assert captured[0].caller_file is not None
    assert captured[0].caller_file.endswith("test_debug.py")
    assert isinstance(captured[0].caller_line, int)
    assert captured[0].caller_line > 0


def test_every_n_emits_only_nth_call():
    captured: list[DebugRecord] = []

    @debug(label="d.nth", every_n=3, on_record=captured.append)
    def fn() -> None:
        pass

    for _ in range(9):
        fn()

    assert len(captured) == 3


def test_every_n_1_emits_all():
    captured: list[DebugRecord] = []

    @debug(label="d.nth1", every_n=1, on_record=captured.append)
    def fn() -> None:
        pass

    for _ in range(5):
        fn()

    assert len(captured) == 5


def test_sample_rate_zero_emits_nothing():
    captured: list[DebugRecord] = []

    @debug(label="d.rate0", sample_rate=0.0, on_record=captured.append)
    def fn() -> None:
        pass

    for _ in range(50):
        fn()

    assert len(captured) == 0


def test_sample_rate_full_emits_all():
    captured: list[DebugRecord] = []

    @debug(label="d.rate1", sample_rate=1.0, on_record=captured.append)
    def fn() -> None:
        pass

    for _ in range(5):
        fn()

    assert len(captured) == 5


def test_always_sampler():
    s = AlwaysSampler()
    assert all(s.should_emit() for _ in range(100))


def test_nth_sampler_thread_safe():
    s = NthSampler(5)
    results = []
    lock = threading.Lock()

    def run():
        for _ in range(20):
            result = s.should_emit()
            with lock:
                results.append(result)

    threads = [threading.Thread(target=run) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 80
    assert sum(results) == 16


def test_rate_sampler_bounds():
    with pytest.raises(ValueError):
        RateSampler(1.5)
    with pytest.raises(ValueError):
        RateSampler(-0.1)


def test_nth_sampler_bounds():
    with pytest.raises(ValueError):
        NthSampler(0)


def test_build_sampler_every_n():
    s = build_sampler(every_n=4, sample_rate=1.0)
    assert isinstance(s, NthSampler)


def test_build_sampler_rate():
    s = build_sampler(every_n=1, sample_rate=0.5)
    assert isinstance(s, RateSampler)


def test_build_sampler_always():
    s = build_sampler(every_n=1, sample_rate=1.0)
    assert isinstance(s, AlwaysSampler)


def test_logger_receives_ok_at_debug_level():
    log_records: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            log_records.append(record)

    logger = logging.getLogger("test.debug.ok")
    logger.setLevel(logging.DEBUG)
    handler = Capture()
    logger.addHandler(handler)
    logger.propagate = False

    @debug(mode="simple", label="d.logok", logger=logger)
    def fn() -> str:
        return "ok"

    fn()
    assert len(log_records) == 1
    assert log_records[0].levelno == logging.DEBUG


def test_logger_receives_error_level_on_exception():
    log_records: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            log_records.append(record)

    logger = logging.getLogger("test.debug.err")
    logger.setLevel(logging.DEBUG)
    handler = Capture()
    logger.addHandler(handler)
    logger.propagate = False

    @debug(mode="simple", label="d.logerr", logger=logger)
    def fn() -> None:
        raise ValueError("bad")

    with pytest.raises(ValueError):
        fn()

    assert len(log_records) == 1
    assert log_records[0].levelno == logging.ERROR


def test_logger_receives_warning_for_slow_call():
    log_records: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            log_records.append(record)

    logger = logging.getLogger("test.debug.slow")
    logger.setLevel(logging.DEBUG)
    handler = Capture()
    logger.addHandler(handler)
    logger.propagate = False

    @debug(mode="simple", label="d.logslow", slow_threshold_ms=1.0, logger=logger)
    def fn() -> None:
        time.sleep(0.05)

    fn()
    assert log_records[0].levelno == logging.WARNING


def test_simple_mode_does_not_raise():
    @debug(mode="simple", label="d.simple")
    def fn(x: int) -> int:
        return x * 2

    fn(5)


def test_simple_mode_exception_reraises():
    @debug(mode="simple", label="d.simple_exc")
    def fn() -> None:
        raise RuntimeError("oops")

    with pytest.raises(RuntimeError):
        fn()


def test_json_mode_success_fields():
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
    assert data["raised"] is False
    assert "ts" in data
    assert "thread" in data
    assert "span_id" in data
    assert data["exception"] is None


def test_json_mode_exception_fields():
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
    assert data["raised"] is True
    assert data["exception"]["type"] == "KeyError"
    assert data["return"] is None


async def test_async_return_value():
    captured: list[DebugRecord] = []

    @debug(label="d.async", on_record=captured.append)
    async def fetch() -> str:
        await asyncio.sleep(0)
        return "data"

    assert await fetch() == "data"
    assert captured[0].return_repr == "'data'"


async def test_async_exception_reraised():
    captured: list[DebugRecord] = []

    @debug(label="d.async_exc", on_record=captured.append)
    async def boom() -> None:
        raise ValueError("async fail")

    with pytest.raises(ValueError, match="async fail"):
        await boom()

    assert captured[0].raised
    assert captured[0].exception_type == "ValueError"


async def test_async_thread_and_task_captured():
    captured: list[DebugRecord] = []

    @debug(label="d.async_ctx", on_record=captured.append)
    async def fn() -> None:
        await asyncio.sleep(0)

    await fn()
    assert captured[0].thread_id == threading.get_ident()
    assert captured[0].task_name is not None


async def test_async_trace_id_propagated():
    captured: list[DebugRecord] = []
    set_trace_id("async-trace-xyz")

    @debug(label="d.async_trace", on_record=captured.append)
    async def fn() -> None:
        pass

    await fn()
    assert captured[0].trace_id == "async-trace-xyz"


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
    assert data["task"] is not None


def test_debug_record_raised_false():
    r = DebugRecord(
        name="fn", file="f.py", line=1, args_repr={},
        return_repr="'ok'", exception_repr=None, exception_type=None,
        traceback_lines=None, duration_ns=100,
        timestamp="2026-01-01T00:00:00+00:00", thread_id=1, thread_name="main",
        task_name=None, trace_id=None, span_id="abcd1234",
        caller_file=None, caller_line=None, depth=0, slow=False,
    )
    assert not r.raised


def test_debug_record_raised_true():
    r = DebugRecord(
        name="fn", file="f.py", line=1, args_repr={},
        return_repr=None, exception_repr="ValueError: x", exception_type="ValueError",
        traceback_lines=None, duration_ns=100,
        timestamp="2026-01-01T00:00:00+00:00", thread_id=1, thread_name="main",
        task_name=None, trace_id=None, span_id="abcd1234",
        caller_file=None, caller_line=None, depth=0, slow=False,
    )
    assert r.raised
