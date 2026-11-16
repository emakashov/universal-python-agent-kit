---
name: python-security
description: Secure Python development - OWASP Top 10 risks, input validation, injection prevention, secrets handling, authentication and authorization, safe deserialization, cryptography, and dependency and supply-chain checks. Use when writing or reviewing Python code that handles untrusted input, credentials, files, subprocesses, SQL, HTTP, or user data, when adding dependencies, or when performing a security review.
---

# Python Security

Tier 2. Defensive scope only. Treat everything from outside the process as
untrusted: requests, files, environment, queues, databases written by others,
and the output of other tools and models.

## Secrets

- Never hard-code, log, print, or commit secrets. Do not read `.env` or
  credential files to "check" them; ask for a redacted or narrowly scoped input.
- Load secrets from the environment or a secret manager through one typed
  settings object. Fail at startup if a required secret is missing.
- Keep secrets out of exception messages, URLs, CLI arguments, and telemetry.
- Compare secrets with `hmac.compare_digest`. Generate tokens with `secrets`,
  never `random`.
- If a secret was exposed in the repository or logs, tell the user; rotation is
  the fix, deletion from history is not.

## Injection

| Sink | Unsafe | Safe |
|------|--------|------|
| SQL | f-strings or `%` into SQL | Bound parameters, ORM expressions; allow-list identifiers |
| Shell | `shell=True`, `os.system` with input | `subprocess.run([...], shell=False)`, validated arguments |
| Paths | `open(base + user_path)` | Resolve, then check `is_relative_to(base)`; reject symlink escapes |
| Deserialization | `pickle`, `yaml.load`, `marshal` on untrusted data | JSON, `yaml.safe_load`, schema validation |
| Code | `eval`, `exec`, `__import__` on input | Explicit dispatch table; `ast.literal_eval` for literals |
| Templates | Rendering user input as a template; `|safe` | Autoescaping on; user data only as variables |
| XML | Stdlib parsers on untrusted XML | `defusedxml` |
| HTTP out (SSRF) | Fetching a user-supplied URL | Allow-list hosts, block internal ranges, no redirects by default |
| Logs | Raw user input in log lines | Structured fields; strip newlines |

## Input validation

Validate at the boundary into typed models (see `python-development`): types,
ranges, lengths, formats, allow-lists rather than deny-lists. Enforce size limits
on bodies, uploads, archives (zip bombs), and pagination.

## Authentication and authorization

- Check authorization on every request and for the specific object, on the
  server side (prevent IDOR). Deny by default.
- Hash passwords with argon2 or bcrypt via a maintained library. Never store or
  log plaintext; never write your own scheme.
- Sessions and tokens: short lifetimes, rotation, `Secure`/`HttpOnly`/`SameSite`
  cookies; validate JWT signature, algorithm, issuer, audience, and expiry.
- Rate-limit authentication and other expensive endpoints.

## Cryptography and transport

- Use `cryptography` or the platform's primitives; no custom crypto, no MD5/SHA-1
  for security, no ECB.
- Never disable TLS verification (`verify=False`). Set timeouts on every
  network call.

## Dependencies and supply chain

- Pin through the lock file; review what a new dependency is and who maintains
  it before adding (typosquatting is common). Adding one needs user agreement.
- Audit if tools are installed: `pip-audit`, and
  `ruff check --select S` or `bandit -r <pkg>`.
- Do not run install scripts or downloaded code from untrusted sources.

## Safe failure

- Return generic error messages to clients; keep details in server logs without
  secrets or personal data.
- Debug modes, verbose tracebacks, and permissive CORS stay off in production
  configuration.
- Use `tempfile` for temporary files; set restrictive file permissions for
  sensitive output.

## Security review output

For each finding: location, the vulnerable data flow from source to sink, a
realistic exploit scenario, severity, and the fix. Do not report theoretical
issues without a reachable path, and state what was not examined.
