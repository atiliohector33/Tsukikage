from __future__ import annotations


class TsukikageError(Exception):
    pass


class TimeoutExpired(TsukikageError):
    def __init__(
        self,
        func_name: str,
        seconds: float,
        message: str | None = None,
    ) -> None:
        self.func_name = func_name
        self.seconds = seconds
        super().__init__(message or f"'{func_name}' timed out after {seconds}s")
