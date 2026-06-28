from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DebugRecord:
    name: str
    file: str
    line: int
    args_repr: dict[str, str]
    return_repr: str | None
    exception_repr: str | None
    exception_type: str | None
    traceback_lines: tuple[str, ...] | None
    duration_ns: int
    timestamp: str
    thread_id: int
    thread_name: str
    task_name: str | None
    trace_id: str | None
    span_id: str
    caller_file: str | None
    caller_line: int | None
    depth: int
    slow: bool

    @property
    def raised(self) -> bool:
        return self.exception_repr is not None
