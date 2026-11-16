---
name: python-performance
description: Measurement-driven Python performance work - profiling CPU, memory, and I/O, benchmarking, algorithmic and data-structure fixes, caching, concurrency choices, and avoiding premature optimization. Use when Python code is too slow, uses too much memory, has to meet a latency or throughput target, or when an optimization is proposed.
---

# Python Performance

Tier 2. Never optimize without a measurement, and never keep an optimization
without a measurement that shows it helped.

## Procedure

1. **Define the target**: which operation, on what input size, how fast or how
   small, measured how. Without a target there is no "done".
2. **Make it reproducible**: a benchmark script or test with realistic data.
3. **Check correctness coverage** before changing anything; optimizations break edge cases.
4. **Profile** to find where the time or memory actually goes. Do not guess.
5. **Fix the largest contributor** with the simplest change. Re-measure.
6. **Stop** when the target is met. Report before/after numbers and conditions.

Attack the premise first: is the work needed at all? Can it be done once, done
less often, done on less data, or pushed to the database?

## Measuring

| Need | Tool |
|------|------|
| Micro-benchmark | `python -m timeit`, `pytest-benchmark` if installed |
| CPU profile, deterministic | `python -m cProfile -o out.prof script.py`, then `pstats` or `snakeviz` |
| CPU profile, sampling, running process | `py-spy record -o flame.svg -- python script.py`, `py-spy top --pid` |
| Line level | `line_profiler` (`kernprof -l`) |
| Memory | `tracemalloc`, `memray`, `scalene` |
| Import time | `python -X importtime` |
| SQL | query log, `EXPLAIN (ANALYZE, BUFFERS)`; see `postgresql`, `sqlalchemy` |

Use tools only if installed. Measure several runs, report the spread, use the
same machine and data for before and after, and use production-like data sizes.

## Where the time usually is

1. **I/O and queries**: N+1 queries, missing index, chatty network calls, no
   batching, no connection reuse. Fix these before touching Python code.
2. **Algorithm and data structure**: O(n²) loops, `in` on a list instead of a set,
   repeated sorting, repeated work inside a loop, string concatenation in a loop.
3. **Unneeded work**: loading whole files or tables, building lists that are only
   iterated (use generators), re-parsing, re-compiling regexes, eager logging
   string formatting.
4. **Interpreter overhead** in hot loops: move to built-ins, comprehensions,
   `itertools`, `collections`, vectorized NumPy/Polars operations.

## Techniques, in order of preference

- Do less: filter early, select only needed columns, paginate, stream.
- Better structure: `set`/`dict` lookups, `deque`, `heapq`, `bisect`.
- Cache pure, expensive, repeated calls: `functools.cache`/`lru_cache` with a
  bound; define invalidation before adding a cache. An unbounded cache is a leak.
- Batch: bulk inserts, `executemany`, pipelined requests.
- Concurrency by workload: I/O-bound → `asyncio` or threads; CPU-bound →
  `ProcessPoolExecutor`/multiprocessing or native code. Threads do not speed up
  CPU-bound pure Python on GIL builds.
- Memory: `__slots__`, generators, chunked reads, `array`/NumPy for numeric data.
- Native acceleration (Cython, Rust, Numba) only when profiling shows a hot pure
  Python loop that the above cannot fix, and the project accepts the build cost.

## Do not

- Do not trade readability for an unmeasured micro-optimization.
- Do not add a cache, pool, or async layer without evidence it is needed.
- Do not benchmark with toy data, debug builds, or a cold cache only.
- Do not change behavior (ordering, precision, error handling) silently for speed.

## Report

The target, the profile finding, the change, before/after numbers with input size
and environment, and the tests that confirm unchanged behavior.
