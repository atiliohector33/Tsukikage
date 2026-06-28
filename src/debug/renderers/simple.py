from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ...core.renderer import _fmt
from .base import BaseDebugRenderer, display_file

if TYPE_CHECKING:
    from ..record import DebugRecord


class SimpleDebugRenderer(BaseDebugRenderer):
    def render(self, record: DebugRecord) -> None:
        print(self.format_plain(record), file=sys.stderr)

    def format_plain(self, record: DebugRecord) -> str:
        parts: list[str] = [f"[debug] {record.name}", display_file(record.file) + f":{record.line}"]

        if record.trace_id:
            parts.append(f"trace={record.trace_id} span={record.span_id}")
        parts.append(f"thread={record.thread_name}")
        if record.task_name:
            parts.append(f"task={record.task_name}")
        if record.depth > 0:
            parts.append(f"depth={record.depth}")

        if record.args_repr:
            parts.append("  ".join(f"{k}={v}" for k, v in record.args_repr.items()))

        if record.raised:
            parts.append(f"💥 {record.exception_repr}")
        else:
            parts.append(f"→ {record.return_repr}")

        duration = _fmt(record.duration_ns)
        parts.append(duration + (" ⚠SLOW" if record.slow else ""))

        return "  |  ".join(parts)
