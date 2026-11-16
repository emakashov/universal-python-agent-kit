---
name: fastapi
description: FastAPI application development - REST API design, routers, Pydantic v2 request and response models, dependency injection, async endpoints, error handling, authentication, background work, and testing with the test client. Use only when the project uses FastAPI and the task touches its endpoints, dependencies, schemas, middleware, lifespan, or API tests.
---

# FastAPI

Tier 3. Activate only if `fastapi` is a project dependency. Combine with
`python-development`, `python-testing`, and `sqlalchemy` when it is the ORM.

## Structure

- Thin route handlers: parse input, call a service function, return a response.
  Business rules live in plain Python that does not import FastAPI.
- Group endpoints with `APIRouter` per resource; include routers in one app
  factory. Follow the layout the project already has.
- Startup and shutdown resources (engine, HTTP client, pools) are created in the
  `lifespan` context manager, not at import time and not in `@app.on_event`.

## Schemas

- Separate models for input and output (`UserCreate`, `UserUpdate`, `UserRead`).
  Never return ORM objects or internal models directly, and never expose fields
  such as password hashes.
- Declare `response_model` (or the return annotation) and explicit `status_code`
  on every endpoint; declare error responses in `responses=`.
- Pydantic v2: `model_config = ConfigDict(from_attributes=True)` for ORM reading,
  `Field(...)` constraints, `Annotated` types for reuse. Reject unknown fields on
  input (`extra="forbid"`) where the API should be strict.
- Validate at this boundary once; pass typed objects to services.

## Dependencies

- Use `Annotated[T, Depends(...)]` aliases for shared dependencies
  (`SessionDep`, `CurrentUser`).
- Dependencies with `yield` own resource cleanup: one database session per
  request, closed in the `finally` part.
- Put authentication and authorization in dependencies, applied at router level
  so that a new endpoint is protected by default. Check access to the specific
  object, not only that a user is logged in.
- Read settings through one cached settings dependency (`pydantic-settings`).

## Async

- `async def` endpoints must not call blocking code (sync DB drivers,
  `requests`, `time.sleep`, heavy CPU). Use async libraries, or declare the
  endpoint with plain `def` so it runs in the thread pool.
- Do not mix a sync SQLAlchemy session into `async def` handlers.
- Set timeouts on outgoing calls; reuse one `httpx.AsyncClient` from lifespan.
- `BackgroundTasks` only for short, loss-tolerant work. Durable jobs go to a queue.

## Errors

- Raise `HTTPException` in the HTTP layer only. Services raise domain exceptions;
  map them to responses with `@app.exception_handler`.
- One consistent error body shape across the API. Do not leak tracebacks or SQL.
- Correct status codes: 400/422 invalid input, 401 unauthenticated, 403
  forbidden, 404 missing, 409 conflict, 201 with `Location` for created.

## API design

- Nouns for resources, plural collections, HTTP verbs for actions; idempotent
  `PUT`/`DELETE`.
- Paginate every list endpoint with a bounded page size; make filtering and
  sorting explicit and allow-listed.
- Changing a response shape or status code is a breaking change: version or
  coordinate it, and check the generated OpenAPI diff.
- Restrictive CORS; no wildcard origin together with credentials.

## Testing

- Test through the HTTP interface: `TestClient`, or `httpx.AsyncClient` with
  `ASGITransport` for async tests. Assert status, body, and headers, which is
  what the API's user observes.
- Replace external boundaries with `app.dependency_overrides`, and clear the
  overrides after each test. Do not patch internals of handlers.
- Run database-backed tests against a real database with per-test transaction
  rollback or a fresh schema.
- Cover for each endpoint: success, validation error, unauthenticated, forbidden,
  not found.

## Quality gate

Tests pass; the OpenAPI schema generates (`app.openapi()`) and changes to it are
intended; no blocking calls in async paths; new endpoints carry auth dependencies.
