# Decorators

All decorators follow the same conventions:

- Work as **bare decorators** (`@timer`) or **with options** (`@timer(mode="json")`)
- Support **sync and async** functions
- Use `functools.wraps` — your function's `__name__` and `__doc__` are preserved
- Output to **stderr** by default — never pollutes your stdout

Pick the one you need:

| Decorator | What it gives you | Stats? |
|-----------|-------------------|--------|
| [`@timer`](timer.md) | Execution time, accumulated statistics | ✅ yes |
| [`@timeout`](timeout.md) | Hard time limit — raises `TimeoutExpired` | — |
| [`@profile`](profile.md) | Time + CPU + memory + threads | ✅ yes |
| [`@debug`](debug.md) | Args, return, exception, file/line, thread, task, trace ID, span ID, call depth, slow flag, redaction, traceback, caller, sampling, logger routing | — |
