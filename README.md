# 🌙 Tsukikage

> **One decorator. Total visibility.**

```
  _____            _    _ _
 |_   _|          | |  (_) |
   | |___ _   _| | ___| | | ____ _  __ _  ___
   | / __| | | | |/ / | | |/ / _` |/ _` |/ _ \
   | \__ \ |_| |   <| | |   < (_| | (_| |  __/
   \_/___/\__,_|_|\_\_|_|_|\_\__,_|\__, |\___|
                                     __/ |
                                    |___/
```

*Tsukikage (月影) — moonlight in Japanese. Subtle. Always present. Illuminates what was hidden.*

---

Python instrumentation through decorators. Add **one line** to any function and get timing, profiling, timeouts, retries, and more — with zero configuration and beautiful terminal output.

---

## The Big Dream 🚀

We believe observability shouldn't require a PhD in DevOps.

The dream is simple: **any Python developer — from beginner to staff engineer — should be able to understand exactly what their code is doing, just by adding a decorator.** No YAML files, no agents to configure, no dashboards to set up. Just Python.

```python
@log
def process_payment(order_id: str) -> Receipt:
    ...
```

That one line should tell you everything: how long it took, how much memory it used, what the arguments were, what it returned, whether it raised an exception — and optionally ping your Slack when it fails in production.

That's where we're going. We're just getting started.

---

## What's here today (v0.2) ✅

| Decorator | What it does |
|-----------|-------------|
| `@timer` | Measures execution time with nanosecond precision. Tracks avg, min, max, and percentiles across calls. |
| `@timeout` | Kills a function if it takes too long. Works with sync and async. Raises `TimeoutExpired`. |
| `@profile` | All-in-one snapshot: wall time, CPU time, memory delta, memory peak, and thread count. |

---

## Install

```bash
pip install tsukikage
```

Or with Poetry:

```bash
poetry add tsukikage
```

**Requires Python 3.10+**

---

## `@timer` — Know exactly how long things take ⏱️

### Basic usage

```python
from tsukikage import timer

@timer
def fetch_user(user_id: int) -> dict:
    # simulate a database call
    import time; time.sleep(0.042)
    return {"id": user_id, "name": "Ada Lovelace"}

fetch_user(1)
```

**Output (pretty mode, default):**
```
╭─ ⏱  __main__.fetch_user ──────────────────╮
│  duration    42.317 ms                      │
│  calls       1                              │
╰─────────────────────────────────────────────╯
```

---

### Call it multiple times → get full statistics

```python
for _ in range(10):
    fetch_user(1)
```

```
╭─ ⏱  __main__.fetch_user ──────────────────╮
│  duration    41.889 ms                      │
│  calls       10                             │
│  avg         42.104 ms                      │
│  min         41.312 ms                      │
│  max         43.891 ms                      │
│  p50         42.017 ms                      │
│  p75         42.544 ms                      │
│  p95         43.712 ms                      │
╰─────────────────────────────────────────────╯
```

The stats **accumulate across calls** — so you can benchmark a function throughout the lifetime of your program, not just a single run.

---

### Output modes

**simple** — clean one-liner, great for CI logs:

```python
@timer(mode="simple", label="db.query")
def query(): ...
```
```
[timer] db.query → 3.412 ms  avg=3.501 ms  calls=5
```

---

**json** — pipe to any observability tool:

```python
@timer(mode="json", label="api.search")
def search(q: str): ...
```
```json
{
  "name": "api.search",
  "duration_ms": 12.441,
  "calls": 3,
  "avg_ms": 13.012,
  "min_ms": 12.441,
  "max_ms": 14.103,
  "p50_ms": 12.887,
  "p75_ms": 13.501,
  "p95_ms": 14.003
}
```

---

### Inspect stats programmatically

```python
@timer(label="payments.charge")
def charge(amount: float): ...

charge(99.90)
charge(149.90)

stats = charge.stats()
print(stats.calls)    # 2
print(stats.avg_ns)   # avg in nanoseconds
print(stats.min_ns)   # fastest run
print(stats.max_ns)   # slowest run

# reset counters whenever you want
charge.reset()
```

---

### Use cases for `@timer`

| Scenario | Why it helps |
|----------|-------------|
| Slow API endpoint | See exactly which function is the bottleneck |
| Database query tuning | Track query time across hundreds of requests |
| Background job monitoring | Is that nightly job getting slower over time? |
| Benchmarking two implementations | Call both 100x, compare avg + p95 |
| Performance regression detection | Check before/after a refactor |

---

## `@timeout` — Never let a function hang forever 🚫⏳

### Basic usage

```python
from tsukikage import timeout, TimeoutExpired

@timeout(seconds=5.0)
def call_external_api() -> dict:
    import httpx
    return httpx.get("https://slow-api.example.com/data").json()

try:
    data = call_external_api()
except TimeoutExpired as e:
    print(f"Gave up after {e.seconds}s on '{e.func_name}'")
```

---

### Custom error message

```python
@timeout(seconds=2.0, message="The payment gateway is not responding.")
def authorize_payment(card_token: str): ...
```

---

### Works with async too

```python
import asyncio
from tsukikage import timeout

@timeout(seconds=3.0)
async def fetch_recommendations(user_id: int) -> list:
    await asyncio.sleep(10)  # simulating a slow upstream
    return []

# raises TimeoutExpired after 3 seconds
await fetch_recommendations(42)
```

---

### Combine with a retry (manual, for now)

```python
from tsukikage import timeout, TimeoutExpired

@timeout(seconds=2.0)
def unstable_service() -> str:
    ...

for attempt in range(3):
    try:
        result = unstable_service()
        break
    except TimeoutExpired:
        print(f"attempt {attempt + 1} timed out, retrying...")
```

> 💡 Soon `@retry` will handle this automatically.

---

### Use cases for `@timeout`

| Scenario | Why it helps |
|----------|-------------|
| Third-party HTTP calls | Don't let a slow vendor freeze your app |
| Database queries with no timeout | Guard against runaway queries |
| User-uploaded script execution | Hard-limit untrusted code |
| Async microservice calls | Cancel slow upstreams, return a fallback |
| Any function with an SLA | Enforce it at the code level |

---

## TimeoutExpired exception

```python
from tsukikage import TimeoutExpired

try:
    slow_function()
except TimeoutExpired as e:
    e.func_name   # "slow_function"
    e.seconds     # 5.0
    str(e)        # "'slow_function' timed out after 5.0s"
```

---

## `@profile` — The full picture in one decorator 📊

When `@timer` isn't enough and you need to know *why* something is slow.

### Basic usage

```python
from tsukikage import profile

@profile
def build_report(rows: list[dict]) -> bytes:
    data = [transform(r) for r in rows]
    return serialize(data)

build_report(my_rows)
```

**Output (pretty mode, default):**
```
╭─ 📊  __main__.build_report ─────────────────╮
│  duration      87.412 ms                      │
│  cpu time      84.103 ms                      │
│  memory delta  +4.21 MB                       │
│  memory peak   6.88 MB                        │
│  threads       4 → 4                          │
│  calls         1                              │
╰──────────────────────────────────────────────╯
```

Call it multiple times and you get averages too:

```
╭─ 📊  __main__.build_report ─────────────────╮
│  duration      91.003 ms                      │
│  cpu time      88.441 ms                      │
│  memory delta  +4.33 MB                       │
│  memory peak   6.92 MB                        │
│  threads       4 → 4                          │
│  calls         5                              │
│  ─────────────────────────────────────────── │
│  avg duration  89.214 ms                      │
│  avg cpu       86.782 ms                      │
╰──────────────────────────────────────────────╯
```

---

### Output modes

**simple** — one line with all metrics:

```python
@profile(mode="simple", label="etl.transform")
def transform(df): ...
```
```
[profile] etl.transform  duration=87.412ms  cpu=84.103ms  mem=+4.21MB  peak=6.88MB  threads=4→4  calls=1
```

---

**json** — structured output for log aggregators and dashboards:

```python
@profile(mode="json", label="ml.inference")
def predict(features): ...
```
```json
{
  "name": "ml.inference",
  "calls": 3,
  "duration_ms": 87.412,
  "cpu_ms": 84.103,
  "memory_delta_bytes": 4415488,
  "memory_peak_bytes": 7216128,
  "threads_before": 4,
  "threads_after": 4,
  "avg_duration_ms": 86.891,
  "avg_cpu_ms": 83.644
}
```

---

### Inspect snapshots programmatically

```python
@profile(label="db.migrate")
def run_migration(): ...

run_migration()

stats = run_migration.stats()
snap = stats.last             # most recent ProfileSnapshot

snap.duration_ns              # wall time in nanoseconds
snap.cpu_ns                   # CPU time (user + kernel), excludes sleep
snap.memory_delta_bytes       # bytes allocated during the call
snap.memory_peak_bytes        # peak Python-level memory during the call
snap.threads_before           # active threads before the call
snap.threads_after            # active threads after the call

stats.avg_duration_ns         # average across all calls
stats.avg_cpu_ns
stats.avg_memory_delta_bytes

run_migration.reset()         # clear accumulated snapshots
```

> **Memory note:** measured via `tracemalloc` — Python-level allocations only.
> C extensions (NumPy, Pandas internals) are not tracked.
> CPU time uses `time.process_time_ns()` and excludes `time.sleep()`.

---

### Works with async too

```python
@profile(label="api.fetch_all")
async def fetch_all(ids: list[int]) -> list[dict]:
    return await asyncio.gather(*[fetch(i) for i in ids])
```

---

### Use cases for `@profile`

| Scenario | Why it helps |
|----------|-------------|
| Memory leak investigation | Watch `memory_delta_bytes` grow across calls |
| CPU vs I/O bound analysis | High `duration`, low `cpu_ns` → you're waiting on I/O |
| Data pipeline tuning | See exactly which step allocates the most memory |
| ML inference profiling | Track CPU and memory per batch |
| Concurrency debugging | Thread count changing unexpectedly? Now you'll know. |

---

## How it works under the hood 🔧

- **`@timer`** uses `time.perf_counter_ns()` for nanosecond precision. Stats are stored in a thread-safe singleton registry, so they accumulate correctly even in multi-threaded apps.

- **`@profile`** combines `time.perf_counter_ns()` for wall time, `time.process_time_ns()` for CPU time, `tracemalloc` for memory, and `threading.active_count()` for threads. Zero extra dependencies — all stdlib.

- **`@timeout`** on Unix/macOS uses `SIGALRM` — which actually interrupts the function mid-execution. On Windows or from a worker thread, it falls back to `concurrent.futures` (the function finishes in the background, but your code moves on).

---

## Roadmap

### v0.1 ✅
- [x] `@timer` — execution time, stats, percentiles, 3 output modes
- [x] `@timeout` — sync + async, SIGALRM on Unix, thread fallback

### v0.2 ✅ (current)
- [x] `@profile` — wall time, CPU time, memory delta/peak, thread count

### v0.3
- [ ] `@retry` — attempts, delay, exponential backoff, jitter
- [ ] `@log` — the main decorator. Args, return value, exceptions, duration, memory
- [ ] `@trace` — auto call tree: `main → auth → db → save`
- [ ] `@debug` — dev-mode decorator showing args, return, file + line

### v0.4
- [ ] `@cache` — in-memory and disk, with TTL
- [ ] `@memory` — isolated memory measurement decorator
- [ ] `@count_calls` — call counter with reset

### v1.0
- [ ] `@notify` — send alerts to Slack, Discord, or Telegram on failure
- [ ] Plugin system — OpenTelemetry, Prometheus, Sentry
- [ ] CLI: `tsukikage inspect app.py`
- [ ] Framework integrations: FastAPI, Flask, Celery

---

## Philosophy

- **One decorator, one problem.** `@timer` times. `@timeout` limits. No surprises.
- **Zero config to start.** `@timer` with no arguments works perfectly.
- **Beautiful output by default.** Because you deserve to actually read your terminal.
- **Extensible.** Output modes, custom labels, programmatic access to stats — it's all there.

---

## Contributing

This project is in early development. Ideas, bug reports, and PRs are very welcome.

```bash
git clone https://github.com/thehecktour/tsukikage
cd tsukikage
poetry install
poetry run pytest
```

---

## License

MIT — do whatever you want with it.

---

*Built with care. Named after moonlight. Designed to make invisible things visible.* 🌙
