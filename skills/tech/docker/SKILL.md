---
name: docker
description: Docker and Docker Compose - writing Dockerfiles, multi-stage builds, small and secure images, build caching, Compose services, health checks, and container debugging. Use only when the project uses Docker and the task involves a Dockerfile, a Compose file, .dockerignore, image build or size problems, or running the application in containers.
---

# Docker

Tier 3. Activate only if the project has Docker or Compose files, or the user asks
to containerize. Language-independent; Python specifics are marked.

## Safety

- Do not run destructive commands without explicit confirmation:
  `docker system prune`, `docker volume rm`, `docker compose down -v`,
  `docker rm -f` on containers you did not start. Volumes hold user data.
- Do not push images or log in to registries without explicit permission.
- Never bake secrets into images: not in `ENV`, `ARG`, `COPY`, or layer history.
  Use BuildKit secrets (`RUN --mount=type=secret`) at build time and environment
  or secret mounts at run time. Do not read or print `.env` files.

## Dockerfile

- Pin the base image to a specific tag (and digest where reproducibility
  matters); never `latest`. Prefer slim official images.
- Multi-stage: build tools and compilers in the builder stage; copy only
  artifacts into the runtime stage.
- Order layers from least to most frequently changing: system packages →
  dependency manifests → dependency install → application source. Copy the lock
  file and install dependencies before copying the source.
- One concern per `RUN`; clean package caches in the same layer
  (`apt-get install --no-install-recommends ... && rm -rf /var/lib/apt/lists/*`).
- Run as a non-root user (`USER app`); do not require write access to the image
  filesystem; write only to declared volumes or `/tmp`.
- Exec-form `ENTRYPOINT`/`CMD` (`["python", "-m", "app"]`) so signals reach the
  process; one main process per container.
- `.dockerignore` excludes `.git`, virtualenvs, caches, tests data, local env files.
- Add `HEALTHCHECK` or an orchestrator-level probe for services.

### Python image sketch (uv)

```dockerfile
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev

FROM python:3.13-slim
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
CMD ["python", "-m", "my_package"]
```

Adapt versions and paths to the project; use the versions it already pins.
For pip-based projects install from a hashed requirements file with
`pip install --no-cache-dir -r requirements.txt`.

## Compose

- Compose is for local development and tests unless the project deploys with it.
- Use the `compose.yaml` name and the `docker compose` (v2) command unless the
  project uses the older ones. No top-level `version:` key in new files.
- `depends_on` with `condition: service_healthy` plus a real `healthcheck`; the
  application must still tolerate a dependency that is not ready.
- Named volumes for state; bind mounts only for development source.
- Configuration through `environment`/`env_file`; secrets never committed.
  Publish only the ports that are needed, bound to `127.0.0.1` for local-only services.
- Pin image tags of dependencies (database, cache) to the production major version.
- Use `profiles` for optional services rather than separate near-duplicate files.

## Debugging

- Build: `docker build --progress=plain`; find cache misses by layer order.
- Run: `docker compose logs -f <svc>`, `docker compose ps`, `docker inspect`,
  `docker compose exec <svc> sh`.
- Size: `docker image history <image>`; check what the build context sends.
- "Works locally, not in container": check working directory, user and file
  permissions, missing environment variables, `localhost` vs service name,
  architecture (`linux/amd64` vs `arm64`), and bind mounts hiding image content.

## Quality gate

Image builds from a clean cache; container starts and passes its health check as
non-root; no secrets in `docker history`; image scanned if a scanner (`trivy`,
`docker scout`) is installed; Dockerfile linted if `hadolint` is installed.
