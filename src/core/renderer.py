from __future__ import annotations

import json
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from .models import ProfileSnapshot, ProfileStats, TimerStats

RenderMode = Literal["simple", "pretty", "json"]

_console = Console(stderr=True)


def _fmt(ns: int | float) -> str:
    ns = float(ns)
    if ns < 1_000:
        return f"{ns:.0f} ns"
    if ns < 1_000_000:
        return f"{ns / 1_000:.3f} µs"
    if ns < 1_000_000_000:
        return f"{ns / 1_000_000:.3f} ms"
    return f"{ns / 1_000_000_000:.3f} s"


class BaseTimerRenderer(ABC):
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


def _fmt_bytes(b: int | float) -> str:
    b = float(b)
    if abs(b) < 1024:
        return f"{b:.0f} B"
    if abs(b) < 1024 ** 2:
        return f"{b / 1024:.2f} KB"
    return f"{b / 1024 ** 2:.2f} MB"


def _fmt_bytes_delta(b: int | float) -> str:
    prefix = "+" if b >= 0 else ""
    return f"{prefix}{_fmt_bytes(b)}"


class BaseProfileRenderer(ABC):
    @abstractmethod
    def render(self, stats: ProfileStats, snapshot: ProfileSnapshot) -> None: ...


class SimpleProfileRenderer(BaseProfileRenderer):
    def render(self, stats: ProfileStats, snapshot: ProfileSnapshot) -> None:
        parts = [
            f"[profile] {stats.name}",
            f"duration={_fmt(snapshot.duration_ns)}",
            f"cpu={_fmt(snapshot.cpu_ns)}",
            f"mem={_fmt_bytes_delta(snapshot.memory_delta_bytes)}",
            f"peak={_fmt_bytes(snapshot.memory_peak_bytes)}",
            f"threads={snapshot.threads_before}→{snapshot.threads_after}",
            f"calls={stats.calls}",
        ]
        print("  ".join(parts), file=sys.stderr)


class PrettyProfileRenderer(BaseProfileRenderer):
    def render(self, stats: ProfileStats, snapshot: ProfileSnapshot) -> None:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="dim", no_wrap=True)
        table.add_column(style="bold magenta", no_wrap=True)

        table.add_row("duration", _fmt(snapshot.duration_ns))
        table.add_row("cpu time", _fmt(snapshot.cpu_ns))
        table.add_row("memory delta", _fmt_bytes_delta(snapshot.memory_delta_bytes))
        table.add_row("memory peak", _fmt_bytes(snapshot.memory_peak_bytes))
        table.add_row(
            "threads",
            f"{snapshot.threads_before} → {snapshot.threads_after}",
        )
        table.add_row("calls", str(stats.calls))

        if stats.calls > 1:
            table.add_section()
            if stats.avg_duration_ns is not None:
                table.add_row("avg duration", _fmt(stats.avg_duration_ns))
            if stats.avg_cpu_ns is not None:
                table.add_row("avg cpu", _fmt(stats.avg_cpu_ns))

        _console.print(
            Panel(
                table,
                title=f"[magenta]📊  {stats.name}[/magenta]",
                border_style="magenta",
            )
        )


class JsonProfileRenderer(BaseProfileRenderer):
    def render(self, stats: ProfileStats, snapshot: ProfileSnapshot) -> None:
        data: dict[str, object] = {
            "name": stats.name,
            "calls": stats.calls,
            "duration_ms": snapshot.duration_ns / 1_000_000,
            "cpu_ms": snapshot.cpu_ns / 1_000_000,
            "memory_delta_bytes": snapshot.memory_delta_bytes,
            "memory_peak_bytes": snapshot.memory_peak_bytes,
            "threads_before": snapshot.threads_before,
            "threads_after": snapshot.threads_after,
        }
        if stats.calls > 1:
            if stats.avg_duration_ns is not None:
                data["avg_duration_ms"] = stats.avg_duration_ns / 1_000_000
            if stats.avg_cpu_ns is not None:
                data["avg_cpu_ms"] = stats.avg_cpu_ns / 1_000_000
        print(json.dumps(data), file=sys.stderr)


def get_profile_renderer(mode: RenderMode) -> BaseProfileRenderer:
    match mode:
        case "simple":
            return SimpleProfileRenderer()
        case "json":
            return JsonProfileRenderer()
        case _:
            return PrettyProfileRenderer()
