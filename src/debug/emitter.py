from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import DebugConfig
    from .record import DebugRecord
    from .renderers.base import BaseDebugRenderer


class BaseEmitter(ABC):
    @abstractmethod
    def emit(self, record: DebugRecord) -> None: ...


class StderrEmitter(BaseEmitter):
    def __init__(self, renderer: BaseDebugRenderer) -> None:
        self._renderer = renderer

    def emit(self, record: DebugRecord) -> None:
        self._renderer.render(record)


class LoggerEmitter(BaseEmitter):
    def __init__(
        self,
        renderer: BaseDebugRenderer,
        logger: logging.Logger,
        level_ok: int,
        level_slow: int,
        level_error: int,
    ) -> None:
        self._renderer = renderer
        self._logger = logger
        self._level_ok = level_ok
        self._level_slow = level_slow
        self._level_error = level_error

    def emit(self, record: DebugRecord) -> None:
        text = self._renderer.format_plain(record)
        self._logger.log(self._level_for(record), text)

    def _level_for(self, record: DebugRecord) -> int:
        if record.raised:
            return self._level_error
        if record.slow:
            return self._level_slow
        return self._level_ok


def build_emitter(config: DebugConfig, renderer: BaseDebugRenderer) -> BaseEmitter:
    if config.logger is not None:
        return LoggerEmitter(
            renderer,
            config.logger,  # type: ignore[arg-type]
            config.log_level_ok,
            config.log_level_slow,
            config.log_level_error,
        )
    return StderrEmitter(renderer)
