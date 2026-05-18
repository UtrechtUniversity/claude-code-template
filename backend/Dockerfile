# Dev-only image for the template backend.
# Hot-reload works by mounting the source tree as a volume in docker-compose.yml;
# this Dockerfile just bakes the interpreter and dependency set.

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml ./
COPY src ./src
RUN uv pip install --system --no-cache -e ".[dev]" \
    || uv pip install --system --no-cache -e "."

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Entrypoint runs `alembic upgrade head` then execs uvicorn.
# Overridden by `docker compose run --rm backend <cmd>` — see
# entrypoint.sh for the rationale.
CMD ["/app/entrypoint.sh"]
