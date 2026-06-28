from __future__ import annotations

from contextvars import ContextVar, Token

_trace_id: ContextVar[str | None] = ContextVar("tsukikage_trace_id", default=None)
_call_depth: ContextVar[int] = ContextVar("tsukikage_call_depth", default=0)


def set_trace_id(value: str) -> None:
    _trace_id.set(value)


def get_trace_id() -> str | None:
    return _trace_id.get()


def clear_trace_id() -> None:
    _trace_id.set(None)


def get_depth() -> int:
    return _call_depth.get()


def push_depth() -> Token[int]:
    return _call_depth.set(_call_depth.get() + 1)


def pop_depth(token: Token[int]) -> None:
    _call_depth.reset(token)
