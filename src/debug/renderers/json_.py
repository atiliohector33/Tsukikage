from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from .base import BaseDebugRenderer

if TYPE_CHECKING:
    from ..record import DebugRecord


class JsonDebugRenderer(BaseDebugRenderer):
    def render(self, record: DebugRecord) -> None:
        print(self.format_plain(record), file=sys.stderr)

    def format_plain(self, record: DebugRecord) -> str:
        data: dict[str, object] = {
            "ts": record.timestamp,
            "name": record.name,
            "file": record.file,
            "line": record.line,
            "thread": {"id": record.thread_id, "name": record.thread_name},
            "task": record.task_name,
            "trace_id": record.trace_id,
            "span_id": record.span_id,
            "depth": record.depth,
            "args": record.args_repr,
            "duration_ms": round(record.duration_ns / 1_000_000, 6),
            "slow": record.slow,
            "raised": record.raised,
        }

        if record.caller_file:
            data["caller"] = {"file": record.caller_file, "line": record.caller_line}

        if record.raised:
            data["exception"] = {
                "type": record.exception_type,
                "message": record.exception_repr,
                "traceback": list(record.traceback_lines) if record.traceback_lines else None,
            }
            data["return"] = None
        else:
            data["return"] = record.return_repr
            data["exception"] = None

        return json.dumps(data)
