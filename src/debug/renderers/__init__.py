from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseDebugRenderer
from .json_ import JsonDebugRenderer
from .pretty import PrettyDebugRenderer
from .simple import SimpleDebugRenderer

if TYPE_CHECKING:
    from ...core.renderer import RenderMode


def get_renderer(mode: RenderMode) -> BaseDebugRenderer:
    match mode:
        case "simple":
            return SimpleDebugRenderer()
        case "json":
            return JsonDebugRenderer()
        case _:
            return PrettyDebugRenderer()


__all__ = [
    "BaseDebugRenderer",
    "JsonDebugRenderer",
    "PrettyDebugRenderer",
    "SimpleDebugRenderer",
    "get_renderer",
]
