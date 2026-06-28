# 🐛 @debug

> See **inside every call** — args by name, return value, exception, file + line, duration. No `print()` needed.

---

## Basic usage

```python
from tsukikage import debug

@debug
def create_order(item: str, qty: int = 1) -> dict:
    return {"item": item, "qty": qty, "total": qty * 9.99}

create_order("widget", qty=3)
```

**Terminal output (success):**

<div class="terminal">
╭─ 🐛  __main__.create_order &nbsp;<span class="dim">example.py:4</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;──────╮<br>
│&nbsp; &nbsp;<span class="dim">item</span> &nbsp; &nbsp; &nbsp; <span class="cyn">'widget'</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;│<br>
│&nbsp; &nbsp;<span class="dim">qty</span> &nbsp; &nbsp; &nbsp; &nbsp;<span class="cyn">3</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;│<br>
│ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">return</span> &nbsp; &nbsp; <span class="grn">{'item': 'widget', 'qty': 3, 'total': 29.97}</span> &nbsp; &nbsp;│<br>
│&nbsp; &nbsp;<span class="dim">duration</span> &nbsp; <span class="grn">12.441 µs</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
╰────────────────────────────────────────────────────────────────────╯
</div>

---

## Exception path

```python
@debug
def parse_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)

parse_config("/etc/nonexistent.json")
```

**Terminal output (exception — red panel):**

<div class="terminal" style="border-left-color: #fc8181;">
╭─ 🐛💥 __main__.parse_config &nbsp;<span class="dim">app.py:7</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ──────╮<br>
│&nbsp; &nbsp;<span class="dim">path</span> &nbsp; &nbsp; &nbsp; <span class="cyn">'/etc/nonexistent.json'</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="red">💥 FileNotFoundError</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;│<br>
│&nbsp; &nbsp;<span class="dim">exception</span> &nbsp;<span class="red">[Errno 2] No such file or directory: '...'</span> &nbsp;│<br>
│&nbsp; &nbsp;<span class="dim">duration</span> &nbsp; <span class="grn">88.213 µs</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
╰────────────────────────────────────────────────────────────────────╯
</div>

The panel turns **red** and shows the exception type + message. The exception is **re-raised** — `@debug` never swallows errors.

---

## Output modes

=== "pretty (default)"

    ```python
    @debug
    def my_fn(x, y): ...
    ```

    Rich panel, color-coded by outcome. Yellow border on success, red + 💥 on exception.

=== "simple"

    ```python
    @debug(mode="simple", label="orders.create")
    def create_order(item, qty): ...
    ```

    ```
    [debug] orders.create(item='widget', qty=3) → {'item': 'widget', ...}  12.4 µs
    [debug] orders.create(item='broken', qty=0) 💥 ValueError: qty must be > 0
    ```

=== "json — success"

    ```python
    @debug(mode="json")
    def create_order(item: str, qty: int = 1) -> dict: ...
    ```

    ```json
    {
      "name": "create_order",
      "file": "app.py",
      "line": 12,
      "args": {
        "item": "'widget'",
        "qty": "3"
      },
      "return": "{'item': 'widget', 'qty': 3, 'total': 29.97}",
      "exception": null,
      "raised": false,
      "duration_ms": 0.012
    }
    ```

=== "json — exception"

    ```json
    {
      "name": "parse_config",
      "file": "app.py",
      "line": 7,
      "args": {
        "path": "'/etc/nonexistent.json'"
      },
      "return": null,
      "exception": "[Errno 2] No such file or directory: '/etc/nonexistent.json'",
      "raised": true,
      "duration_ms": 0.088
    }
    ```

---

## Custom label

```python
@debug(label="payments.authorize")
def authorize(token: str, amount: float) -> bool:
    ...
```

The label appears in the panel header and in JSON `"name"` — useful when you have many decorated functions and want clean log lines.

---

## Truncating long values

```python
@debug(max_length=80)    # default is 200
def embed(text: str) -> list[float]:
    return model.encode(text)
```

Long argument reprs and return values are truncated to `max_length` characters with a `…` suffix. Prevents the panel from becoming unreadable when you're passing large objects.

---

## Async support

```python
@debug(mode="json")
async def fetch_document(doc_id: str) -> dict:
    return await db.get(doc_id)

doc = await fetch_document("doc_abc123")
```

Works identically. Duration is wall time including all `await` suspensions.

---

## API reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `"pretty"` \| `"simple"` \| `"json"` | `"pretty"` | Output format |
| `label` | `str \| None` | `None` | Custom name. Defaults to `module.qualname` |
| `max_length` | `int` | `200` | Max chars for arg/return repr before truncation |

---

## Use cases

| Scenario | What `@debug` gives you |
|----------|------------------------|
| Understanding a third-party function | Real args & return, every time |
| Tracking down a flaky test | Exact inputs on the failing call |
| Verifying refactor behavior | Before/after return values side by side |
| Logging edge cases in production | JSON mode → structured log stream |
| Debugging async race conditions | Per-call duration + arg snapshot |
