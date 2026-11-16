---
name: django
description: Django application development - models and ORM queries, migrations, views and forms, Django REST Framework, settings, security, and testing. Use only when the project uses Django and the task touches its models, migrations, querysets, views, serializers, admin, settings, or tests.
---

# Django

Tier 3. Activate only if `django` is a project dependency. Follow the project's
Django version and its existing app structure.

## Models and ORM

- Business rules belong in models, managers/querysets, or service functions, not
  in views, serializers, templates, or signals.
- Enforce integrity in the database: `UniqueConstraint`, `CheckConstraint`,
  `on_delete` chosen deliberately, `null`/`blank` chosen deliberately
  (`null=True` on string fields is rarely right).
- Prevent N+1: `select_related` for forward FK/one-to-one, `prefetch_related`
  for reverse and many-to-many. Verify with `assertNumQueries` or the query log.
- Use `F()` and `update()` for atomic counters, `select_for_update()` inside a
  transaction for read-modify-write, `bulk_create`/`bulk_update` for batches,
  `exists()`/`count()` instead of loading rows, `iterator()` for large scans.
- `transaction.atomic()` around multi-step writes; side effects that must happen
  only after commit go in `transaction.on_commit`.
- Avoid signals for core logic; an explicit call is easier to follow and test.

## Migrations

- Create with `makemigrations`; review the generated file; never edit a migration
  that has been applied on a shared environment — add a new one.
- `python manage.py makemigrations --check --dry-run` must report no changes.
- Schema migrations and data migrations are separate files. Data migrations use
  `apps.get_model`, are batched, and have a reverse operation or state
  `migrations.RunPython.noop` deliberately.
- Zero-downtime changes go in steps: add nullable column → backfill → enforce
  `NOT NULL`; stop using a column → deploy → drop it. Do not rename a column or
  table in one step on a live system.
- On PostgreSQL, large-table indexes use `AddIndexConcurrently` in a
  non-atomic migration.
- Applying migrations to any shared or production database requires explicit
  user confirmation. Never run `flush`, `reset_db`, or `migrate <app> zero` there.

## Views and APIs

- Thin views. Validate input with forms or serializers; never trust `request`
  data directly.
- Every view states its permission: login and object-level checks, by default
  deny. Filter querysets by the current user/tenant in `get_queryset`.
- DRF: explicit `fields` in serializers (never `"__all__"` for writable ones),
  separate read and write serializers when they differ, pagination and throttling
  configured, `permission_classes` on every viewset.

## Security

- Keep the defaults on: CSRF middleware, template autoescaping, clickjacking
  protection, password validators. `mark_safe` and `|safe` only on trusted content.
- No raw SQL built with string formatting; use the ORM or parameters with
  `raw()`/`cursor.execute(sql, params)`.
- `SECRET_KEY`, database credentials, and `DEBUG` come from the environment;
  `DEBUG=False` and explicit `ALLOWED_HOSTS` in production.
- `python manage.py check --deploy` passes for production settings.
- Validate uploads (type, size); serve user media from a separate location.

## Settings

Environment-specific values via environment variables; one settings module or a
small base/override split as the project already does. Do not add settings that
nothing reads.

## Testing

- Use the project's runner (`pytest-django` or `manage.py test`).
- Test through the public surface: the test `Client`/`APIClient` for views, model
  and service methods for rules. Assert responses and database state.
- Build data with factories (`factory_boy`, `model_bakery`) or small helpers, not
  large fixtures files.
- Use the real database engine of production for tests of queries and constraints.
- Cover permissions explicitly: anonymous, wrong user, right user.

## Quality gate

Tests pass; `makemigrations --check` clean; `manage.py check` clean; query count
for changed list views verified; migrations reviewed for locking and reversibility.
