# Roadmap

> Tsukikage is young. Here's where it stands and where it's going.

---

## Current: v0.4

| Decorator | Status | Description |
|-----------|--------|-------------|
| `@timer` | ✅ Stable | Nanosecond wall-clock, accumulated stats (avg, min, max, p50, p75, p95) |
| `@timeout` | ✅ Stable | SIGALRM on Unix, futures fallback, asyncio.wait_for for async |
| `@profile` | ✅ Stable | Wall time + CPU time + memory (tracemalloc) + thread count |
| `@debug` | ✅ Stable | Args, return, exception, thread, task, trace ID, span ID, call depth, slow flag, redaction, full traceback, caller info, sampling, logger routing |

All four decorators share the same interface:

- Bare form (`@timer`) and options form (`@timer(mode="json")`)
- Sync and async support
- Three output modes: `pretty` / `simple` / `json`
- `functools.wraps` — metadata preserved

### What's new in `@debug` v0.4

The debug decorator was rebuilt for multi-service Python backends:

| Feature | What it does |
|---|---|
| `trace_id` + `span_id` | Propagate a request ID through the entire call chain via `ContextVar` |
| `depth` | Track call nesting — 0 is the entry point, increments with each nested `@debug` |
| `redact` | Replace argument values with `***` before any output is written |
| `slow_threshold_ms` | Flag calls that exceed a duration; yellow panel, `WARNING` log level |
| `include_traceback` | Capture the full stack trace on exceptions, structured as an array in JSON |
| `include_caller` | Record the file and line number of the code that called the function |
| `every_n` | Deterministic sampling — emit on every N-th call, thread-safe |
| `sample_rate` | Probabilistic sampling — emit ~X% of all calls |
| `logger` | Route output to any `logging.Logger` with auto-levelling (DEBUG/WARNING/ERROR) |

---

## Upcoming

### v0.5 — `@log`

The decorator the big dream is built on.

```python
@log(level="INFO", include=["args", "return", "duration"])
def process_payment(order_id: str) -> Receipt:
    ...
```

Structured log output that plays nicely with `logging.Logger`, JSON log pipelines, and cloud log sinks. Drop-in for teams that already have a log aggregator — no new infrastructure needed.

---

### v0.6 — `@retry`

```python
@retry(times=3, delay=0.5, on=httpx.HTTPError)
def fetch(url: str) -> bytes:
    ...
```

Automatic retry with configurable backoff, exception filtering, and optional jitter. Composable with `@timeout` for retry-with-limit patterns.

---

### v0.7 — `@cache`

```python
@cache(ttl=60, key=lambda url, **_: url)
def fetch_prices(url: str, headers: dict) -> dict:
    ...
```

Function-level cache with TTL, custom key functions, and an invalidation API. Think `functools.lru_cache` but time-aware and inspectable.

---

### v1.0 — Composability

The big unlock: stack decorators and have them talk to each other.

```python
@log
@retry(times=3)
@timeout(seconds=5)
@timer
def call_api() -> dict:
    ...
```

Each decorator in the stack reports through a single unified trace record — one JSON blob that tells the whole story of that call.

---

## The big dream

We believe any Python developer should be able to understand exactly what their code is doing — **just by adding a decorator**.

No YAML configuration. No sidecar agents. No dashboards to set up. Just Python.

The path there:

```
v0.x  →  solid, composable primitives
v1.0  →  unified trace record
v2.0  →  optional cloud export (OTLP, Datadog, Grafana)
v3.0  →  AI-assisted anomaly detection
```

If you have ideas, open an issue on [GitHub](https://github.com/atiliohector33/Tsukikage/issues). We build this in public.
