# 📊 @profile

> A full snapshot per call: **wall time, CPU time, memory delta & peak, thread count.**

---

## Basic usage

```python
from tsukikage import profile

@profile
def build_inverted_index(docs: list[str]) -> dict:
    return {word: i for i, doc in enumerate(docs) for word in doc.split()}

build_inverted_index(["hello world", "foo bar baz"] * 1000)
```

**Terminal output:**

<div class="terminal">
╭─ 📊  __main__.build_inverted_index ───────────────────────────────╮<br>
│&nbsp; &nbsp;<span class="dim">wall time</span> &nbsp; &nbsp;<span class="grn">18.441 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">cpu time</span> &nbsp; &nbsp; <span class="grn">17.892 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">memory</span> &nbsp; &nbsp; &nbsp; <span class="grn">+512.34 KB</span> &nbsp;<span class="dim">(peak 1.23 MB)</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">threads</span> &nbsp; &nbsp; &nbsp;<span class="grn">1 → 1</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
╰───────────────────────────────────────────────────────────────────╯
</div>

---

## Multiple calls — accumulated stats

```python
for dataset in all_datasets:
    build_inverted_index(dataset)

stats = build_inverted_index.stats()
```

<div class="terminal">
╭─ 📊  __main__.build_inverted_index ───────────────────────────────╮<br>
│&nbsp; &nbsp;<span class="dim">wall time</span> &nbsp; &nbsp;<span class="grn">20.112 ms</span> &nbsp;<span class="dim">avg 19.003 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">cpu time</span> &nbsp; &nbsp; <span class="grn">19.441 ms</span> &nbsp;<span class="dim">avg 18.812 ms</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">memory</span> &nbsp; &nbsp; &nbsp; <span class="grn">+498.00 KB</span> &nbsp;<span class="dim">avg +503.12 KB</span> &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">threads</span> &nbsp; &nbsp; &nbsp;<span class="grn">1 → 1</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; │<br>
│&nbsp; &nbsp;<span class="dim">calls</span> &nbsp; &nbsp; &nbsp; &nbsp;<span class="grn">8</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;│<br>
╰───────────────────────────────────────────────────────────────────╯
</div>

---

## Output modes

=== "pretty (default)"

    ```python
    @profile
    def process(data): ...
    ```

    Rich panel with borders, aligned columns, delta memory with sign.

=== "simple"

    ```python
    @profile(mode="simple", label="indexer.build")
    def process(data): ...
    ```

    ```
    [profile] indexer.build → wall=18.4ms cpu=17.9ms mem=+512KB threads=1→1
    ```

=== "json"

    ```python
    @profile(mode="json", label="indexer.build")
    def process(data): ...
    ```

    ```json
    {
      "name": "indexer.build",
      "wall_ms": 18.441,
      "cpu_ms": 17.892,
      "memory_before_bytes": 4194304,
      "memory_after_bytes": 4718592,
      "memory_delta_bytes": 524288,
      "memory_peak_bytes": 1290240,
      "threads_before": 1,
      "threads_after": 1,
      "calls": 1,
      "avg_wall_ms": 18.441,
      "avg_cpu_ms": 17.892,
      "avg_memory_delta_bytes": 524288
    }
    ```

    Structured output ready for Elasticsearch, Datadog, or any log sink.

---

## Programmatic access

```python
@profile(label="search.rank")
def rank_results(query: str) -> list:
    ...

for q in test_queries:
    rank_results(q)

stats = rank_results.stats()
last  = stats.last          # most recent ProfileSnapshot

print(last.duration_ns)           # wall time in nanoseconds
print(last.cpu_ns)                # CPU time in nanoseconds
print(last.memory_delta_bytes)    # net memory (property: after - before)
print(last.memory_peak_bytes)     # peak allocation during call
print(last.threads_before)        # thread count at call start
print(last.threads_after)         # thread count at call end

print(stats.calls)                # total call count
print(stats.avg_duration_ns)      # average wall time
print(stats.avg_cpu_ns)           # average CPU time
print(stats.avg_memory_delta_bytes)

rank_results.reset()              # clear accumulated data
```

---

## Async support

```python
@profile(label="db.query")
async def search(q: str) -> list[dict]:
    return await db.execute("SELECT * FROM docs WHERE ts @@ $1", q)

results = await search("python observability")
```

Wall time includes all `await` suspension. CPU time reflects only actual Python execution.

---

## Memory tracking note

!!! info "Python-level memory via tracemalloc"
    `@profile` uses Python's built-in `tracemalloc` to measure memory. This tracks **Python object allocations** — not C extensions or subprocess memory. For native extensions (numpy, pandas), the delta may be zero or partial.

    For system-level memory, combine with `resource.getrusage()` or a tool like `memray`.

---

## API reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `"pretty"` \| `"simple"` \| `"json"` | `"pretty"` | Output format |
| `label` | `str \| None` | `None` | Custom metric name. Defaults to `module.qualname` |

---

## Use cases

| Scenario | What to watch |
|----------|--------------|
| Large data transformation | `memory_delta` — are you building 10× the input? |
| Concurrent request handler | `threads_before/after` — are threads leaking? |
| ML feature pipeline | `cpu_ms / wall_ms` — CPU-bound or I/O-bound? |
| ORM query builder | `wall_ms` per call — N+1 hiding in here? |
| Cache effectiveness check | Compare `memory_delta` hit vs miss runs |
