from __future__ import annotations

import random
from threading import Lock
from typing import Protocol, runtime_checkable


@runtime_checkable
class Sampler(Protocol):
    def should_emit(self) -> bool: ...


class AlwaysSampler:
    def should_emit(self) -> bool:
        return True


class RateSampler:
    def __init__(self, rate: float) -> None:
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"sample_rate must be in [0.0, 1.0], got {rate}")
        self._rate = rate

    def should_emit(self) -> bool:
        return random.random() < self._rate


class NthSampler:
    def __init__(self, n: int) -> None:
        if n < 1:
            raise ValueError(f"every_n must be >= 1, got {n}")
        self._n = n
        self._count = 0
        self._lock = Lock()

    def should_emit(self) -> bool:
        with self._lock:
            self._count += 1
            return self._count % self._n == 0


def build_sampler(every_n: int, sample_rate: float) -> Sampler:
    if every_n > 1:
        return NthSampler(every_n)
    if sample_rate < 1.0:
        return RateSampler(sample_rate)
    return AlwaysSampler()
