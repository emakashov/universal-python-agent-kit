---
name: observability
description: Observability for services - structured logging, metrics, distributed tracing with OpenTelemetry, correlation IDs, health checks, alerting signals, and keeping sensitive data out of telemetry. Use only when the project is a running service or job and the task involves adding or changing logs, metrics, traces, health endpoints, or diagnosing production behavior from telemetry.
---

# Observability

Tier 3. Activate only if the project is an operated service or job, or already
has logging, metrics, or tracing libraries. Use the libraries and backends the
project already has; do not add a telemetry stack unasked.

## Goal

Someone who did not write the code can answer from telemetry alone: is it
working, what is failing, for whom, since when, and where in the request path.
Add signals that answer a question someone will actually ask. Unused telemetry is
cost and noise: subtract before you add.

## Logging

- Use the project's logger. Python: `logging.getLogger(__name__)` or the
  configured structured logger (`structlog`); never `print` in service code.
  Libraries do not configure logging; applications do, once, at startup.
- Log messages are always in English, even when the code's comments are Russian.
- Structured logs (JSON in production) with a stable event name and fields, not
  values interpolated into prose: `log.info("order_paid", extra={"order_id": id})`.
- With stdlib logging pass arguments lazily (`log.info("x=%s", x)`), not f-strings.
- Levels: `DEBUG` developer detail; `INFO` business-relevant events and state
  changes; `WARNING` unexpected but handled; `ERROR` an operation failed and
  someone may need to act; `CRITICAL` the service cannot continue.
- Log an exception once, where it is handled, with the traceback
  (`log.exception` or `exc_info=True`). Do not log and re-raise at every layer.
- Include correlation fields on every line: request or trace id, and the
  relevant entity ids. Propagate them with `contextvars`, not function parameters.
- Do not log in tight loops; aggregate or sample.

## Sensitive data

Never put into logs, metrics labels, span attributes, or error reports:
passwords, tokens, API keys, session ids, full authorization headers, payment
data, or personal data beyond what the project's policy allows. Log identifiers,
not contents. Redact at the logger level as a backstop, not as the only defense.

## Metrics

- Instrument the four golden signals for each service boundary: traffic (rate),
  errors, latency (histogram, not average), saturation (queue depth, pool usage).
- For jobs and pipelines: last success time, duration, items processed, items failed.
- Types: counter for things that only increase; gauge for current values;
  histogram for distributions with buckets suited to the expected range.
- Naming: follow the backend's convention (Prometheus: `snake_case`, base units,
  `_total` for counters, `_seconds`, `_bytes`).
- Labels must have bounded cardinality. Never use user ids, emails, raw URLs,
  or error messages as label values; use route templates and error classes.

## Tracing

- Use OpenTelemetry with the project's exporter. Prefer auto-instrumentation for
  frameworks, HTTP clients, and database drivers; add manual spans only around
  meaningful units of work.
- Propagate context across every boundary: HTTP headers (W3C `traceparent`),
  message metadata, background tasks, thread and process pools.
- Span names are low-cardinality (`GET /orders/{id}`); details go in attributes
  following semantic conventions. Record exceptions and set error status.
- Put the trace id into log records so logs and traces can be joined.
- Sampling is a deployment decision; do not hard-code it.

## Health and readiness

- Liveness: the process is not stuck; cheap; no dependency calls.
- Readiness: the service can take traffic; checks critical dependencies with
  short timeouts.
- Handle `SIGTERM`: stop accepting work, finish in-flight requests, flush telemetry.

## Alerting signals

Alert on user-visible symptoms (error rate, latency, missed job deadline) tied to
an objective, not on every cause. Each alert must be actionable and link to what
to check. Changing alert rules or dashboards in shared systems needs the user's
permission.

## Testing

- Assert important log events and metrics as behavior where they are part of the
  contract (audit events, billing counters): `caplog`, an in-memory metric reader
  or span exporter.
- Do not assert incidental log wording.
- Verify that telemetry failure does not break the request path: exporters are
  non-blocking and have timeouts.

## Diagnosing from telemetry

Start from the symptom and time window; narrow by service, route, and error
class; follow one trace end to end; correlate with deployments and configuration
changes. State what the data shows and what it does not; absence of logs is not
evidence of absence of events.
