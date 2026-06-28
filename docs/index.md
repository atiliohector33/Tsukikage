---
hide:
  - toc
---

<div class="hero" markdown>

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

<p class="hero-tagline">月影 — moonlight. Subtle. Always present. Illuminates what was hidden.</p>

[Get started &nbsp; →](#install){ .md-button .md-button--primary }
[View on GitHub](https://github.com/atiliohector33/Tsukikage){ .md-button }

</div>

---

## What is it?

**Tsukikage** is a Python instrumentation library built entirely around decorators.

Add **one line** to any function and instantly get timing, profiling, timeout protection, and dev-mode debugging — with zero configuration and beautiful terminal output.

```python
from tsukikage import timer, timeout, profile, debug
```

That's all the importing you'll ever need to do.

---

## Decorators

<div class="grid cards" markdown>

-   :material-timer-outline:{ .lg } &nbsp; **@timer**

    ---

    Nanosecond wall-clock timing. Stats accumulate across calls: avg, min, max, p50, p75, p95.

    [:octicons-arrow-right-24: Read the docs](decorators/timer.md)

-   :material-timer-off-outline:{ .lg } &nbsp; **@timeout**

    ---

    Kill functions that run too long. True interruption via SIGALRM on Unix. Async-native.

    [:octicons-arrow-right-24: Read the docs](decorators/timeout.md)

-   :material-chart-bar:{ .lg } &nbsp; **@profile**

    ---

    One snapshot with everything: wall time, CPU time, memory delta/peak, thread count.

    [:octicons-arrow-right-24: Read the docs](decorators/profile.md)

-   :material-bug-outline:{ .lg } &nbsp; **@debug**

    ---

    Built for multi-service backends. Args, return, exception, thread, task, **trace ID**, span ID, call depth, slow flag, redaction, full traceback, caller info, sampling, and logger routing.

    [:octicons-arrow-right-24: Read the docs](decorators/debug.md)

</div>

---

## Install

=== "pip"

    ```bash
    pip install tsukikage
    ```

=== "poetry"

    ```bash
    poetry add tsukikage
    ```

=== "uv"

    ```bash
    uv add tsukikage
    ```

!!! info "Requirements"
    Python **3.10+**. The only runtime dependency is [`rich`](https://github.com/Textualize/rich) for terminal output.

---

## Quick start

```python
from tsukikage import timer, debug, profile, timeout, TimeoutExpired
from tsukikage import set_trace_id, clear_trace_id
import time

# ── time a function ────────────────────────────────────────────────────────
@timer
def fetch_user(user_id: int) -> dict:
    time.sleep(0.04)
    return {"id": user_id, "name": "Ada Lovelace"}

fetch_user(1)   # pretty panel to stderr
fetch_user(2)   # now shows avg, min, max, p50, p95

# ── inspect every call, distributed-tracing style ─────────────────────────
set_trace_id("req-abc123")   # set once in your request middleware

@debug(label="auth.validate", redact=["password"])
def validate(username: str, password: str) -> dict:
    return {"user": username, "ok": True}

@debug(label="orders.create", slow_threshold_ms=50.0)
def create_order(item: str, qty: int = 1) -> dict:
    return {"item": item, "qty": qty, "total": qty * 9.99}

validate("ada", password="s3cr3t")  # password shown as ***
create_order("widget", qty=3)       # slow flag if > 50 ms
clear_trace_id()

# ── profile memory + cpu ───────────────────────────────────────────────────
@profile
def build_index(docs: list[str]) -> dict:
    return {word: i for i, doc in enumerate(docs) for word in doc.split()}

build_index(["hello world", "foo bar baz"])

# ── protect against slow calls ─────────────────────────────────────────────
@timeout(seconds=2.0, message="upstream took too long")
def call_api() -> dict:
    ...

try:
    call_api()
except TimeoutExpired as e:
    print(e)   # "upstream took too long"
```

---

## The big dream 🚀

We believe observability shouldn't require a PhD in DevOps.

The dream is simple: **any Python developer — from beginner to staff engineer — should be able to understand exactly what their code is doing, just by adding a decorator.**

No YAML. No agents. No dashboards. Just Python.

```python
@log
def process_payment(order_id: str) -> Receipt:
    ...
```

That one line should tell you everything: how long it took, how much memory it used, what the arguments were, what it returned, whether it raised an exception — and optionally ping your Slack when it fails in production.

That's where we're going. We're [just getting started](roadmap.md).
