from __future__ import annotations

from threading import Lock

from .models import ProfileStats, TimerStats


class _TimerRegistry:
    _instance: _TimerRegistry | None = None
    _init_lock: Lock = Lock()

    def __new__(cls) -> _TimerRegistry:
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._store: dict[str, TimerStats] = {}
                    instance._lock: Lock = Lock()
                    cls._instance = instance
        return cls._instance

    def get_or_create(self, name: str) -> TimerStats:
        with self._lock:
            if name not in self._store:
                self._store[name] = TimerStats(name=name)
            return self._store[name]

    def reset(self, name: str | None = None) -> None:
        with self._lock:
            if name is not None:
                self._store.pop(name, None)
            else:
                self._store.clear()

    @property
    def all(self) -> dict[str, TimerStats]:
        with self._lock:
            return dict(self._store)


timer_registry: _TimerRegistry = _TimerRegistry()


class _ProfileRegistry:
    _instance: _ProfileRegistry | None = None
    _init_lock: Lock = Lock()

    def __new__(cls) -> _ProfileRegistry:
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._store: dict[str, ProfileStats] = {}
                    instance._lock: Lock = Lock()
                    cls._instance = instance
        return cls._instance

    def get_or_create(self, name: str) -> ProfileStats:
        with self._lock:
            if name not in self._store:
                self._store[name] = ProfileStats(name=name)
            return self._store[name]

    def reset(self, name: str | None = None) -> None:
        with self._lock:
            if name is not None:
                self._store.pop(name, None)
            else:
                self._store.clear()

    @property
    def all(self) -> dict[str, ProfileStats]:
        with self._lock:
            return dict(self._store)


profile_registry: _ProfileRegistry = _ProfileRegistry()
