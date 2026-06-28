from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..record import DebugRecord


class BaseDebugRenderer(ABC):
    @abstractmethod
    def render(self, record: DebugRecord) -> None: ...

    @abstractmethod
    def format_plain(self, record: DebugRecord) -> str: ...


def display_file(path: str) -> str:
    try:
        return str(Path(path).relative_to(Path.cwd()))
    except ValueError:
        return Path(path).name
