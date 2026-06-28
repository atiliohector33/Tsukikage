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

## What's here today (v0.1) ✅

| Decorator | What it does |
|-----------|-------------|
| `@timer` | Measures execution time with nanosecond precision. Tracks avg, min, max, and percentiles across calls. |
| `@timeout` | Kills a function if it takes too long. Works with sync and async. Raises `TimeoutExpired`. |

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

## How it works under the hood 🔧

- **`@timer`** uses `time.perf_counter_ns()` for nanosecond precision. Stats are stored in a thread-safe singleton registry, so they accumulate correctly even in multi-threaded apps.

- **`@timeout`** on Unix/macOS uses `SIGALRM` — which actually interrupts the function mid-execution. On Windows or from a worker thread, it falls back to `concurrent.futures` (the function finishes in the background, but your code moves on).

---

## Roadmap

### v0.1 (now)
- [x] `@timer` — execution time, stats, percentiles, 3 output modes
- [x] `@timeout` — sync + async, SIGALRM on Unix, thread fallback

### v0.2
- [ ] `@retry` — attempts, delay, exponential backoff, jitter
- [ ] `@log` — the main decorator. Args, return value, exceptions, duration
- [ ] `@trace` — auto call tree: `main → auth → db → save`
- [ ] `@debug` — dev-mode decorator showing args, return, file + line

### v0.3
- [ ] `@cache` — in-memory and disk, with TTL
- [ ] `@profile` — time + memory + CPU in one shot
- [ ] `@memory` — peak memory usage

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
