---
name: postgresql
description: PostgreSQL schema design, SQL, indexing, query plans, transactions and locking, and safe zero-downtime migrations. Use only when the project uses PostgreSQL and the task involves writing or reviewing SQL, designing tables or indexes, diagnosing slow queries or locks, or writing database migrations.
---

# PostgreSQL

Tier 3. Activate only if the project uses PostgreSQL. Language-independent.

## Safety first

- Know which database you are connected to before running anything. Never run
  DDL, `DELETE`, `UPDATE`, or `TRUNCATE` against a shared or production database
  without explicit user confirmation for that statement.
- Prefer read-only inspection (`EXPLAIN`, catalog queries). Note that
  `EXPLAIN ANALYZE` executes the statement: wrap writes in a transaction you
  roll back.
- Never put credentials in commands, code, or logs.

## Schema design

- Types: `bigint` or `uuid` keys; `timestamptz` for instants (never `timestamp`
  for them); `numeric` for money; `text` over `varchar(n)` unless the limit is a
  real rule; `jsonb` only for genuinely schemaless data; `boolean`, not flags in
  integers.
- Constraints carry the invariants: `NOT NULL`, `UNIQUE`, `CHECK`, foreign keys
  with deliberate `ON DELETE`. The application is not the only writer over time.
- Normalize first; denormalize only for a measured need and with a plan to keep
  the copies consistent.
- Name constraints and indexes explicitly and consistently.

## Indexes

- Index for actual queries: columns in `WHERE`, `JOIN`, `ORDER BY`. Index foreign
  key columns; PostgreSQL does not do it automatically.
- Composite index order: equality columns first, then range or sort column.
- Use partial indexes for hot subsets (`WHERE deleted_at IS NULL`), expression
  indexes for computed predicates (`lower(email)`), `INCLUDE` for index-only
  scans, GIN for `jsonb`, arrays, and full-text, BRIN for huge append-only tables.
- Every index costs writes and space. Remove unused ones (`pg_stat_user_indexes`)
  rather than adding more.

## Query writing and tuning

- Measure with `EXPLAIN (ANALYZE, BUFFERS)` on realistic data. Compare estimated
  and actual rows; a large gap points at stale statistics (`ANALYZE`) or a
  predicate the planner cannot estimate.
- Common causes of slow queries: a function or cast on the indexed column,
  leading-wildcard `LIKE`, `OR` across columns, `OFFSET` on deep pages, missing
  join index, `SELECT *` on wide rows, `NOT IN` with a nullable subquery.
- Use keyset pagination (`WHERE (created_at, id) < (...) ORDER BY ... LIMIT n`).
- Use set-based statements: `INSERT ... SELECT`, `UPDATE ... FROM`,
  `INSERT ... ON CONFLICT DO UPDATE`, `COPY` for bulk load.
- Always parameterize. Never build SQL by concatenating values.

## Transactions and locking

- Keep transactions short. No network calls or user waits inside one.
- Default isolation is `READ COMMITTED`. For read-modify-write use
  `SELECT ... FOR UPDATE`, an atomic `UPDATE ... WHERE ... RETURNING`, or
  `SERIALIZABLE` with retry on serialization failure.
- Queue-style workers: `FOR UPDATE SKIP LOCKED`.
- Take locks in a consistent order to avoid deadlocks; handle deadlock and
  serialization errors by retrying the whole transaction.
- Set `statement_timeout`, `lock_timeout`, and `idle_in_transaction_session_timeout`.

## Migrations without downtime

Set `lock_timeout` in migrations so a blocked DDL fails fast instead of queueing
behind long transactions and blocking everyone.

| Change | Safe way |
|--------|----------|
| Add column | Nullable or with a constant default; backfill in batches; then `SET NOT NULL` |
| Add `NOT NULL` | `CHECK (col IS NOT NULL) NOT VALID` → `VALIDATE CONSTRAINT` → `SET NOT NULL` |
| Add index | `CREATE INDEX CONCURRENTLY` (outside a transaction); check it is not `INVALID` |
| Add foreign key / check | Add `NOT VALID`, then `VALIDATE CONSTRAINT` separately |
| Rename or drop column, change type | Expand → migrate code → contract, across deployments |
| Large backfill or delete | Batches with commits between them, never one statement |

Every migration is tested on an empty database and on production-like data
volume, and has a rollback path or a stated reason it cannot be reversed.

## Operations

- Use a connection pooler or bounded application pool; do not open a connection
  per request.
- Find slow queries with `pg_stat_statements`; find blockers with
  `pg_stat_activity` and `pg_locks`.
- Roles get least privilege; the application role does not own the schema where
  the project separates them.
