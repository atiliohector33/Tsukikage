from __future__ import annotations

import json
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from .models import TimerStats

RenderMode = Literal["simple", "pretty", "json"]

_console = Console(stderr=True)


def _fmt(ns: int | float) -> str:
    """Format a nanosecond duration as a human-readable string."""
    ns = float(ns)
    if ns < 1_000:
        return f"{ns:.0f} ns"
    if ns < 1_000_000:
        return f"{ns / 1_000:.3f} µs"
    if ns < 1_000_000_000:
        return f"{ns / 1_000_000:.3f} ms"
    return f"{ns / 1_000_000_000:.3f} s"


class BaseTimerRenderer(ABC):
    """Strategy interface for timer output rendering."""

    @abstractmethod
    def render(self, stats: TimerStats, duration_ns: int) -> None: ...


class SimpleTimerRenderer(BaseTimerRenderer):
    def render(self, stats: TimerStats, duration_ns: int) -> None:
        parts = [f"[timer] {stats.name} → {_fmt(duration_ns)}"]
        if stats.calls > 1 and stats.avg_ns is not None:
            parts.append(f"avg={_fmt(stats.avg_ns)}")
        parts.append(f"calls={stats.calls}")
        print("  ".join(parts), file=sys.stderr)


class PrettyTimerRenderer(BaseTimerRenderer):
    def render(self, stats: TimerStats, duration_ns: int) -> None:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="dim", no_wrap=True)
        table.add_column(style="bold green", no_wrap=True)

        table.add_row("duration", _fmt(duration_ns))
        table.add_row("calls", str(stats.calls))

        if stats.calls > 1 and stats.avg_ns is not None:
            table.add_row("avg", _fmt(stats.avg_ns))
            table.add_row("min", _fmt(stats.min_ns or 0))
            table.add_row("max", _fmt(stats.max_ns or 0))

            for p, label in ((50.0, "p50"), (75.0, "p75"), (95.0, "p95")):
                value = stats.percentile(p)
                if value is not None:
                    table.add_row(label, _fmt(value))

        _console.print(
            Panel(table, title=f"[cyan]⏱  {stats.name}[/cyan]", border_style="cyan")
        )


class JsonTimerRenderer(BaseTimerRenderer):
    def render(self, stats: TimerStats, duration_ns: int) -> None:
        data: dict[str, object] = {
            "name": stats.name,
            "duration_ms": duration_ns / 1_000_000,
            "calls": stats.calls,
        }
        if stats.avg_ns is not None:
            data["avg_ms"] = stats.avg_ns / 1_000_000
        if stats.min_ns is not None:
            data["min_ms"] = stats.min_ns / 1_000_000
        if stats.max_ns is not None:
            data["max_ms"] = stats.max_ns / 1_000_000
        for p in (50.0, 75.0, 95.0):
            value = stats.percentile(p)
            if value is not None:
                data[f"p{int(p)}_ms"] = value / 1_000_000
        print(json.dumps(data), file=sys.stderr)


def get_renderer(mode: RenderMode) -> BaseTimerRenderer:
    match mode:
        case "simple":
            return SimpleTimerRenderer()
        case "json":
            return JsonTimerRenderer()
        case _:
            return PrettyTimerRenderer()
