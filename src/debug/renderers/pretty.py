from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...core.renderer import _fmt
from .base import BaseDebugRenderer, display_file
from .simple import SimpleDebugRenderer

if TYPE_CHECKING:
    from ..record import DebugRecord

_console = Console(stderr=True)


class PrettyDebugRenderer(BaseDebugRenderer):
    def render(self, record: DebugRecord) -> None:
        _console.print(self._build_panel(record))

    def format_plain(self, record: DebugRecord) -> str:
        return SimpleDebugRenderer().format_plain(record)

    def _build_panel(self, record: DebugRecord) -> Panel:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="dim", no_wrap=True)
        table.add_column(no_wrap=False, max_width=80)

        table.add_row("file", f"[dim]{display_file(record.file)}:{record.line}[/dim]")

        if record.trace_id:
            table.add_row("trace", f"[dim]{record.trace_id}[/dim]  [dim]span={record.span_id}[/dim]")
        if record.depth > 0:
            table.add_row("depth", str(record.depth))
        table.add_row("thread", f"[dim]{record.thread_name} ({record.thread_id})[/dim]")
        if record.task_name:
            table.add_row("task", f"[dim]{record.task_name}[/dim]")

        if record.caller_file:
            table.add_row(
                "caller",
                f"[dim]{display_file(record.caller_file)}:{record.caller_line}[/dim]",
            )

        if record.args_repr:
            args_parts = [f"[yellow]{k}[/yellow]={v}" for k, v in record.args_repr.items()]
            table.add_row("args", "  ".join(args_parts))
        else:
            table.add_row("args", "[dim]—[/dim]")

        if record.raised:
            table.add_row("raised", f"[bold red]{record.exception_repr}[/bold red]")
            if record.traceback_lines:
                tb = "\n".join(record.traceback_lines[-8:])
                table.add_row("traceback", f"[dim]{tb}[/dim]")
        else:
            table.add_row("return", f"[green]{record.return_repr}[/green]")

        dur = _fmt(record.duration_ns)
        table.add_row("duration", dur + ("  [bold yellow]⚠ slow[/bold yellow]" if record.slow else ""))

        border = "red" if record.raised else ("yellow" if record.slow else "cyan")
        icon = "💥" if record.raised else ("⚠ " if record.slow else "🐛")

        return Panel(
            table,
            title=f"[{border}]{icon} {record.name}[/{border}]",
            border_style=border,
        )
