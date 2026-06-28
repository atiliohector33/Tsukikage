# 🚫 @timeout

> Set a **hard time limit** on any function. If it doesn't finish in time, raise `TimeoutExpired`.

---

## Basic usage

```python
from tsukikage import timeout, TimeoutExpired

@timeout(seconds=5.0)
def call_external_api() -> dict:
    import time; time.sleep(10)   # simulates a slow upstream
    return {"status": "ok"}

try:
    call_external_api()
except TimeoutExpired as e:
    print(f"Timed out: {e}")
```

`TimeoutExpired` is raised after exactly **5 seconds** — the function is interrupted mid-execution.

---

## Custom message

```python
@timeout(seconds=3.0, message="payment gateway took too long — retry or use fallback")
def charge_card(token: str) -> dict:
    ...

try:
    charge_card("tok_abc123")
except TimeoutExpired as e:
    print(e.message)    # "payment gateway took too long — retry or use fallback"
    print(e.func_name)  # "charge_card"
    print(e.seconds)    # 3.0
```

!!! tip "Structured exception"
    `TimeoutExpired` carries `.func_name`, `.seconds`, and `.message` — easy to log or forward to alerting.

---

## Async support

```python
@timeout(seconds=2.0, message="websocket response timeout")
async def wait_for_ack(ws) -> bool:
    async for msg in ws:
        if msg.type == "ack":
            return True
    return False

result = await wait_for_ack(connection)
```

For async functions, `@timeout` uses `asyncio.wait_for` — fully cooperative with the event loop, no background threads.

---

## Retry pattern

Combine `@timeout` with any retry library or a simple loop:

```python
import time

@timeout(seconds=2.0)
def fetch(url: str) -> str:
    ...

for attempt in range(3):
    try:
        return fetch(url)
    except TimeoutExpired:
        if attempt == 2:
            raise
        time.sleep(0.5 * (attempt + 1))
```

---

## How it works under the hood

=== "Unix — SIGALRM (default)"

    On macOS / Linux, when called from the **main thread**, `@timeout` uses `signal.SIGALRM`:

    ```
    signal.alarm(seconds)   →   execute fn()   →   signal.alarm(0)
    ```

    - True OS-level interruption — works even if the function is blocked in C
    - Zero overhead — no extra threads
    - Requires main thread (Python limitation on signal handling)

=== "Windows / worker threads — futures"

    When `SIGALRM` is unavailable (Windows, or a non-main thread), `@timeout` falls back to `concurrent.futures`:

    ```
    ThreadPoolExecutor   →   Future.result(timeout=seconds)
    ```

    - Works on all platforms and in all threads
    - The underlying thread may linger after cancellation
    - Slightly higher overhead due to thread creation

The fallback is chosen **automatically** — you don't need to configure anything.

---

## `TimeoutExpired` reference

```python
from tsukikage import TimeoutExpired

try:
    my_fn()
except TimeoutExpired as e:
    e.func_name   # str — name of the decorated function
    e.seconds     # float — the limit that was exceeded
    e.message     # str | None — custom message, if provided
    str(e)        # formatted summary string
```

---

## API reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `seconds` | `float` | *(required)* | Time limit in seconds |
| `message` | `str \| None` | `None` | Optional message on `TimeoutExpired`. Defaults to auto-generated |

!!! warning "No bare-decorator form"
    `@timeout` always requires `seconds`. Use `@timeout(seconds=5.0)`, never just `@timeout`.

---

## Use cases

| Scenario | Limit suggestion |
|----------|-----------------|
| External HTTP call | `2–5 s` — depends on your SLA |
| Database query | `1–3 s` — slow query = bad query |
| File I/O on network drive | `10–30 s` |
| Background job step | `60–300 s` |
| LLM API call | `30–120 s` |
