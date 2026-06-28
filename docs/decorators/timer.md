# ⏱ @timer

> Measure execution time with **nanosecond precision**. Stats accumulate across calls.

---

## Basic usage

```python
from tsukikage import timer

@timer
def fetch_user(user_id: int) -> dict:
    import time; time.sleep(0.042)
    return {"id": user_id, "name": "Ada Lovelace"}

fetch_user(1)
```

**Terminal output:**

<div class="terminal">
╭─ ⏱  __main__.fetch_user ───────────────────────╮<br>
│&nbsp; &nbsp;<span class="dim">duration</span> &nbsp; &nbsp;<span class="grn">42.317 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">calls</span> &nbsp; &nbsp; &nbsp;<span class="grn">1</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
╰────────────────────────────────────────────────╯
</div>

---

## Call it multiple times → get full statistics

```python
for _ in range(10):
    fetch_user(1)
```

<div class="terminal">
╭─ ⏱  __main__.fetch_user ───────────────────────╮<br>
│&nbsp; &nbsp;<span class="dim">duration</span> &nbsp; &nbsp;<span class="grn">41.889 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">calls</span> &nbsp; &nbsp; &nbsp;<span class="grn">10</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;│<br>
│&nbsp; &nbsp;<span class="dim">avg</span> &nbsp; &nbsp; &nbsp; &nbsp;<span class="grn">42.104 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">min</span> &nbsp; &nbsp; &nbsp; &nbsp;<span class="grn">41.312 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">max</span> &nbsp; &nbsp; &nbsp; &nbsp;<span class="grn">43.891 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">p50</span> &nbsp; &nbsp; &nbsp; &nbsp;<span class="grn">42.017 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">p75</span> &nbsp; &nbsp; &nbsp; &nbsp;<span class="grn">42.544 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">p95</span> &nbsp; &nbsp; &nbsp; &nbsp;<span class="grn">43.712 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
╰────────────────────────────────────────────────╯
</div>

Stats **accumulate across calls** for the lifetime of the program — no manual averaging needed.

---

## Output modes

=== "pretty (default)"

    ```python
    @timer                     # or @timer(mode="pretty")
    def query(sql: str): ...
    ```

    Rich panel with color, border, and aligned table. Best for interactive development.

=== "simple"

    ```python
    @timer(mode="simple", label="db.query")
    def query(sql: str): ...
    ```

    ```
    [timer] db.query → 3.412 ms  avg=3.501 ms  calls=5
    ```

    One line. Great for CI logs or scripts where you want low noise.

=== "json"

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

    Pipe directly into Datadog, Grafana Loki, or any log aggregator.

---

## Programmatic access

```python
@timer(label="payments.charge")
def charge(amount: float): ...

charge(99.90)
charge(149.90)

stats = charge.stats()
print(stats.calls)     # 2
print(stats.avg_ns)    # average in nanoseconds
print(stats.min_ns)    # fastest run
print(stats.max_ns)    # slowest run
print(stats.percentile(95))  # p95 in nanoseconds

charge.reset()         # clear accumulated data
```

!!! tip "Stats survive exceptions"
    If the decorated function raises, the call is **still counted** and the duration is **still recorded**. You won't lose your baseline.

---

## Async support

```python
@timer(label="ws.broadcast")
async def broadcast(message: str) -> int:
    await asyncio.gather(...)
    return sent_count

await broadcast("hello")
```

Works identically — wall clock time includes all awaited operations.

---

## API reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `"pretty"` \| `"simple"` \| `"json"` | `"pretty"` | Output format |
| `label` | `str \| None` | `None` | Custom metric name. Defaults to `module.qualname` |

---

## Use cases

| Scenario | Why `@timer` |
|----------|-------------|
| Slow API endpoint | Find the exact bottleneck — not just "the endpoint is slow" |
| Database query tuning | Track time across hundreds of real requests |
| Background job monitoring | Catch gradual slowdowns before users notice |
| Benchmarking two implementations | Call both 100× and compare avg + p95 |
| Pre/post refactor check | Did the rewrite actually make it faster? |
