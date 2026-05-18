#!/bin/sh
# Backend container entrypoint.
#
# Runs Alembic migrations against the dev DB, then execs uvicorn.
# `exec` so SIGTERM from docker reaches uvicorn directly and the
# container shuts down cleanly.
#
# This entrypoint is invoked by the Dockerfile CMD. `docker compose
# run --rm backend <cmd>` (used by `make test` and `make migrate`)
# overrides CMD entirely, so it does NOT run this script — tests and
# manual alembic invocations stay decoupled from the startup path.
set -e

echo "[entrypoint] applying migrations..."
alembic upgrade head

echo "[entrypoint] starting uvicorn..."
exec uvicorn app.main:app \
  --host 0.0.0.0 --port 8000 \
  --reload --reload-dir /app/src
