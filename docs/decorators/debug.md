# 🐛 @debug

> Designed for **multi-service Python backends**. See inside every call — args, return, exception, thread, task, trace ID, span ID, call depth, slow flag, redacted fields, full traceback, and who called whom.

---

## Basic usage

```python
from tsukikage import debug

@debug
def create_user(name: str, role: str = "viewer") -> dict:
    return {"id": 1, "name": name, "role": role}

create_user("Ada Lovelace", role="admin")
```

<div class="terminal">
╭───────────────── 🐛 __main__.create_user ─── <span class="dim">app.py:4</span> ──────────────────╮<br>
│&nbsp; &nbsp;<span class="dim">thread</span> &nbsp; &nbsp; <span class="cyn">MainThread (8588435648)</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">args</span> &nbsp; &nbsp; &nbsp; <span class="cyn">name='Ada Lovelace'</span>&nbsp; &nbsp;<span class="cyn">role='admin'</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">return</span> &nbsp; &nbsp; <span class="grn">{'id': 1, 'name': 'Ada Lovelace', 'role': 'admin'}</span> │<br>
│&nbsp; &nbsp;<span class="dim">duration</span> &nbsp; <span class="grn">18.3 µs</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
╰──────────────────────────────────────────────────────────────────────╯
</div>

When a function raises, the panel turns red and the exception is re-raised — `@debug` never swallows errors.

```python
@debug
def get_user(user_id: int) -> dict:
    if user_id <= 0:
        raise ValueError(f"invalid user_id: {user_id}")
    return {"id": user_id}

get_user(-1)   # raises — panel is red
```

<div class="terminal" style="border-left-color: #fc8181;">
╭──────────────── 💥 __main__.get_user ─── <span class="dim">app.py:8</span> ──────────────────╮<br>
│&nbsp; &nbsp;<span class="dim">thread</span> &nbsp; &nbsp; <span class="cyn">MainThread (8588435648)</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">args</span> &nbsp; &nbsp; &nbsp; <span class="cyn">user_id=-1</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="red">💥 ValueError</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">exception</span> &nbsp; <span class="red">ValueError: invalid user_id: -1</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">duration</span> &nbsp; <span class="grn">11.7 µs</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
╰──────────────────────────────────────────────────────────────────────╯
</div>

---

## Output modes

=== "pretty (default)"

    Rich-rendered panel. Border is **cyan** on success, **yellow** on slow calls, **red** on exceptions.

    ```python
    @debug(label="auth.login")
    def login(username: str) -> dict: ...
    ```

=== "simple"

    Single line per call. Great for high-volume logging where panels would be noise.

    ```python
    @debug(mode="simple", label="billing.charge")
    def charge(amount: float, currency: str) -> str: ...
    ```

    ```
    [debug] billing.charge  |  app.py:12  |  thread=MainThread  |  amount=99.9  currency='BRL'  |  → 'approved'  |  14.2 µs
    [debug] billing.charge  |  app.py:12  |  thread=MainThread  |  amount=-10.0  currency='BRL'  |  💥 ValueError: amount must be positive  |  9.1 µs
    ```

=== "json"

    One JSON object per call, written to stderr. Every field is present — structured logs, log shippers, and observability pipelines will love it.

    ```python
    @debug(mode="json", label="auth.login")
    def login(username: str, password: str) -> bool: ...
    ```

    **Success:**

    ```json
    {
      "ts": "2026-06-28T16:30:00.123456+00:00",
      "name": "auth.login",
      "file": "/app/auth.py",
      "line": 14,
      "thread": { "id": 8588435648, "name": "MainThread" },
      "task": null,
      "trace_id": "req-abc123",
      "span_id": "2946f57c",
      "depth": 1,
      "args": { "username": "'ada@example.com'", "password": "***" },
      "caller": { "file": "/app/gateway.py", "line": 88 },
      "duration_ms": 0.042,
      "slow": false,
      "raised": false,
      "return": "True",
      "exception": null
    }
    ```

    **Exception (with traceback):**

    ```json
    {
      "ts": "2026-06-28T16:30:01.000000+00:00",
      "name": "db.execute_query",
      "file": "/app/db.py",
      "line": 31,
      "thread": { "id": 8588435648, "name": "MainThread" },
      "task": null,
      "trace_id": "req-abc123",
      "span_id": "b4d1b2c3",
      "depth": 2,
      "args": { "sql": "'SELECT * FROM users WHERE id = 1'" },
      "caller": null,
      "duration_ms": 1.204,
      "slow": false,
      "raised": true,
      "return": null,
      "exception": {
        "type": "ConnectionError",
        "message": "ConnectionError: database unreachable",
        "traceback": [
          "Traceback (most recent call last):",
          "  File \"/app/db.py\", line 34, in _connect",
          "    raise ConnectionError(\"database unreachable\")",
          "ConnectionError: database unreachable"
        ]
      }
    }
    ```

---

## Distributed tracing

This is the feature that makes `@debug` genuinely useful in multi-service backends. Set a `trace_id` once at the entry point and every decorated call in that request — no matter how deeply nested — carries it automatically.

```python
from tsukikage import debug, set_trace_id, clear_trace_id

set_trace_id("req-2024-abc123")   # call this in your middleware / request handler

@debug(label="gateway.handle_order", mode="pretty")
def handle_order(order_id: str) -> dict:
    user = validate_user("usr-99")
    payment = process_payment(order_id, amount=149.90)
    return {"order_id": order_id, "user": user, "payment": payment}

@debug(label="auth.validate_user", mode="pretty")
def validate_user(user_id: str) -> dict:
    return {"user_id": user_id, "authorized": True}

@debug(label="payment.process", mode="pretty")
def process_payment(order_id: str, amount: float) -> dict:
    fraud = check_fraud(amount)
    return {"order_id": order_id, "amount": amount, "fraud": fraud}

@debug(label="antifraude.check", mode="pretty")
def check_fraud(amount: float) -> str:
    return "approved" if amount < 10_000 else "review"

handle_order("ORD-001")
clear_trace_id()
```

Each panel shows its position in the call tree:

| Field | What it tells you |
|---|---|
| `trace_id` | The request ID that spawned this entire call chain |
| `span_id` | Unique 8-hex ID for **this specific call** — different every time |
| `depth` | How deep in the call stack this function is (0 = entry point) |

<div class="terminal">
╭──────────────── 🐛 auth.validate_user ────────────────────────╮<br>
│&nbsp; &nbsp;<span class="dim">trace</span> &nbsp; &nbsp; <span class="cyn">req-2024-abc123</span>&nbsp; &nbsp;<span class="dim">span=2946f57c</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">depth</span> &nbsp; &nbsp; <span class="cyn">1</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">thread</span> &nbsp; &nbsp;<span class="cyn">MainThread (8588435648)</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">args</span> &nbsp; &nbsp; &nbsp;<span class="cyn">user_id='usr-99'</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">return</span> &nbsp; &nbsp;<span class="grn">{'user_id': 'usr-99', 'authorized': True}</span>&nbsp; &nbsp;│<br>
│&nbsp; &nbsp;<span class="dim">duration</span> &nbsp;<span class="grn">12.6 µs</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
╰───────────────────────────────────────────────────────────────╯
</div>

!!! tip "FastAPI / Django middleware"
    Set `set_trace_id(request.headers.get("X-Request-ID", secrets.token_hex(8)))` in your middleware. From that point on, every `@debug`-decorated function in the request lifecycle carries that ID — no context passing needed.

### Thread and asyncio safety

`trace_id` and `depth` are stored in a `ContextVar`. This means:

- In a **thread pool**: each thread has its own isolated copy. No cross-contamination between concurrent requests.
- In **asyncio**: each `Task` has its own copy. Two concurrent coroutines never see each other's trace IDs.

### API

```python
from tsukikage import set_trace_id, get_trace_id, clear_trace_id

set_trace_id("req-abc123")   # set for this thread/task
get_trace_id()               # → "req-abc123"
clear_trace_id()             # → None
```

---

## Redacting sensitive fields

Pass a list of argument names that should never appear in output — they're replaced with `***` regardless of mode.

```python
@debug(
    label="auth.login",
    redact=["password", "token", "card_number"],
)
def login(username: str, password: str, token: str) -> bool:
    ...

login("ada@example.com", password="s3cr3t", token="eyJ...")
```

<div class="terminal">
╭──────────────────── 🐛 auth.login ────────────────────────────╮<br>
│&nbsp; &nbsp;<span class="dim">args</span> &nbsp; &nbsp; &nbsp;<span class="cyn">username='ada@example.com'</span>&nbsp; &nbsp;<span class="dim">password=***</span>&nbsp; &nbsp;<span class="dim">token=***</span>│<br>
│&nbsp; &nbsp;<span class="dim">return</span> &nbsp; &nbsp;<span class="grn">True</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">duration</span> &nbsp;<span class="grn">5.1 µs</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
╰───────────────────────────────────────────────────────────────╯
</div>

Redaction happens **before** any output — the raw value is never serialised.

---

## Slow call detection

Flag calls that exceed a duration threshold. The panel border turns **yellow** and a `⚠ slow` marker appears.

```python
@debug(label="cache.lookup", slow_threshold_ms=20.0)
def lookup(key: str) -> str | None:
    time.sleep(0.05)   # 50 ms — above threshold
    return None
```

<div class="terminal" style="border-left-color: #f6e05e;">
╭─────────────────── ⚠  cache.lookup ──────────────────────────╮<br>
│&nbsp; &nbsp;<span class="dim">args</span> &nbsp; &nbsp; &nbsp;<span class="cyn">key='user:99:profile'</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">return</span> &nbsp; &nbsp;<span class="grn">None</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">duration</span> &nbsp;<span class="grn">52.6 ms</span>&nbsp; &nbsp;<span style="color: #f6e05e;">⚠ slow</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
╰──────────────────────────────────────────────────────────────╯
</div>

In JSON mode, the `"slow": true` field is set. In logger mode, slow calls are routed to `WARNING` level automatically.

---

## Full traceback capture

By default, only the exception type and message are captured. Set `include_traceback=True` to get the full stack trace as a structured list.

```python
@debug(label="db.execute", include_traceback=True)
def execute(sql: str) -> list:
    def _connect():
        raise ConnectionError("database unreachable")
    return _connect()

execute("SELECT * FROM users")
```

In JSON mode, the traceback appears as an array under `exception.traceback`. In pretty mode, each frame is shown inside the panel.

---

## Caller info

Know exactly which line of code triggered the decorated function.

```python
@debug(label="email.send", mode="simple", include_caller=True)
def send_email(to: str, subject: str) -> None: ...

# called from notifications.py line 88
send_email("ada@example.com", subject="Welcome!")
```

```
[debug] email.send  |  app.py:14  |  caller=notifications.py:88  |  to='ada@...'  subject='Welcome!'  |  → None  |  8.0 µs
```

In JSON mode, the field is:

```json
"caller": { "file": "/app/notifications.py", "line": 88 }
```

---

## Sampling

### Every N calls — deterministic

Emit a record on every N-th invocation. Useful for high-frequency hot paths where logging every call would be too much.

```python
@debug(label="metrics.event", mode="simple", every_n=100)
def record_event(event: str) -> None: ...
```

Only calls 100, 200, 300, … are emitted. Thread-safe.

### Sample rate — probabilistic

Emit approximately `sample_rate * 100`% of calls, chosen randomly.

```python
@debug(label="telemetry.span", mode="json", sample_rate=0.1)
def trace_span(span: str) -> None: ...
```

~10% of calls produce output. Useful when you want statistical coverage without overwhelming a log aggregator.

!!! note
    `every_n` takes precedence over `sample_rate`. If both are set, `every_n` is used.

---

## Logger routing

Route output to a Python `logging.Logger` instead of stderr. The log level is chosen automatically based on outcome:

| Outcome | Default level |
|---|---|
| Success | `DEBUG` |
| Slow call (above `slow_threshold_ms`) | `WARNING` |
| Exception | `ERROR` |

```python
import logging
from tsukikage import debug

logger = logging.getLogger("my_app")

@debug(label="api.handler", mode="simple", logger=logger, slow_threshold_ms=100.0)
def handle_request(endpoint: str) -> dict:
    return {"status": 200, "endpoint": endpoint}
```

Override any of the defaults:

```python
@debug(
    logger=logger,
    log_level_ok=logging.INFO,
    log_level_slow=logging.ERROR,
    log_level_error=logging.CRITICAL,
)
def critical_path() -> None: ...
```

!!! tip
    In production, pair `logger=` with `mode="simple"` or `mode="json"`. The `pretty` renderer falls back to simple formatting when writing to a logger — no ANSI escape codes in your log files.

---

## Truncating long values

```python
@debug(label="ml.predict", mode="simple", max_length=80)
def predict(features: list[float]) -> list[float]:
    return [round(x * 0.42, 4) for x in features]

predict([float(i) for i in range(50)])
```

```
[debug] ml.predict  |  ...  |  features=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.…  |  → [0.0, 0.42, 0.84, …
```

Both argument reprs and the return repr are individually capped. The default is 200 characters.

---

## Async support

`@debug` detects async functions automatically and wraps them correctly. In async mode, the `task` field captures the `asyncio.Task` name.

```python
from tsukikage import debug, set_trace_id

set_trace_id("req-async-xyz")

@debug(label="api.fetch_products", slow_threshold_ms=5.0)
async def fetch_products(category: str) -> list[dict]:
    await asyncio.sleep(0.02)    # 20 ms — above threshold
    return [{"id": 1, "name": "Keyboard"}]

await fetch_products("hardware")
```

<div class="terminal" style="border-left-color: #f6e05e;">
╭──────────────────── ⚠  api.fetch_products ────────────────────╮<br>
│&nbsp; &nbsp;<span class="dim">trace</span> &nbsp; &nbsp; <span class="cyn">req-async-xyz</span>&nbsp; &nbsp;<span class="dim">span=3b23652d</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">task</span> &nbsp; &nbsp; &nbsp;<span class="cyn">Task-1</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">thread</span> &nbsp; &nbsp;<span class="cyn">MainThread (8588435648)</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">args</span> &nbsp; &nbsp; &nbsp;<span class="cyn">category='hardware'</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">return</span> &nbsp; &nbsp;<span class="grn">[{'id': 1, 'name': 'Keyboard'}]</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">duration</span> &nbsp;<span class="grn">21.3 ms</span>&nbsp; &nbsp;<span style="color: #f6e05e;">⚠ slow</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
╰───────────────────────────────────────────────────────────────╯
</div>

Duration is wall time including all `await` suspensions.

---

## API reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `mode` | `"pretty"` \| `"simple"` \| `"json"` | `"pretty"` | Output format |
| `label` | `str \| None` | `None` | Custom name shown in output. Defaults to `module.qualname` |
| `max_length` | `int` | `200` | Max chars for each arg/return repr before truncation with `…` |
| `slow_threshold_ms` | `float \| None` | `None` | Mark the call as slow if duration exceeds this value (ms) |
| `redact` | `list[str]` | `[]` | Argument names whose values are replaced with `***` |
| `include_traceback` | `bool` | `False` | Capture full stack trace on exceptions |
| `include_caller` | `bool` | `False` | Capture file + line of the calling code |
| `every_n` | `int` | `1` | Emit output only on every N-th call |
| `sample_rate` | `float` | `1.0` | Fraction of calls to emit (0.0–1.0, probabilistic) |
| `logger` | `logging.Logger \| None` | `None` | Route output to this logger instead of stderr |
| `log_level_ok` | `int` | `logging.DEBUG` | Log level for successful calls |
| `log_level_slow` | `int` | `logging.WARNING` | Log level for slow calls |
| `log_level_error` | `int` | `logging.ERROR` | Log level for calls that raised an exception |

---

## Tracing context API

| Function | Description |
|---|---|
| `set_trace_id(value: str)` | Set the trace ID for the current thread/task |
| `get_trace_id() → str \| None` | Read the current trace ID |
| `clear_trace_id()` | Remove the trace ID (set to `None`) |

---

## Use cases

| Scenario | Recommended config |
|---|---|
| **Microservice request tracing** | `set_trace_id(request_id)` in middleware + `mode="json"` + `logger=` |
| **Debugging a flaky test** | `@debug` bare — pretty panel shows exact args on the failing call |
| **Securing a sensitive endpoint** | `redact=["password", "token", "api_key"]` |
| **Finding slow database queries** | `slow_threshold_ms=50.0` + `mode="simple"` |
| **High-throughput worker** | `every_n=100` or `sample_rate=0.05` to keep log volume low |
| **Production structured logs** | `mode="json"` + `logger=` → JSON lines to your aggregator |
| **Debugging async race conditions** | `trace_id` + `task` field identifies which Task touched what |
| **Understanding nested call flow** | `depth` field shows call nesting at a glance |
| **Post-mortem crash analysis** | `include_traceback=True` → full stack in structured JSON |
| **Auditing who calls what** | `include_caller=True` → file + line of every call site |
