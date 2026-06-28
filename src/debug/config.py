from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ..core.renderer import RenderMode


@dataclass(frozen=True)
class DebugConfig:
    mode: RenderMode = "pretty"
    label: str | None = None
    max_length: int = 200
    sample_rate: float = 1.0
    every_n: int = 1
    slow_threshold_ms: float | None = None
    redact: tuple[str, ...] = field(default_factory=tuple)
    include_traceback: bool = False
    include_caller: bool = False
    logger: logging.Logger | None = None
    log_level_ok: int = logging.DEBUG
    log_level_slow: int = logging.WARNING
    log_level_error: int = logging.ERROR
