from __future__ import annotations

import json
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from .models import DebugRecord, ProfileSnapshot, ProfileStats, TimerStats

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

def _fmt_bytes(b: int | float) -> str:
    """Format bytes as a human-readable string."""
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
    """Strategy interface for profile output rendering."""

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


# ---------------------------------------------------------------------------
# Debug renderers
# ---------------------------------------------------------------------------


def _display_file(file: str) -> str:
    """Return a short, readable file path relative to cwd when possible."""
    try:
        return str(Path(file).relative_to(Path.cwd()))
    except ValueError:
        return Path(file).name


class BaseDebugRenderer(ABC):
    """Strategy interface for debug output rendering."""

    @abstractmethod
    def render(self, record: DebugRecord) -> None: ...


class SimpleDebugRenderer(BaseDebugRenderer):
    def render(self, record: DebugRecord) -> None:
        file_display = _display_file(record.file)
        parts = [f"[debug] {record.name}", f"{file_display}:{record.line}"]

        if record.args_repr:
            parts.append("  ".join(f"{k}={v}" for k, v in record.args_repr.items()))

        if record.raised:
            parts.append(f"💥 {record.exception_repr}")
        else:
            parts.append(f"→ {record.return_repr}")

        parts.append(_fmt(record.duration_ns))
        print("  |  ".join(parts), file=sys.stderr)


class PrettyDebugRenderer(BaseDebugRenderer):
    def render(self, record: DebugRecord) -> None:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="dim", no_wrap=True)
        table.add_column(no_wrap=False, max_width=80)

        file_display = _display_file(record.file)
        table.add_row("file", f"[dim]{file_display}:{record.line}[/dim]")

        if record.args_repr:
            args_parts = [f"[yellow]{k}[/yellow]={v}" for k, v in record.args_repr.items()]
            table.add_row("args", "  ".join(args_parts))
        else:
            table.add_row("args", "[dim]—[/dim]")

        if record.raised:
            table.add_row("raised", f"[bold red]{record.exception_repr}[/bold red]")
        else:
            table.add_row("return", f"[green]{record.return_repr}[/green]")

        table.add_row("duration", _fmt(record.duration_ns))

        border = "red" if record.raised else "yellow"
        icon = "💥" if record.raised else "🐛"
        _console.print(
            Panel(
                table,
                title=f"[{border}]{icon}  {record.name}[/{border}]",
                border_style=border,
            )
        )


class JsonDebugRenderer(BaseDebugRenderer):
    def render(self, record: DebugRecord) -> None:
        data: dict[str, object] = {
            "name": record.name,
            "file": record.file,
            "line": record.line,
            "duration_ms": record.duration_ns / 1_000_000,
            "args": record.args_repr,
        }
        if record.raised:
            data["raised"] = record.exception_repr
        else:
            data["return"] = record.return_repr
        print(json.dumps(data), file=sys.stderr)


def get_debug_renderer(mode: RenderMode) -> BaseDebugRenderer:
    match mode:
        case "simple":
            return SimpleDebugRenderer()
        case "json":
            return JsonDebugRenderer()
        case _:
            return PrettyDebugRenderer()
