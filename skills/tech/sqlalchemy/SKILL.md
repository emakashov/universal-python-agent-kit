---
name: sqlalchemy
description: SQLAlchemy 2.x usage - typed declarative models, sessions and unit of work, transactions, relationship loading, async sessions, Alembic migrations, and testing against a real database. Use only when the project uses SQLAlchemy and the task touches its models, queries, sessions, transactions, engine configuration, or Alembic migrations.
---

# SQLAlchemy

Tier 3. Activate only if `sqlalchemy` is a project dependency. Use the style of
the installed major version; do not mix 1.x `Query` style into 2.x code.

## Models (2.x)

```python
class Base(DeclarativeBase):
    pass

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    status: Mapped[OrderStatus]
    note: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped["Customer"] = relationship(back_populates="orders")
```

- Nullability follows the annotation (`Mapped[str | None]`). Put constraints and
  indexes in the model so migrations stay in sync.
- Set a naming convention on `MetaData` so constraint names are deterministic.
- Timezone-aware timestamps; `Numeric` for money.

## Sessions and transactions

- A `Session` is a unit of work for one request or job. Never share one across
  threads, tasks, or requests; never keep one in a module global.
- One place owns the transaction boundary (request dependency, job wrapper,
  `with session.begin():`). Repositories and services do not call `commit()`;
  they may `flush()` to obtain generated keys.
- Always release: `with Session(engine) as session:` or a `yield` dependency.
- On error, roll back; do not continue using a session after a failed flush
  without rollback.
- Concurrent updates: use `with_for_update()`, an atomic `UPDATE ... WHERE`, or a
  `version_id_col` for optimistic locking. Read-modify-write without one of
  these is a race.
- Session-factory options are a project decision (`expire_on_commit`); do not
  change them to fix one call site.

## Queries

- Use `select()` with `session.execute()` / `session.scalars()`;
  `session.get(Model, pk)` for primary-key lookup.
- Always bound parameters; `text("... :name")` with parameters if raw SQL is needed.
- Avoid N+1: choose loading per query with `selectinload` (collections) or
  `joinedload` (many-to-one). Consider `lazy="raise"` on relationships so
  accidental lazy loads fail in tests.
- Select only what is needed for large reads; page with keyset pagination; stream
  with `yield_per`.
- Bulk work: `session.execute(insert(Model), rows)`, `update()`/`delete()`
  statements; not per-row ORM loops.

## Async

- `create_async_engine`, `async_sessionmaker(expire_on_commit=False)`.
- No implicit lazy loading in async: load relationships eagerly or use
  `AsyncAttrs`/`awaitable_attrs`.
- One `AsyncSession` per task; never share it between concurrent tasks
  (`asyncio.gather` on one session is a bug).

## Engine

Create one engine per process and database. Configure pool size, `pool_pre_ping`,
and timeouts from settings. Dispose on shutdown. Never log connection URLs with
credentials.

## Alembic

- Generate with `alembic revision --autogenerate -m "..."`, then read and correct
  the file: autogenerate misses renames, some type changes, and data moves.
- Every revision has a working `downgrade` or a stated reason it cannot.
- Never edit a revision that was applied on a shared environment; add a new one.
- Keep one head (`alembic heads`); test `upgrade head` on an empty database and
  on a copy of real schema state.
- Follow the zero-downtime and locking rules in `postgresql`.
- Applying migrations to shared or production databases needs explicit user
  confirmation.

## Testing

- Test against the same database engine as production (container or local
  instance). SQLite does not reproduce PostgreSQL types, constraints, or locking.
- Isolate tests with a connection-level transaction rolled back after each test
  (`join_transaction_mode="create_savepoint"`), or a fresh schema.
- Test repositories by behavior: what is stored and returned, including
  constraint violations; do not assert on generated SQL strings.
- Do not mock `Session`.

## Quality gate

Tests pass on the real engine; `alembic upgrade head` works from empty; `alembic
check` (if available) reports no pending model changes; no new N+1 on changed paths.
