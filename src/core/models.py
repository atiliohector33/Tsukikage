from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class TimerStats:
    """Accumulates timing statistics for a decorated function across all calls."""

    name: str
    calls: int = 0
    total_ns: int = 0
    min_ns: int | None = None
    max_ns: int | None = None
    durations_ns: list[int] = field(default_factory=list, repr=False)

    def record(self, duration_ns: int) -> None:
        self.calls += 1
        self.total_ns += duration_ns
        self.durations_ns.append(duration_ns)
        if self.min_ns is None or duration_ns < self.min_ns:
            self.min_ns = duration_ns
        if self.max_ns is None or duration_ns > self.max_ns:
            self.max_ns = duration_ns

    @property
    def avg_ns(self) -> float | None:
        return self.total_ns / self.calls if self.calls > 0 else None

    def percentile(self, p: float) -> float | None:
        """Return the p-th percentile in nanoseconds.

        Requires at least 2 recorded calls and 1 <= p <= 99.
        Uses the inclusive method which works well on small samples.
        """
        if self.calls < 2 or not (1.0 <= p <= 99.0):
            return None
        quantiles = statistics.quantiles(self.durations_ns, n=100, method="inclusive")
        return quantiles[round(p) - 1]

@dataclass(frozen=True)
class ProfileSnapshot:
    """Immutable record of a single @profile execution."""

    name: str
    duration_ns: int
    cpu_ns: int
    memory_before_bytes: int
    memory_after_bytes: int
    memory_peak_bytes: int
    threads_before: int
    threads_after: int

    @property
    def memory_delta_bytes(self) -> int:
        return self.memory_after_bytes - self.memory_before_bytes


def _avg(values: Sequence[int | float]) -> float | None:
    return sum(values) / len(values) if values else None


@dataclass
class ProfileStats:
    """Accumulates ProfileSnapshots across calls to a @profile-decorated function."""

    name: str
    calls: int = 0
    snapshots: list[ProfileSnapshot] = field(default_factory=list, repr=False)

    def record(self, snapshot: ProfileSnapshot) -> None:
        self.calls += 1
        self.snapshots.append(snapshot)

    @property
    def last(self) -> ProfileSnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    @property
    def avg_duration_ns(self) -> float | None:
        return _avg([s.duration_ns for s in self.snapshots])

    @property
    def avg_cpu_ns(self) -> float | None:
        return _avg([s.cpu_ns for s in self.snapshots])

    @property
    def avg_memory_delta_bytes(self) -> float | None:
        return _avg([s.memory_delta_bytes for s in self.snapshots])


# ---------------------------------------------------------------------------
# Debug models
# ---------------------------------------------------------------------------


@dataclass
class DebugRecord:
    """Single-call record produced by @debug."""

    name: str
    file: str
    line: int
    args_repr: dict[str, str]
    return_repr: str | None
    exception_repr: str | None
    duration_ns: int

    @property
    def raised(self) -> bool:
        return self.exception_repr is not None
