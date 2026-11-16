---
name: python-data-engineering
description: Python data engineering - pandas and Polars transformations, ETL and ELT pipeline design, schema and data validation, idempotent loads, file formats, and testing data code. Use when writing or changing data pipelines, DataFrame transformations, ingestion or export jobs, or data quality checks in a Python project that uses pandas, Polars, PyArrow, DuckDB, or similar libraries.
---

# Python Data Engineering

Tier 2. Use the DataFrame library the project already uses. Do not introduce
Polars into a pandas codebase, or the reverse, without being asked.

## Pipeline design

- Separate extract, transform, and load. Transformations are pure functions from
  DataFrame to DataFrame with no I/O, so they can be tested directly.
- **Idempotent**: re-running a step for the same input and period yields the same
  state. Use partition overwrite, upsert/merge on a key, or delete-then-insert in
  one transaction. Never blind append on retry.
- **Atomic output**: write to a temporary location, then rename or swap; a failed
  run must not leave partial data visible.
- Make runs parameterized by an explicit time window or batch id, not by "now".
- Keep raw input immutable; derive everything else from it reproducibly.
- Process incrementally and in bounded memory: chunked reads, lazy scans, streaming.

## Validation at boundaries

Validate data when it enters and before it leaves, with the project's tool
(Pandera, Pydantic, Great Expectations, or explicit checks):

- schema: column names, dtypes, nullability;
- keys: uniqueness, referential integrity;
- values: ranges, allowed categories, formats;
- volume: row count within expected bounds, no silent empty input.

Decide per rule whether a violation fails the run or quarantines the rows. Never
drop bad rows silently; count and report them.

## Correctness traps

- **Joins**: check key uniqueness before joining; assert the row count after. In
  pandas use `merge(..., validate="one_to_many")` and `indicator=True` to audit.
- **Nulls**: `NaN` vs `None` vs `pd.NA`; nulls in join keys and group keys;
  aggregates skipping nulls. State the intended null policy.
- **Types**: integers turning to float because of nulls (use nullable dtypes);
  IDs parsed as numbers losing leading zeros; mixed-type object columns.
- **Time**: store UTC, convert at the edges; be explicit about naive vs aware;
  watch DST and inclusive/exclusive window ends.
- **Money and precision**: use `Decimal` or integer minor units, not float.
- **Duplicates**: define the business key and the dedup rule explicitly.
- **Ordering**: do not rely on row order unless you sorted.

## pandas

- Vectorized operations; avoid `iterrows`, `apply(axis=1)`, and Python loops over rows.
- No chained assignment; use `.loc[rows, cols] = ...`. Avoid `inplace=True`.
- Set dtypes on read (`dtype=`, `parse_dates=`); use `category` for
  low-cardinality strings; read only needed columns (`usecols`).
- Prefer method chains with `assign`/`pipe` over many intermediate variables.

## Polars

- Use the lazy API (`scan_*`, `.lazy()`, `.collect()`) so the optimizer can push
  down filters and projections.
- Express logic with expressions (`pl.col`, `when/then/otherwise`, `over`); avoid
  `map_elements` and row-wise Python.
- Declare schemas explicitly on read for production inputs.

## Storage and formats

- Prefer Parquet (typed, columnar, compressed) for intermediate and analytical
  data; CSV only at external boundaries, with explicit encoding, delimiter,
  quoting, and dtypes.
- Partition by the column used for incremental loads and pruning.
- Load into databases with bulk mechanisms (`COPY`, bulk insert), not row-by-row.

## Testing data code

- Unit-test transformations with small, hand-built frames that include the
  awkward cases: empty frame, nulls, duplicates, boundary dates.
- Compare with the library's testing helpers (`pandas.testing.assert_frame_equal`,
  `polars.testing.assert_frame_equal`).
- Expected values come from the business rule, not from the current output.
- Add a re-run test that proves idempotency for load steps.

## Operations

Log row counts in and out of each step, rejected rows, and durations. Never log
record contents that may contain personal data. Make failures loud: a pipeline
that silently produces an empty or partial result is worse than one that stops.
